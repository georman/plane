# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: the public page a client opens from the approval email.
# GET shows the work; every choice is a POST so that link scanners in mail
# clients can never approve anything by opening it. The signed token in the
# URL is the only credential, and only the newest emailed link works.
#
# Single item: Approve / Request changes / Comment.
# Batch (sub-items with files, e.g. 4 IG posts): Approve or Request changes
# per post, Approve all, Comment. When every post has an answer the parent
# moves on (all approved) or goes to Corrections (any changes).

import json
from html import escape

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from plane.bgtasks.gam_approval_task import add_comment, proof_files
from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import ApprovalItemDecision, ApprovalRequest
from plane.license.utils.gam_brand import get_brand
from plane.settings.storage import S3Storage
from plane.utils.gam_approval import batch_posts, corrections_state, next_state_after, read_token
from plane.utils.gam_client_texts import client_language, texts
from plane.utils.gam_worktime import TZ

PAGE = """<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} – {brand_name}</title>
<style>
  body {{ margin:0; background:#f5f7f6; color:#17201c; font:16px/1.55 Arial, Helvetica, sans-serif; }}
  main {{ max-width:720px; margin:0 auto; padding:24px 16px 48px; }}
  .card {{ background:#fff; border:1px solid #d7dfdb; border-radius:10px; padding:20px; margin-top:16px; }}
  h1 {{ font-size:1.4rem; margin:12px 0 4px; }} h2 {{ font-size:1.1rem; margin:0 0 8px; }}
  .muted {{ color:#5a6862; }}
  .files {{ display:grid; gap:12px; margin-top:12px; }}
  .files img {{ max-width:100%; border:1px solid #d7dfdb; border-radius:6px; }}
  button {{ font:inherit; font-weight:bold; border:0; border-radius:8px; padding:12px 20px; cursor:pointer; }}
  .approve {{ background:#1f6f4a; color:#fff; }}
  .wide {{ width:100%; }}
  .changes {{ background:#fff; color:#b42318; border:1px solid #b42318; }}
  .neutral {{ background:#fff; color:#17201c; border:1px solid #aab5b0; }}
  textarea {{ width:100%; box-sizing:border-box; min-height:90px; font:inherit; padding:10px;
             border:1px solid #d7dfdb; border-radius:6px; margin:8px 0 12px; }}
  details summary {{ cursor:pointer; color:#b42318; font-weight:bold; margin-top:12px; }}
  .row {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-top:14px; }}
  .badge {{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:bold; font-size:14px; }}
  .badge.ok {{ background:#e3f3ea; color:#1f6f4a; }} .badge.warn {{ background:#fdecea; color:#b42318; }}
  .ok {{ color:#1f6f4a; }} .warn {{ color:#b42318; }}
</style></head>
<body><main>
<img src="{logo_url}" alt="{brand_name}" width="110">
{body}
</main></body></html>"""


def page(title, body, language):
    brand = get_brand()
    return HttpResponse(
        PAGE.format(
            lang=language, title=escape(title), body=body,
            brand_name=escape(brand["name"]), logo_url=escape(brand["logo_url"]),
        )
    )


def message_page(title, text, language, css="muted"):
    return page(title, f'<div class="card"><h1 class="{css}">{escape(title)}</h1><p>{text}</p></div>', language)


def files_html(request, issue, t):
    storage = S3Storage(request=request)
    parts = []
    for asset in proof_files(issue):
        name = asset.attributes.get("name") or "file"
        url = storage.generate_presigned_url(object_name=asset.asset.name, filename=name)
        if not url:
            continue
        if (asset.attributes.get("type") or "").startswith("image/"):
            parts.append(
                f'<a href="{escape(url)}" target="_blank" rel="noopener"><img src="{escape(url)}" alt="{escape(name)}"></a>'
            )
        else:
            parts.append(f'<a href="{escape(url)}" target="_blank" rel="noopener">📎 {escape(name)}</a>')
    return '<div class="files">' + "".join(parts) + "</div>" if parts else f'<p class="muted">{t["no_files"]}</p>'


def description_html(issue):
    text = escape((issue.description_stripped or "").strip()[:1200]).replace("\n", "<br>")
    return f"<p>{text}</p>" if text else ""


def note_html(note):
    return f"<blockquote><p>{escape(note).replace(chr(10), '<br>')}</p></blockquote>"


def move_issue(issue, new_state, actor_id):
    """Change the state the same way the app does, so history and staff notifications work."""
    if not new_state or issue.state_id == new_state.id:
        return
    old_state_id = str(issue.state_id)
    issue.state = new_state
    issue.save()
    issue_activity.delay(
        type="issue.activity.updated",
        requested_data=json.dumps({"state_id": str(new_state.id)}),
        current_instance=json.dumps({"state_id": old_state_id}),
        issue_id=str(issue.id),
        actor_id=str(actor_id),
        project_id=str(issue.project_id),
        epoch=int(timezone.now().timestamp()),
        notification=True,
    )


def decide_post(approval, post, response, note=""):
    """Record the client's answer for one post and move that post."""
    if ApprovalItemDecision.objects.filter(approval=approval, issue=post).exists():
        return
    ApprovalItemDecision.objects.create(
        approval=approval, issue=post, response=response, note=note, decided_at=timezone.now()
    )
    who = escape(approval.recipient_email)
    if response == "approved":
        move_issue(post, next_state_after(approval.state), approval.requested_by_id)
        add_comment(post, approval.requested_by_id, f"<p>✅ Εγκρίθηκε από τον πελάτη ({who}) μέσω email.</p>")
    else:
        move_issue(post, corrections_state(post.project_id), approval.requested_by_id)
        add_comment(post, approval.requested_by_id, f"<p>✏️ Ο πελάτης ({who}) ζήτησε αλλαγές:</p>{note_html(note)}")


def finish(approval, response, note=""):
    """Close the request and move the parent item on."""
    issue = approval.issue
    who = escape(approval.recipient_email)
    if response == "approved":
        next_state = next_state_after(approval.state)
        move_issue(issue, next_state, approval.requested_by_id)
        add_comment(
            issue, approval.requested_by_id,
            f"<p>✅ Εγκρίθηκε από τον πελάτη ({who}) μέσω email."
            + (f" Νέα κατάσταση: {escape(next_state.name)}." if next_state else "") + "</p>",
        )
    else:
        move_issue(issue, corrections_state(issue.project_id), approval.requested_by_id)
        add_comment(
            issue, approval.requested_by_id,
            f"<p>✏️ Ο πελάτης ({who}) ζήτησε αλλαγές.</p>" + (note_html(note) if note else ""),
        )
    approval.response = response
    approval.note = note
    approval.responded_at = timezone.now()
    approval.save(update_fields=["response", "note", "responded_at"])


def done_page(response, language):
    t = texts(language)
    if response == "approved":
        return message_page(t["done_approved_title"], t["done_approved_text"], language, "ok")
    return message_page(t["done_changes_title"], t["done_changes_text"], language, "ok")


@csrf_exempt
def client_approval(request, token):
    approval_id, version = read_token(token)
    approval = (
        ApprovalRequest.objects.select_related("issue", "state").filter(pk=approval_id).first()
        if approval_id else None
    )
    language = client_language(approval.issue) if approval else "el"
    t = texts(language)
    if not approval or approval.token_version != version:
        return message_page(t["invalid_title"], t["invalid_text"], language, "warn")
    issue = approval.issue

    if approval.responded_at:
        when = f"{approval.responded_at.astimezone(TZ):%d/%m/%Y %H:%M}"
        return message_page(t["answered_title"], t["answered_text"].format(name=escape(issue.name), when=when), language)
    if issue.state_id != approval.state_id or issue.deleted_at:
        return message_page(t["moved_title"], t["moved_text"].format(name=escape(issue.name)), language)

    posts = batch_posts(issue)
    decided = {d.issue_id: d for d in ApprovalItemDecision.objects.filter(approval=approval)}

    if request.method == "POST":
        action = request.POST.get("action")
        note = (request.POST.get("note") or "").strip()
        who = escape(approval.recipient_email)

        if action == "comment":
            if not note:
                return page(issue.name, form_html(request, approval, posts, decided, t, error=t["need_comment"]), language)
            add_comment(issue, approval.requested_by_id, f"<p>💬 Σχόλιο πελάτη ({who}):</p>{note_html(note)}")
            return message_page(t["done_comment_title"], t["done_comment_text"], language, "ok")

        if not posts:  # single item
            if action == "approve":
                finish(approval, "approved")
                return done_page("approved", language)
            if action == "changes" and note:
                finish(approval, "changes", note)
                return done_page("changes", language)
            return page(issue.name, form_html(request, approval, posts, decided, t, error=t["need_note"]), language)

        # batch
        by_id = {str(p.id): p for p in posts}
        if action == "approve_all":
            for post in posts:
                decide_post(approval, post, "approved")
        elif action in ("approve_item", "changes_item") and request.POST.get("item") in by_id:
            post = by_id[request.POST["item"]]
            if action == "approve_item":
                decide_post(approval, post, "approved")
            elif note:
                decide_post(approval, post, "changes", note)
            else:
                return page(issue.name, form_html(request, approval, posts, decided, t, error=t["need_note"]), language)

        decisions = list(ApprovalItemDecision.objects.filter(approval=approval, issue__in=posts))
        if len(decisions) == len(posts):
            response = "approved" if all(d.response == "approved" for d in decisions) else "changes"
            finish(approval, response)
            return done_page(response, language)
        return HttpResponseRedirect(request.path)  # show the page again with this post marked

    return page(issue.name, form_html(request, approval, posts, decided, t), language)


def changes_form(t, item_id=None):
    item_field = f'<input type="hidden" name="item" value="{item_id}">' if item_id else ""
    action = "changes_item" if item_id else "changes"
    return f"""<details><summary>{t['request_changes']}</summary>
  <form method="post"><input type="hidden" name="action" value="{action}">{item_field}
    <label>{t['changes_label']}<textarea name="note" required></textarea></label>
    <button class="changes" type="submit">{t['send_changes']}</button>
  </form></details>"""


def form_html(request, approval, posts, decided, t, error=""):
    issue = approval.issue
    error_html = f'<p class="warn"><strong>{escape(error)}</strong></p>' if error else ""
    comment_card = f"""<div class="card"><form method="post"><input type="hidden" name="action" value="comment">
  <label>{t['comment_label']}<textarea name="note"></textarea></label>
  <button class="neutral" type="submit">{t['send_comment']}</button></form></div>"""

    if not posts:
        return f"""<h1>{escape(issue.name)}</h1><p class="muted">{t['page_waiting']}</p>{error_html}
<div class="card">{description_html(issue)}{files_html(request, issue, t)}</div>
<div class="card">
  <form method="post"><input type="hidden" name="action" value="approve">
    <button class="approve wide" type="submit">{t['approve']}</button></form>
  {changes_form(t)}
</div>{comment_card}"""

    open_posts = [p for p in posts if p.id not in decided]
    cards = []
    for index, post in enumerate(posts, start=1):
        decision = decided.get(post.id)
        if decision:
            badge = (
                f'<span class="badge ok">{t["decided_approved"]}</span>' if decision.response == "approved"
                else f'<span class="badge warn">{t["decided_changes"]}</span>'
            )
            actions = f'<div class="row">{badge}</div>'
        else:
            actions = f"""<div class="row">
  <form method="post"><input type="hidden" name="action" value="approve_item"><input type="hidden" name="item" value="{post.id}">
    <button class="approve" type="submit">{t['approve']}</button></form>
</div>{changes_form(t, post.id)}"""
        cards.append(
            f'<div class="card"><h2>{index}. {escape(post.name)}</h2>{description_html(post)}'
            f"{files_html(request, post, t)}{actions}</div>"
        )
    approve_all = (
        f"""<div class="card"><form method="post"><input type="hidden" name="action" value="approve_all">
  <button class="approve wide" type="submit">{t['approve_all']}</button></form>
  <p class="muted">{t['remaining'].format(count=len(open_posts))}</p></div>"""
        if open_posts else ""
    )
    parent_description = description_html(issue)
    return (
        f'<h1>{escape(issue.name)}</h1><p class="muted">{t["page_waiting_batch"]}</p>{error_html}'
        + (f'<div class="card">{parent_description}</div>' if parent_description else "")
        + f"{approve_all}{''.join(cards)}{comment_card}"
    )

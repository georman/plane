# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: the public page a client opens from the approval email.
# GET shows the work and two choices; the choice itself is a POST so that
# link scanners in mail clients can never approve anything by opening it.
# The signed token in the URL is the only credential.

import json
from html import escape

from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from plane.bgtasks.gam_approval_task import add_comment, proof_files
from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import ApprovalRequest
from plane.settings.storage import S3Storage
from plane.utils.gam_approval import corrections_state, next_state_after, read_token

PAGE = """<!doctype html>
<html lang="el"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – GAM</title>
<style>
  body {{ margin:0; background:#f5f7f6; color:#17201c; font:16px/1.55 Arial, Helvetica, sans-serif; }}
  main {{ max-width:680px; margin:0 auto; padding:24px 16px 48px; }}
  .card {{ background:#fff; border:1px solid #d7dfdb; border-radius:10px; padding:20px; margin-top:16px; }}
  h1 {{ font-size:1.4rem; margin:12px 0 4px; }}
  .muted {{ color:#5a6862; }}
  .files {{ display:grid; gap:12px; margin-top:12px; }}
  .files img {{ max-width:100%; border:1px solid #d7dfdb; border-radius:6px; }}
  button {{ font:inherit; font-weight:bold; border:0; border-radius:8px; padding:14px 22px; cursor:pointer; }}
  .approve {{ background:#1f6f4a; color:#fff; width:100%; }}
  .changes {{ background:#fff; color:#b42318; border:1px solid #b42318; }}
  textarea {{ width:100%; box-sizing:border-box; min-height:110px; font:inherit; padding:10px;
             border:1px solid #d7dfdb; border-radius:6px; margin:8px 0 12px; }}
  .ok {{ color:#1f6f4a; }} .warn {{ color:#b42318; }}
</style></head>
<body><main>
<img src="https://project.gam.gr/assets/gam-logo.png" alt="GAM" width="110">
{body}
</main></body></html>"""


def page(title, body, status=200):
    return HttpResponse(PAGE.format(title=escape(title), body=body), status=status)


def message_page(title, text, css="muted"):
    return page(title, f'<div class="card"><h1 class="{css}">{escape(title)}</h1><p>{text}</p></div>')


def files_html(request, issue):
    storage = S3Storage(request=request)
    parts = []
    for asset in proof_files(issue):
        name = asset.attributes.get("name") or "file"
        url = storage.generate_presigned_url(object_name=asset.asset.name, filename=name)
        if not url:
            continue
        if (asset.attributes.get("type") or "").startswith("image/"):
            parts.append(f'<a href="{escape(url)}" target="_blank" rel="noopener"><img src="{escape(url)}" alt="{escape(name)}"></a>')
        else:
            parts.append(f'<a href="{escape(url)}" target="_blank" rel="noopener">📎 {escape(name)}</a>')
    return '<div class="files">' + "".join(parts) + "</div>" if parts else ""


def move_issue(approval, new_state):
    """Change the state the same way the app does, so history and staff notifications work."""
    issue = approval.issue
    old_state_id = str(issue.state_id)
    issue.state = new_state
    issue.save()
    issue_activity.delay(
        type="issue.activity.updated",
        requested_data=json.dumps({"state_id": str(new_state.id)}),
        current_instance=json.dumps({"state_id": old_state_id}),
        issue_id=str(issue.id),
        actor_id=str(approval.requested_by_id),
        project_id=str(issue.project_id),
        epoch=int(timezone.now().timestamp()),
        notification=True,
    )


@csrf_exempt
def client_approval(request, token):
    approval_id = read_token(token)
    approval = (
        ApprovalRequest.objects.select_related("issue", "state").filter(pk=approval_id).first()
        if approval_id else None
    )
    if not approval:
        return message_page(
            "Ο σύνδεσμος δεν ισχύει",
            "Ο σύνδεσμος έχει λήξει ή δεν είναι σωστός. Επικοινωνήστε μαζί μας για νέο.", "warn",
        )
    issue = approval.issue

    if approval.responded_at:
        answer = "εγκρίθηκε" if approval.response == "approved" else "ζητήθηκαν αλλαγές"
        return message_page(
            "Έχετε ήδη απαντήσει",
            f"Για την εργασία «{escape(issue.name)}» {answer} στις "
            f"{timezone.localtime(approval.responded_at):%d/%m/%Y %H:%M}. Ευχαριστούμε!",
        )
    if issue.state_id != approval.state_id or issue.deleted_at:
        return message_page(
            "Η εργασία έχει προχωρήσει",
            f"Η εργασία «{escape(issue.name)}» δεν περιμένει πλέον έγκριση. Αν χρειάζεστε κάτι, επικοινωνήστε μαζί μας.",
        )

    if request.method == "POST":
        action = request.POST.get("action")
        note = (request.POST.get("note") or "").strip()
        if action == "approve":
            next_state = next_state_after(approval.state)
            if next_state:
                move_issue(approval, next_state)
            add_comment(
                issue, approval.requested_by_id,
                f"<p>✅ Εγκρίθηκε από τον πελάτη ({escape(approval.recipient_email)}) μέσω email."
                + (f" Νέα κατάσταση: {escape(next_state.name)}." if next_state else "") + "</p>",
            )
            approval.response = "approved"
        elif action == "changes" and note:
            corrections = corrections_state(issue.project_id)
            if corrections:
                move_issue(approval, corrections)
            add_comment(
                issue, approval.requested_by_id,
                f"<p>✏️ Ο πελάτης ({escape(approval.recipient_email)}) ζήτησε αλλαγές:</p>"
                f"<blockquote><p>{escape(note).replace(chr(10), '<br>')}</p></blockquote>",
            )
            approval.response = "changes"
            approval.note = note
        else:
            return page(issue.name, form_html(request, approval, error="Γράψτε μας τι θέλετε να αλλάξει."))
        approval.responded_at = timezone.now()
        approval.save(update_fields=["response", "note", "responded_at"])
        if approval.response == "approved":
            return message_page("Ευχαριστούμε για την έγκριση!", "Προχωράμε στο επόμενο βήμα και θα σας ενημερώσουμε.", "ok")
        return message_page("Λάβαμε τις αλλαγές σας", "Θα κάνουμε τις διορθώσεις και θα σας στείλουμε νέα πρόταση.", "ok")

    return page(issue.name, form_html(request, approval))


def form_html(request, approval, error=""):
    issue = approval.issue
    description = escape((issue.description_stripped or "").strip()[:800])
    error_html = f'<p class="warn">{escape(error)}</p>' if error else ""
    return f"""
<h1>{escape(issue.name)}</h1>
<p class="muted">Η εργασία είναι έτοιμη για την έγκρισή σας.</p>
{f'<div class="card"><p>{description}</p></div>' if description else ''}
<div class="card">{files_html(request, issue) or '<p class="muted">Δεν υπάρχουν συνημμένα αρχεία.</p>'}</div>
<div class="card">
  <form method="post"><input type="hidden" name="action" value="approve">
    <button class="approve" type="submit">✓ Έγκριση</button>
  </form>
</div>
<div class="card">
  <form method="post"><input type="hidden" name="action" value="changes">
    <label for="note"><strong>Ζητώ αλλαγές</strong> – γράψτε μας τι θέλετε να αλλάξει:</label>
    <textarea id="note" name="note" required></textarea>
    {error_html}
    <button class="changes" type="submit">Αποστολή αλλαγών</button>
  </form>
</div>"""

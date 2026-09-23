# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: when a work item enters an approval state, email the
# customer a link to approve it or request changes (see
# plane/app/views/gam_approval.py for the page the link opens).

import logging
import os
from datetime import timedelta
from html import escape

from celery import shared_task
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

from plane.db.models import (
    ApprovalRequest,
    FileAsset,
    Issue,
    IssueComment,
    IssueCustomerService,
    State,
)
from plane.license.utils.gam_brand import client_email_settings, get_brand
from plane.license.utils.instance_value import get_email_configuration
from plane.settings.storage import S3Storage
from plane.utils.exception_logger import log_exception
from plane.utils.gam_approval import batch_posts, is_approval_state, make_token
from plane.utils.gam_client_texts import client_language, texts

# Proof files are attached to the email up to this total size; the approval page shows all of them
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_ATTACHMENTS = 5


def add_comment(issue, actor_id, html):
    IssueComment(
        comment_html=html,
        issue=issue,
        project_id=issue.project_id,
        workspace_id=issue.workspace_id,
        actor_id=actor_id,
    ).save()


def proof_files(issue):
    return FileAsset.objects.filter(
        issue_id=issue.id,
        entity_type=FileAsset.EntityTypeContext.ISSUE_ATTACHMENT,
        is_uploaded=True,
        deleted_at__isnull=True,
    ).order_by("-created_at")


def approval_url(approval):
    base = os.environ.get("WEB_URL", "https://project.gam.gr").rstrip("/")
    return f"{base}/api/gam/approval/{make_token(approval)}/"


def send_email(to, subject, html, text, files=()):
    host, user, password, port, use_tls, use_ssl, sender = get_email_configuration()
    connection = get_connection(
        host=host, port=int(port), username=user, password=password,
        use_tls=use_tls == "1", use_ssl=use_ssl == "1",
    )
    msg = EmailMultiAlternatives(subject=subject, body=text, from_email=sender, to=[to], connection=connection)
    msg.attach_alternative(html, "text/html")
    for name, content, mime in files:
        msg.attach(name, content, mime)
    msg.send()


def send_client_email(to, subject, html, text, files=()):
    """Every email meant for a client goes through here. In test mode it goes to the test address instead."""
    mode, test_email = client_email_settings()
    if mode == "live":
        send_email(to, subject, html, text, files)
        return to
    banner = (
        '<div style="background:#fff4e5;border:1px solid #f0a020;padding:10px 14px;margin-bottom:16px;'
        'font-family:Arial,sans-serif;font-size:14px">🧪 <strong>ΔΟΚΙΜΗ / TEST</strong> – '
        f"σε κανονική λειτουργία θα πήγαινε στο <strong>{escape(to)}</strong></div>"
    )
    send_email(test_email, f"[ΔΟΚΙΜΗ → {to}] {subject}", banner + html, f"[TEST - would go to {to}]\n\n{text}", files)
    return test_email


def email_shell(brand, language, body_html):
    t = texts(language)
    return f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;color:#17201c">
  <img src="{escape(brand['logo_url'])}" alt="{escape(brand['name'])}" width="120" style="margin:16px 0">
  <p>{t['greeting']}</p>
  {body_html}
  <p>{t['thanks']}<br>{escape(brand['name'])}</p>
</div>"""


def email_button(url, label):
    return (
        f'<p style="margin:28px 0"><a href="{url}" style="background:#1f6f4a;color:#ffffff;text-decoration:none;'
        f'padding:14px 26px;border-radius:8px;font-weight:bold;display:inline-block">{label}</a></p>'
    )


def render_request_email(issue, url, attached_names, other_count, language, post_count=0):
    brand = get_brand()
    t = texts(language)
    name = escape(issue.name)
    if attached_names:
        files_line = t["email_files_attached"].format(files=escape(", ".join(attached_names)))
        if other_count:
            files_line += t["email_files_more"].format(count=other_count)
    else:
        files_line = t["email_files_page"]
    intro = (
        t["email_intro_batch"].format(name=name, count=post_count) if post_count else t["email_intro"].format(name=name)
    )
    howto = t["email_howto_batch"] if post_count else t["email_howto"]
    body = (
        f"<p>{intro} {files_line}</p>{email_button(url, t['email_button'])}<p>{howto}</p>"
        f'<p style="color:#5a6862;font-size:13px">{t["email_link_note"]}</p>'
    )
    html = email_shell(brand, language, body)
    text = f"{issue.name}\n\n{url}\n\n{brand['name']}"
    return html, text


def collect_email_files(issues):
    """Attach proof files from these items, up to MAX_ATTACHMENTS / MAX_ATTACHMENT_BYTES."""
    storage = S3Storage()
    files, names, total, other = [], [], 0, 0
    for issue in issues:
        for asset in proof_files(issue):
            size = int(asset.size or asset.attributes.get("size") or 0)
            file_name = asset.attributes.get("name") or "file"
            if len(files) < MAX_ATTACHMENTS and total + size <= MAX_ATTACHMENT_BYTES:
                body = storage.s3_client.get_object(Bucket=storage.aws_storage_bucket_name, Key=asset.asset.name)
                files.append((file_name, body["Body"].read(), asset.attributes.get("type") or "application/octet-stream"))
                names.append(file_name)
                total += size
            else:
                other += 1
    return files, names, other


@shared_task
def send_approval_request(issue_id, state_id, actor_id):
    try:
        issue = Issue.objects.get(pk=issue_id)
        if str(issue.state_id) != str(state_id):
            return  # moved on before the email went out

        # A state change can be recorded twice in quick succession; send once
        if ApprovalRequest.objects.filter(
            issue=issue, state_id=state_id, responded_at__isnull=True,
            created_at__gte=timezone.now() - timedelta(minutes=2),
        ).exists():
            return

        link = IssueCustomerService.objects.filter(issue=issue).select_related("customer").first()
        email = (link.customer.contact_email or "").strip() if link else ""
        if not email:
            add_comment(
                issue, actor_id,
                "<p>⚠️ Δεν στάλθηκε email έγκρισης: ορίστε πελάτη με email σε αυτή την εργασία "
                "(Customer στη φόρμα της εργασίας, email στο Settings → Customers) και ξαναβάλτε την σε "
                "κατάσταση έγκρισης.</p>",
            )
            return

        # Older unanswered requests for this item are replaced by this one
        ApprovalRequest.objects.filter(issue=issue, responded_at__isnull=True).delete()
        approval = ApprovalRequest.objects.create(
            issue=issue, state_id=state_id, recipient_email=email, requested_by_id=actor_id
        )

        language = client_language(issue)
        posts = batch_posts(issue)
        files, attached_names, other_count = collect_email_files(posts or [issue])
        html, text = render_request_email(
            issue, approval_url(approval), attached_names, other_count, language, post_count=len(posts)
        )
        subject = texts(language)["email_subject"].format(name=issue.name, brand=get_brand()["name"])
        delivered_to = send_client_email(email, subject, html, text, files)

        approval.sent_at = timezone.now()
        approval.save(update_fields=["sent_at"])
        note = "" if delivered_to == email else f" (δοκιμαστική λειτουργία: στάλθηκε στο {escape(delivered_to)})"
        add_comment(issue, actor_id, f"<p>📧 Στάλθηκε email έγκρισης στο {escape(email)}{note}.</p>")
        logging.getLogger("plane.worker").info("GAM approval request sent for %s", issue_id)
    except Exception as e:
        log_exception(e)


def queue_approval_requests(issue_activities):
    """Called after activities are saved: any move into an approval state triggers an email."""
    for activity in issue_activities:
        if activity.field != "state" or not activity.new_identifier:
            continue
        state = State.objects.filter(pk=activity.new_identifier).first()
        if is_approval_state(state):
            send_approval_request.delay(str(activity.issue_id), str(state.id), str(activity.actor_id))

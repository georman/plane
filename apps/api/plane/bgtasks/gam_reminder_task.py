# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: reminders.
# - Clients who haven't answered an approval email get a reminder after 3
#   working days, at most twice.
# - Every working morning each team member gets one email listing their
#   items due tomorrow, overdue, or stuck in the same state for 5+ working days.

from collections import defaultdict
from datetime import timedelta
from html import escape

from celery import shared_task
from django.utils import timezone

from plane.db.models import ApprovalRequest, Issue, IssueActivity, IssueAssignee
from plane.license.utils.gam_brand import get_brand
from plane.utils.exception_logger import log_exception
from plane.utils.gam_worktime import TZ, is_working_time, working_days_between

APPROVAL_REMINDER_AFTER_DAYS = 3
MAX_APPROVAL_REMINDERS = 2
STUCK_AFTER_DAYS = 5


@shared_task
def send_approval_reminders():
    from plane.bgtasks.gam_approval_task import add_comment, approval_url, send_email

    now = timezone.now()
    if not is_working_time(now):
        return
    pending = ApprovalRequest.objects.filter(
        responded_at__isnull=True, sent_at__isnull=False, reminder_count__lt=MAX_APPROVAL_REMINDERS,
        issue__deleted_at__isnull=True,
    ).select_related("issue")
    brand = get_brand()
    for approval in pending:
        try:
            issue = approval.issue
            if issue.state_id != approval.state_id:
                continue  # moved on without the client answering by email
            last = approval.last_reminder_at or approval.sent_at
            if working_days_between(last, now) < APPROVAL_REMINDER_AFTER_DAYS:
                continue
            url = approval_url(approval)
            html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;color:#17201c">
  <img src="{escape(brand['logo_url'])}" alt="{escape(brand['name'])}" width="120" style="margin:16px 0">
  <p>Γεια σας,</p>
  <p>Σας υπενθυμίζουμε ότι η εργασία <strong>«{escape(issue.name)}»</strong> περιμένει την έγκρισή σας.</p>
  <p style="margin:28px 0">
    <a href="{url}" style="background:#1f6f4a;color:#ffffff;text-decoration:none;padding:14px 26px;border-radius:8px;font-weight:bold;display:inline-block">Δείτε και εγκρίνετε</a>
  </p>
  <p style="color:#5a6862;font-size:13px">Reminder: your approval is still needed.</p>
  <p>Ευχαριστούμε,<br>{escape(brand['name'])}</p>
</div>"""
            text = f"Υπενθύμιση: η εργασία «{issue.name}» περιμένει την έγκρισή σας.\n\n{url}\n\n{brand['name']}"
            send_email(approval.recipient_email, f"Υπενθύμιση έγκρισης: {issue.name} – {brand['name']}", html, text)
            approval.reminder_count += 1
            approval.last_reminder_at = now
            approval.save(update_fields=["reminder_count", "last_reminder_at"])
            add_comment(
                issue, approval.requested_by_id,
                f"<p>🔔 Στάλθηκε υπενθύμιση έγκρισης ({approval.reminder_count}/{MAX_APPROVAL_REMINDERS}) "
                f"στο {escape(approval.recipient_email)}.</p>",
            )
        except Exception as e:
            log_exception(e)


def _last_state_change(issue):
    last = IssueActivity.objects.filter(issue=issue, field="state").order_by("-created_at").values_list(
        "created_at", flat=True
    ).first()
    return last or issue.created_at


@shared_task
def send_daily_digest():
    from plane.bgtasks.gam_approval_task import send_email
    from plane.bgtasks.gam_sla_task import item_url

    now = timezone.now()
    today = now.astimezone(TZ).date()
    if today.weekday() >= 5:
        return
    # Friday's "due tomorrow" covers the weekend and Monday
    horizon = today + timedelta(days=3 if today.weekday() == 4 else 1)

    open_items = Issue.issue_objects.filter(
        state__group__in=["backlog", "unstarted", "started"], archived_at__isnull=True, is_draft=False,
    ).select_related("project", "workspace", "state")
    per_user = defaultdict(lambda: {"overdue": [], "due": [], "stuck": []})
    assignments = IssueAssignee.objects.filter(
        issue__in=open_items, assignee__is_active=True, assignee__is_bot=False
    ).select_related("assignee", "issue", "issue__project", "issue__workspace", "issue__state")
    for link in assignments:
        issue, email = link.issue, link.assignee.email
        if issue.target_date and issue.target_date < today:
            per_user[email]["overdue"].append(issue)
        elif issue.target_date and issue.target_date <= horizon:
            per_user[email]["due"].append(issue)
        elif issue.state.group == "started" and working_days_between(_last_state_change(issue), now) >= STUCK_AFTER_DAYS:
            per_user[email]["stuck"].append(issue)

    brand = get_brand()
    sections = [
        ("overdue", "🔴 Εκπρόθεσμες"),
        ("due", "🟠 Λήγουν σύντομα"),
        ("stuck", "⏸️ Κολλημένες 5+ εργάσιμες στην ίδια κατάσταση"),
    ]
    for email, groups in per_user.items():
        try:
            parts = []
            for key, title in sections:
                items = groups[key]
                if not items:
                    continue
                rows = "".join(
                    f'<li><a href="{item_url(i)}">{escape(i.project.identifier)}-{i.sequence_id}</a> '
                    f"{escape(i.name)} – <em>{escape(i.state.name)}</em>"
                    + (f" – προθεσμία {i.target_date:%d/%m}" if i.target_date else "")
                    + "</li>"
                    for i in items
                )
                parts.append(f"<h3 style='margin:18px 0 6px'>{title} ({len(items)})</h3><ul>{rows}</ul>")
            if not parts:
                continue
            html = (
                "<div style='font-family:Arial,Helvetica,sans-serif;max-width:640px;color:#17201c'>"
                f"<p>Καλημέρα! Οι εργασίες σας που χρειάζονται προσοχή σήμερα:</p>{''.join(parts)}"
                f"<p style='color:#5a6862;font-size:13px'>{escape(brand['name'])}</p></div>"
            )
            count = sum(len(v) for v in groups.values())
            send_email(email, f"{brand['name']}: {count} εργασίες θέλουν προσοχή σήμερα", html,
                       "Οι εργασίες σας που χρειάζονται προσοχή: δείτε το email σε HTML.")
        except Exception as e:
            log_exception(e)

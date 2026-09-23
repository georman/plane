# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: first-response SLA for Customer Support and Hosting.
# A new item gets a response deadline in working hours based on its
# priority. It counts as answered when a team member comments or moves it
# out of the backlog states. Staff get a warning at 75% of the time and an
# alert when the deadline passes.

from html import escape

from celery import shared_task
from django.utils import timezone

from plane.db.models import Issue, IssueAssignee, IssueSLA, ProjectMember, State, WorkspaceMember
from plane.license.utils.gam_brand import get_brand, web_url
from plane.utils.exception_logger import log_exception
from plane.utils.gam_worktime import TZ, add_working_hours, working_seconds_between

# Projects with an SLA, by identifier
SLA_PROJECTS = {"SUP", "HOST"}
# Working hours to first response, by priority
SLA_HOURS = {"urgent": 2, "high": 8}
DEFAULT_SLA_HOURS = 24
WARN_AT = 0.75
PRIORITY_LABELS = {"urgent": "Επείγον", "high": "Υψηλή", "medium": "Μεσαία", "low": "Χαμηλή", "none": "Χωρίς"}


def sla_hours(priority):
    return SLA_HOURS.get(priority, DEFAULT_SLA_HOURS)


def item_url(issue):
    return f"{web_url()}/{issue.workspace.slug}/browse/{issue.project.identifier}-{issue.sequence_id}/"


def staff_recipients(issue):
    """Assignees, or the project's admins when nobody is assigned."""
    emails = list(
        IssueAssignee.objects.filter(issue=issue, assignee__is_active=True, assignee__is_bot=False)
        .values_list("assignee__email", flat=True)
    )
    if not emails:
        emails = list(
            ProjectMember.objects.filter(project_id=issue.project_id, role=20, is_active=True, member__is_bot=False)
            .values_list("member__email", flat=True)
        )
    return sorted(set(e for e in emails if e))


def start_sla(issue_id):
    issue = Issue.objects.select_related("project").filter(pk=issue_id).first()
    if not issue or issue.project.identifier not in SLA_PROJECTS or issue.parent_id:
        return
    if IssueSLA.objects.filter(issue=issue).exists():
        return
    started = issue.created_at or timezone.now()
    IssueSLA.objects.create(
        issue=issue, priority=issue.priority, started_at=started,
        due_at=add_working_hours(started, sla_hours(issue.priority)),
    )


def update_sla_priority(issue_id):
    sla = IssueSLA.objects.filter(issue_id=issue_id, responded_at__isnull=True, breached_at__isnull=True).first()
    if not sla:
        return
    issue = sla.issue
    if issue.priority != sla.priority:
        sla.priority = issue.priority
        sla.due_at = add_working_hours(sla.started_at, sla_hours(issue.priority))
        sla.warned_at = None
        sla.save(update_fields=["priority", "due_at", "warned_at"])


def mark_responded(issue_id, actor_id):
    sla = IssueSLA.objects.filter(issue_id=issue_id, responded_at__isnull=True).select_related("issue").first()
    if not sla:
        return
    # Only the team counts as a response, not the client commenting on their own request
    is_staff = WorkspaceMember.objects.filter(
        workspace_id=sla.issue.workspace_id, member_id=actor_id, role__gte=15, is_active=True
    ).exists()
    if is_staff:
        sla.responded_at = timezone.now()
        sla.save(update_fields=["responded_at"])


def handle_activities(issue_activities):
    """Called after activities are saved (see issue_activities_task)."""
    for activity in issue_activities:
        try:
            if activity.verb == "created" and not activity.field:
                start_sla(activity.issue_id)
            elif activity.field == "priority":
                update_sla_priority(activity.issue_id)
            elif activity.field == "comment" and activity.verb == "created":
                mark_responded(activity.issue_id, activity.actor_id)
            elif activity.field == "state" and activity.new_identifier:
                state = State.objects.filter(pk=activity.new_identifier).first()
                if state and state.group not in ("backlog", "triage"):
                    mark_responded(activity.issue_id, activity.actor_id)
        except Exception as e:
            log_exception(e)


def alert(sla, kind):
    from plane.bgtasks.gam_approval_task import add_comment, send_email

    issue = sla.issue
    brand = get_brand()
    priority = PRIORITY_LABELS.get(sla.priority, sla.priority)
    due = sla.due_at.astimezone(TZ).strftime("%d/%m %H:%M")
    if kind == "warn":
        subject = f"⚠️ SLA: απάντηση μέχρι {due} – {issue.project.identifier}-{issue.sequence_id}"
        headline = f"Η προθεσμία πρώτης απάντησης λήγει στις <strong>{due}</strong>."
        comment = f"<p>⚠️ SLA: η πρώτη απάντηση πρέπει να δοθεί μέχρι {due}.</p>"
    else:
        subject = f"⏰ SLA έληξε – {issue.project.identifier}-{issue.sequence_id}: {issue.name}"
        headline = f"Η προθεσμία πρώτης απάντησης έληξε στις <strong>{due}</strong> χωρίς απάντηση."
        comment = f"<p>⏰ SLA: η προθεσμία πρώτης απάντησης ({due}) έληξε.</p>"
    url = item_url(issue)
    html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;color:#17201c">
  <p>{headline}</p>
  <p><strong>{escape(issue.project.identifier)}-{issue.sequence_id}: {escape(issue.name)}</strong><br>
  Προτεραιότητα: {escape(priority)} (στόχος {sla_hours(sla.priority)} ώρες εργασίας)</p>
  <p><a href="{url}">Άνοιγμα στο {escape(brand['name'])}</a></p>
</div>"""
    text = f"{subject}\n\n{issue.name}\n{url}"
    for email in staff_recipients(issue):
        send_email(email, subject, html, text)
    add_comment(issue, issue.created_by_id, comment)


@shared_task
def check_slas():
    now = timezone.now()
    open_slas = IssueSLA.objects.filter(
        responded_at__isnull=True, breached_at__isnull=True, issue__deleted_at__isnull=True
    ).select_related("issue", "issue__project", "issue__workspace", "issue__state")
    for sla in open_slas:
        try:
            if sla.issue.state and sla.issue.state.group in ("completed", "cancelled"):
                sla.responded_at = now  # closed without a comment still counts as handled
                sla.save(update_fields=["responded_at"])
                continue
            if now >= sla.due_at:
                alert(sla, "breach")
                sla.breached_at = now
                sla.save(update_fields=["breached_at"])
            elif not sla.warned_at:
                total = working_seconds_between(sla.started_at, sla.due_at)
                used = working_seconds_between(sla.started_at, now)
                if total and used / total >= WARN_AT:
                    alert(sla, "warn")
                    sla.warned_at = now
                    sla.save(update_fields=["warned_at"])
        except Exception as e:
            log_exception(e)

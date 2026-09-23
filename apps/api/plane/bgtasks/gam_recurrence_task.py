# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: creates the next copy of every repeating work item whose
# next_run_date has arrived. See plane/db/models/recurrence.py.

from datetime import date

from celery import shared_task
from django.db import transaction

from plane.db.models import (
    Issue,
    IssueAssignee,
    IssueCustomerService,
    IssueLabel,
    IssueRecurrence,
)
from plane.utils.exception_logger import log_exception


def copy_issue_for_next_period(issue, period):
    """Copy an item with its dates moved forward by one period. The copy starts in the default state."""
    copy = Issue(
        name=issue.name,
        description_html=issue.description_html or "<p></p>",
        priority=issue.priority,
        project_id=issue.project_id,
        workspace_id=issue.workspace_id,
        start_date=issue.start_date + period if issue.start_date else None,
        target_date=issue.target_date + period if issue.target_date else None,
        created_by_id=issue.created_by_id,
    )
    copy.save()

    for assignee_id in IssueAssignee.objects.filter(issue=issue).values_list("assignee_id", flat=True):
        IssueAssignee.objects.create(issue=copy, assignee_id=assignee_id, project_id=issue.project_id,
                                     workspace_id=issue.workspace_id)
    for label_id in IssueLabel.objects.filter(issue=issue).values_list("label_id", flat=True):
        IssueLabel.objects.create(issue=copy, label_id=label_id, project_id=issue.project_id,
                                  workspace_id=issue.workspace_id)

    # Fresh checklist: from the service template when there is one, otherwise the original's sub-item names
    link = IssueCustomerService.objects.filter(issue=issue).first()
    if link:
        IssueCustomerService.objects.create(issue=copy, customer_id=link.customer_id, service_id=link.service_id)
    from plane.app.views.billing import create_service_sub_items

    if link and link.service.template_items.exists():
        create_service_sub_items(copy, link.service_id, None)
    else:
        for name in Issue.issue_objects.filter(parent=issue).order_by("sequence_id").values_list("name", flat=True):
            Issue(name=name, parent=copy, project_id=copy.project_id, workspace_id=copy.workspace_id,
                  created_by_id=issue.created_by_id).save()
    return copy


@shared_task
def create_due_recurring_items():
    today = date.today()
    for recurrence in IssueRecurrence.objects.filter(next_run_date__lte=today).select_related("issue"):
        try:
            with transaction.atomic():
                issue = recurrence.issue
                # Catch up if the task didn't run for a while, but create at most one copy per day
                next_run = recurrence.next_run_date
                while next_run + recurrence.period <= today:
                    next_run += recurrence.period
                copy = copy_issue_for_next_period(issue, recurrence.period)
                recurrence.issue = copy
                recurrence.next_run_date = next_run + recurrence.period
                recurrence.save()
        except Exception as e:
            log_exception(e)

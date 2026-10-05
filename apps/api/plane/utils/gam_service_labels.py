# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: in a project linked to a customer, every service the customer
# has a price for is also a label with the service's name. Staff only pick
# labels; putting a service label on a work item links it to that customer +
# service for billing, and taking the label off removes the link.

from plane.db.models import (
    CustomerServiceRate,
    Issue,
    IssueCustomerService,
    IssueLabel,
    Label,
    Project,
)


def ensure_service_labels(customer):
    """Create a label for each priced service in each of the customer's projects."""
    service_names = list(
        CustomerServiceRate.objects.filter(customer=customer, service__is_active=True).values_list(
            "service__name", flat=True
        )
    )
    for project in Project.objects.filter(customer=customer):
        existing = set(Label.objects.filter(project=project).values_list("name", flat=True))
        for name in service_names:
            if name not in existing:
                Label.objects.create(project=project, workspace_id=project.workspace_id, name=name)


def set_issue_service(issue, customer_id, service_id, user):
    """Link a work item to a customer + service. Returns the link."""
    from plane.app.views.billing import create_service_sub_items

    previous_service_id = IssueCustomerService.objects.filter(issue=issue).values_list("service_id", flat=True).first()
    # a removed link is soft-deleted but still holds the one-per-item slot
    IssueCustomerService.all_objects.filter(issue=issue, deleted_at__isnull=False).delete()
    link, _ = IssueCustomerService.objects.update_or_create(
        issue=issue, defaults={"customer_id": customer_id, "service_id": service_id}
    )
    if str(previous_service_id) != str(service_id):
        create_service_sub_items(issue, service_id, user)
    return link


def sync_issue_service_from_labels(issue_id, actor_id=None):
    issue = Issue.objects.filter(pk=issue_id).select_related("project").first()
    if not issue or not issue.project.customer_id:
        return
    customer_id = issue.project.customer_id
    label_names = set(
        IssueLabel.objects.filter(issue_id=issue_id, label__deleted_at__isnull=True).values_list(
            "label__name", flat=True
        )
    )
    rates = list(
        CustomerServiceRate.objects.filter(
            customer_id=customer_id, service__name__in=label_names, service__is_active=True
        ).order_by("service__name")
    )
    link = IssueCustomerService.objects.filter(issue_id=issue_id).select_related("service").first()

    if rates:
        if link and link.customer_id == customer_id and any(r.service_id == link.service_id for r in rates):
            return
        set_issue_service(issue, customer_id, rates[0].service_id, actor_id and _user(actor_id))
        return

    # No service label any more: drop a link that came from one (a label with
    # the service's name exists in this project but isn't on the item).
    if (
        link
        and link.customer_id == customer_id
        and Label.objects.filter(project_id=issue.project_id, name=link.service.name).exists()
    ):
        link.delete(soft=False)


def _user(user_id):
    from plane.db.models import User

    return User.objects.filter(pk=user_id).first()

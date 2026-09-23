# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: client approval by email. One row per request sent when a
# work item enters an approval state; the client's answer (approve or
# request changes) is recorded here and moves the item on.

from django.conf import settings
from django.db import models

from .base import BaseModel


class ApprovalRequest(BaseModel):
    RESPONSE_CHOICES = (
        ("approved", "Approved"),
        ("changes", "Changes requested"),
    )

    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="gam_approval_requests")
    state = models.ForeignKey("db.State", on_delete=models.CASCADE, related_name="gam_approval_requests")
    recipient_email = models.CharField(max_length=255)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="gam_approval_requests"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    response = models.CharField(max_length=20, choices=RESPONSE_CHOICES, null=True, blank=True)
    note = models.TextField(blank=True)
    # Bumped every time a new link is emailed; older links stop working
    token_version = models.PositiveIntegerField(default=1)
    reminder_count = models.PositiveIntegerField(default=0)
    last_reminder_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "gam_approval_requests"
        verbose_name = "Approval Request"
        verbose_name_plural = "Approval Requests"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.issue_id} -> {self.recipient_email} ({self.response or 'pending'})"


class ApprovalItemDecision(BaseModel):
    """The client's answer for one post (sub-item) inside a batch approval."""

    approval = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name="decisions")
    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="gam_approval_decisions")
    response = models.CharField(max_length=20, choices=ApprovalRequest.RESPONSE_CHOICES)
    note = models.TextField(blank=True)
    decided_at = models.DateTimeField()

    class Meta:
        db_table = "gam_approval_item_decisions"
        verbose_name = "Approval Item Decision"
        verbose_name_plural = "Approval Item Decisions"
        unique_together = ("approval", "issue")

# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: first-response SLA for support-type projects. The clock runs
# in working hours only (see plane/utils/gam_worktime.py).

from django.db import models

from .base import BaseModel


class IssueSLA(BaseModel):
    issue = models.OneToOneField("db.Issue", on_delete=models.CASCADE, related_name="gam_sla")
    priority = models.CharField(max_length=30)
    started_at = models.DateTimeField()
    due_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    warned_at = models.DateTimeField(null=True, blank=True)
    breached_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "gam_issue_slas"
        verbose_name = "Issue SLA"
        verbose_name_plural = "Issue SLAs"

    def __str__(self):
        return f"{self.issue_id} due {self.due_at}"

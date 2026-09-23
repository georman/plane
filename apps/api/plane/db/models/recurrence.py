# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: repeating work items (weekly IG posts, monthly retainers,
# yearly hosting renewals). Plane CE has no recurring work items - a daily
# Celery task (plane.bgtasks.gam_recurrence_task) creates the next copy
# when next_run_date arrives and moves the recurrence onto that copy.

from datetime import date

from dateutil.relativedelta import relativedelta
from django.db import models

from .base import BaseModel


class IssueRecurrence(BaseModel):
    FREQUENCY_CHOICES = (
        ("weekly", "Every week"),
        ("monthly", "Every month"),
        ("yearly", "Every year"),
    )
    PERIODS = {
        "weekly": relativedelta(weeks=1),
        "monthly": relativedelta(months=1),
        "yearly": relativedelta(years=1),
    }

    issue = models.OneToOneField(
        "db.Issue", on_delete=models.CASCADE, related_name="gam_recurrence"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_run_date = models.DateField()

    class Meta:
        db_table = "gam_issue_recurrences"
        verbose_name = "Issue Recurrence"
        verbose_name_plural = "Issue Recurrences"

    def __str__(self):
        return f"{self.issue_id}: {self.frequency} (next {self.next_run_date})"

    @property
    def period(self):
        return self.PERIODS[self.frequency]

    @classmethod
    def first_run_date(cls, issue, frequency):
        """The next copy is due one period after the item's start (or due) date, or after today."""
        base = issue.start_date or issue.target_date or date.today()
        return base + cls.PERIODS[frequency]

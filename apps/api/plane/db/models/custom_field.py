# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: custom fields. A project admin defines extra fields for the
# project's work items (quantity, paper type, PO number, ...); everyone on the
# project fills them in on the work item.

from django.db import models

from .base import BaseModel


class CustomField(BaseModel):
    TYPE_CHOICES = (
        ("text", "Text"),
        ("number", "Number"),
        ("date", "Date"),
        ("select", "Dropdown"),
        ("checkbox", "Checkbox"),
    )

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="custom_fields")
    project = models.ForeignKey("db.Project", on_delete=models.CASCADE, related_name="custom_fields")
    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="text")
    # Choices of a dropdown field
    options = models.JSONField(default=list, blank=True)
    sequence = models.FloatField(default=65535)

    class Meta:
        db_table = "gam_custom_fields"
        verbose_name = "Custom Field"
        verbose_name_plural = "Custom Fields"
        # A deleted field's name can be used again
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                condition=models.Q(deleted_at__isnull=True),
                name="gam_custom_field_unique_name_when_active",
            )
        ]
        ordering = ("sequence", "created_at")

    def __str__(self):
        return f"{self.project_id}: {self.name}"


class IssueCustomFieldValue(BaseModel):
    """One work item's value for one custom field, stored as text
    (numbers as written, dates as YYYY-MM-DD, checkboxes as "true")."""

    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="custom_field_values")
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name="values")
    value = models.TextField(blank=True, default="")

    class Meta:
        db_table = "gam_issue_custom_field_values"
        verbose_name = "Issue Custom Field Value"
        verbose_name_plural = "Issue Custom Field Values"
        # Cleared values are stored as "" rather than deleted, so this stays unique
        unique_together = ("issue", "field")

    def __str__(self):
        return f"{self.issue_id} / {self.field_id}: {self.value}"

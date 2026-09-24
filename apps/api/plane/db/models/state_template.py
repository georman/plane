# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: state templates. Workspace admins keep named sets of states
# (e.g. "GAM pipeline", "Printing"); a project can start from one or have one
# applied later (plane/utils/gam_state_templates.py).

from django.db import models

from .base import BaseModel

# Same as StateGroup, without Triage (importing it here would be circular)
TEMPLATE_GROUP_CHOICES = [
    ("backlog", "Backlog"),
    ("unstarted", "Unstarted"),
    ("started", "Started"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]


class StateTemplate(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="state_templates")
    name = models.CharField(max_length=255)
    # New projects start from this template unless another one is picked
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "gam_state_templates"
        verbose_name = "State Template"
        verbose_name_plural = "State Templates"
        unique_together = ("workspace", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class StateTemplateItem(BaseModel):
    template = models.ForeignKey(StateTemplate, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255, default="#60646C")
    group = models.CharField(max_length=20, choices=TEMPLATE_GROUP_CHOICES, default="backlog")
    sequence = models.FloatField(default=65535)
    # The state new work items start in
    default = models.BooleanField(default=False)

    class Meta:
        db_table = "gam_state_template_items"
        verbose_name = "State Template Item"
        verbose_name_plural = "State Template Items"
        ordering = ("sequence", "created_at")

    def __str__(self):
        return f"{self.template.name}: {self.name}"

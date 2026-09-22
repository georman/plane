# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: audit log for the workspace-admin "log in as member" feature.

from django.conf import settings
from django.db import models

from .base import BaseModel


class ImpersonationLog(BaseModel):
    workspace = models.ForeignKey(
        "db.Workspace", on_delete=models.CASCADE, related_name="impersonation_logs"
    )
    impersonator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="impersonations_performed",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="impersonations_received",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "impersonation_logs"
        verbose_name = "Impersonation Log"
        verbose_name_plural = "Impersonation Logs"
        ordering = ("-started_at",)

    def __str__(self):
        return f"{self.impersonator_id} as {self.target_user_id} in {self.workspace_id}"

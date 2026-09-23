# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: API-key endpoints used by n8n automations.

from django.urls import path

from plane.api.views.gam_email_intake import EmailIntakeEndpoint

urlpatterns = [
    path("workspaces/<str:slug>/gam/email-intake/", EmailIntakeEndpoint.as_view(), name="gam-email-intake"),
]

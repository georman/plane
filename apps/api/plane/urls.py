# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""plane URL Configuration"""

from django.apps import apps
from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from plane.app.views.gam_approval import client_approval
from plane.app.views.gam_billing import billing_review

handler404 = "plane.app.views.error_404.custom_404_view"

urlpatterns = [
    # GAM addition: public client approval page (link from the approval email)
    path("api/gam/approval/<str:token>/", client_approval, name="gam-client-approval"),
    # GAM addition: "Approve & send" for monthly billing statements (link emailed to GAM only)
    path("api/gam/billing/<str:token>/", billing_review, name="gam-billing-review"),
    path("api/", include("plane.app.urls")),
    path("api/public/", include("plane.space.urls")),
    path("api/instances/", include("plane.license.urls")),
    path("api/v1/", include("plane.api.urls")),
    path("auth/", include("plane.authentication.urls")),
    path("", include("plane.web.urls")),
]

if settings.ENABLE_DRF_SPECTACULAR:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

if settings.DEBUG and apps.is_installed("debug_toolbar"):
    try:
        import debug_toolbar

        urlpatterns = [re_path(r"^__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

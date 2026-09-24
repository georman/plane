# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path


from plane.app.views import (
    CustomFieldViewSet,
    IntakeStateEndpoint,
    IssueCustomFieldValuesEndpoint,
    ProjectStateTemplateEndpoint,
    StateViewSet,
)


urlpatterns = [
    # GAM: custom fields
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/custom-fields/",
        CustomFieldViewSet.as_view({"get": "list", "post": "create"}),
        name="project-custom-fields",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/custom-fields/<uuid:pk>/",
        CustomFieldViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="project-custom-fields",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/issues/<uuid:issue_id>/custom-field-values/",
        IssueCustomFieldValuesEndpoint.as_view(),
        name="issue-custom-field-values",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/state-template/",
        ProjectStateTemplateEndpoint.as_view(),
        name="project-state-template",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/",
        StateViewSet.as_view({"get": "list", "post": "create"}),
        name="project-states",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/<uuid:pk>/",
        StateViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="project-state",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/intake-state/",
        IntakeStateEndpoint.as_view(),
        name="intake-state",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/<uuid:pk>/mark-default/",
        StateViewSet.as_view({"post": "mark_as_default"}),
        name="project-state",
    ),
]

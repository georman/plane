# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: state templates. Admins manage them in workspace settings;
# project admins apply one to their project.

from django.db import IntegrityError, transaction
from django.db.models import Max

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.serializers import StateTemplateItemSerializer, StateTemplateSerializer
from plane.db.models import Project, StateTemplate, StateTemplateItem, Workspace
from plane.utils.gam_i18n import message
from plane.utils.gam_state_templates import apply_state_template

from .base import BaseAPIView, BaseViewSet


class StateTemplateViewSet(BaseViewSet):
    serializer_class = StateTemplateSerializer
    model = StateTemplate

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .prefetch_related("items")
            .order_by("name")
        )

    # Members see the list too: they pick a template when creating a project
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def list(self, request, slug):
        return Response(StateTemplateSerializer(self.get_queryset(), many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        try:
            serializer = StateTemplateSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save(workspace_id=workspace.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({"error": message(request, "A template with this name already exists.", "Υπάρχει ήδη πρότυπο με αυτό το όνομα.")}, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = StateTemplateSerializer(instance=self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    template = serializer.save()
                # Only one default template per workspace
                if template.is_default:
                    StateTemplate.objects.filter(workspace_id=template.workspace_id).exclude(pk=template.pk).update(
                        is_default=False
                    )
            except IntegrityError:
                return Response(
                    {"error": message(request, "A template with this name already exists.", "Υπάρχει ήδη πρότυπο με αυτό το όνομα.")}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class StateTemplateItemViewSet(BaseViewSet):
    serializer_class = StateTemplateItemSerializer
    model = StateTemplateItem

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(template__workspace__slug=self.kwargs.get("slug"), template_id=self.kwargs.get("template_id"))
        )

    def _set_only_default(self, item):
        if item.default:
            StateTemplateItem.objects.filter(template_id=item.template_id).exclude(pk=item.pk).update(default=False)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug, template_id):
        template = StateTemplate.objects.get(pk=template_id, workspace__slug=slug)
        last = template.items.aggregate(largest=Max("sequence"))["largest"]
        serializer = StateTemplateItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save(
                template_id=template.id,
                sequence=request.data.get("sequence", (last or 0) + 5000),
            )
            self._set_only_default(item)
            return Response(StateTemplateItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = StateTemplateItemSerializer(instance=self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            item = serializer.save()
            self._set_only_default(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProjectStateTemplateEndpoint(BaseAPIView):
    """Apply a state template to a project."""

    @allow_permission([ROLE.ADMIN])
    def post(self, request, slug, project_id):
        project = Project.objects.get(pk=project_id, workspace__slug=slug)
        try:
            template = StateTemplate.objects.get(pk=request.data.get("template"), workspace__slug=slug)
        except (StateTemplate.DoesNotExist, ValueError):
            return Response({"error": message(request, "Template not found.", "Το πρότυπο δεν βρέθηκε.")}, status=status.HTTP_400_BAD_REQUEST)
        result = apply_state_template(project, template, request.user)
        return Response(result, status=status.HTTP_200_OK)

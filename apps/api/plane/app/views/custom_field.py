# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: custom fields. Project admins manage the fields; members fill
# them in on work items.

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Max

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.serializers import CustomFieldSerializer
from plane.db.models import CustomField, Issue, IssueCustomFieldValue, Project
from plane.utils.gam_i18n import message, user_language

from .base import BaseAPIView, BaseViewSet

def duplicate(request):
    return {"error": message(request, "A field with this name already exists in this project.",
                             "Υπάρχει ήδη πεδίο με αυτό το όνομα σε αυτό το έργο.")}


class CustomFieldViewSet(BaseViewSet):
    serializer_class = CustomFieldSerializer
    model = CustomField

    def get_queryset(self):
        return CustomField.objects.filter(
            workspace__slug=self.kwargs.get("slug"), project_id=self.kwargs.get("project_id")
        ).order_by("sequence", "created_at")

    # Guests (e.g. clients) don't see custom fields: they may hold internal data
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def list(self, request, slug, project_id):
        return Response(CustomFieldSerializer(self.get_queryset(), many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    def create(self, request, slug, project_id):
        project = Project.objects.get(pk=project_id, workspace__slug=slug)
        serializer = CustomFieldSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        last = self.get_queryset().aggregate(largest=Max("sequence"))["largest"]
        try:
            # Savepoint: a duplicate name must not break the rest of the request
            with transaction.atomic():
                field = serializer.save(
                    workspace_id=project.workspace_id, project_id=project.id, sequence=(last or 0) + 5000
                )
        except IntegrityError:
            return Response(duplicate(request), status=status.HTTP_400_BAD_REQUEST)
        return Response(CustomFieldSerializer(field).data, status=status.HTTP_201_CREATED)

    @allow_permission([ROLE.ADMIN])
    def partial_update(self, request, slug, project_id, pk):
        serializer = CustomFieldSerializer(instance=self.get_queryset().get(pk=pk), data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            return Response(duplicate(request), status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    def destroy(self, request, slug, project_id, pk):
        self.get_queryset().get(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def clean_value(field, raw, language="el"):
    """The value as stored, or raises ValueError with a message for the user."""
    say = (lambda en, el: en) if language == "en" else (lambda en, el: el)  # noqa: E731
    if raw is None:
        return ""
    if field.field_type == "checkbox":
        return "true" if raw in (True, "true", "True", "1", 1) else ""
    value = str(raw).strip()
    if not value:
        return ""
    if field.field_type == "number":
        try:
            Decimal(value.replace(",", "."))
        except InvalidOperation:
            raise ValueError(f"{field.name}: " + say("enter a number.", "γράψτε έναν αριθμό."))
        return value.replace(",", ".")
    if field.field_type == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{field.name}: " + say("enter a date.", "επιλέξτε ημερομηνία."))
        return value
    if field.field_type == "select" and value not in field.options:
        raise ValueError(f"{field.name}: " + say("choose one of the options.", "επιλέξτε μία από τις επιλογές."))
    return value


class IssueCustomFieldValuesEndpoint(BaseAPIView):
    """GET: {field_id: value} for a work item. PATCH {field_id: value, ...}: set values ("" clears)."""

    def _issue(self, slug, project_id, issue_id):
        return Issue.issue_objects.get(pk=issue_id, project_id=project_id, workspace__slug=slug)

    def _values(self, issue):
        values = IssueCustomFieldValue.objects.filter(
            issue=issue, field__deleted_at__isnull=True
        ).values_list("field_id", "value")
        return Response({str(field_id): value for field_id, value in values}, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug, project_id, issue_id):
        return self._values(self._issue(slug, project_id, issue_id))

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def patch(self, request, slug, project_id, issue_id):
        issue = self._issue(slug, project_id, issue_id)
        fields = {str(f.id): f for f in CustomField.objects.filter(project_id=project_id, id__in=list(request.data.keys()))}
        try:
            language = user_language(request.user)
            cleaned = {
                field_id: clean_value(fields[field_id], raw, language)
                for field_id, raw in request.data.items()
                if field_id in fields
            }
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        for field_id, value in cleaned.items():
            IssueCustomFieldValue.all_objects.update_or_create(
                issue=issue,
                field_id=field_id,
                defaults={"value": value, "deleted_at": None, "updated_by": request.user},
            )
        return self._values(issue)

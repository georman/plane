# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: set or clear how often a work item repeats.

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.db.models import Issue, IssueRecurrence

from .base import BaseAPIView


def serialize_recurrence(recurrence):
    if not recurrence:
        return None
    return {
        "id": str(recurrence.id),
        "issue": str(recurrence.issue_id),
        "frequency": recurrence.frequency,
        "next_run_date": recurrence.next_run_date.isoformat(),
    }


class IssueRecurrenceEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def get(self, request, slug, project_id, issue_id):
        recurrence = IssueRecurrence.objects.filter(
            issue_id=issue_id, issue__project_id=project_id, issue__workspace__slug=slug
        ).first()
        return Response(serialize_recurrence(recurrence), status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def put(self, request, slug, project_id, issue_id):
        frequency = request.data.get("frequency")
        if frequency not in IssueRecurrence.PERIODS:
            return Response(
                {"error": "Frequency must be weekly, monthly or yearly."}, status=status.HTTP_400_BAD_REQUEST
            )
        issue = Issue.objects.get(pk=issue_id, project_id=project_id, workspace__slug=slug)
        recurrence = IssueRecurrence.objects.filter(issue=issue).first()
        if recurrence and recurrence.frequency == frequency:
            return Response(serialize_recurrence(recurrence), status=status.HTTP_200_OK)
        recurrence, _ = IssueRecurrence.objects.update_or_create(
            issue=issue,
            defaults={
                "frequency": frequency,
                "next_run_date": IssueRecurrence.first_run_date(issue, frequency),
            },
        )
        return Response(serialize_recurrence(recurrence), status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def delete(self, request, slug, project_id, issue_id):
        IssueRecurrence.objects.filter(
            issue_id=issue_id, issue__project_id=project_id, issue__workspace__slug=slug
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

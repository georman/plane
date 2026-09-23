# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: email intake. n8n reads info@gam.gr (leaving the mailbox
# untouched) and posts each new email here. Only emails from an existing
# customer's contact address become work items (in Customer Support, state
# New request); everything else is ignored. Each email is turned into a
# work item once, keyed by its Message-ID.

import json
from html import escape

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import Customer, Issue, Project, WorkspaceMember

from .base import BaseAPIView

INTAKE_PROJECT_IDENTIFIER = "SUP"
MAX_BODY_CHARS = 20000


class EmailIntakeEndpoint(BaseAPIView):
    def post(self, request, slug):
        if not WorkspaceMember.objects.filter(
            workspace__slug=slug, member=request.user, role__gte=15, is_active=True
        ).exists():
            return Response({"error": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        sender = (request.data.get("from_email") or "").strip().lower()
        sender_name = (request.data.get("from_name") or "").strip()
        subject = (request.data.get("subject") or "").strip()
        body = (request.data.get("text") or "").strip()[:MAX_BODY_CHARS]
        message_id = (request.data.get("message_id") or "").strip()[:250]
        if not sender or not message_id:
            return Response({"error": "from_email and message_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.filter(
            workspace__slug=slug, contact_email__iexact=sender, is_active=True
        ).first()
        if not customer:
            return Response({"status": "ignored", "reason": "sender is not a customer"}, status=status.HTTP_200_OK)

        existing = Issue.all_objects.filter(
            workspace__slug=slug, external_source="email", external_id=message_id
        ).first()
        if existing:
            return Response(
                {"status": "duplicate", "issue_id": str(existing.id), "project_id": str(existing.project_id)},
                status=status.HTTP_200_OK,
            )

        project = Project.objects.get(workspace__slug=slug, identifier=INTAKE_PROJECT_IDENTIFIER)
        body_html = escape(body).replace("\n", "<br>") if body else "<em>(χωρίς κείμενο)</em>"
        who = escape(f"{sender_name} <{sender}>" if sender_name else sender)
        description = (
            f"<p>{body_html}</p><p><strong>Email από:</strong> {who} – Πελάτης: {escape(customer.name)}</p>"
        )
        issue = Issue(
            name=(subject or f"Email από {customer.name}")[:255],
            description_html=description,
            project=project,
            workspace_id=project.workspace_id,
            created_by=request.user,
            external_source="email",
            external_id=message_id,
        )
        issue.save()
        issue_activity.delay(
            type="issue.activity.created",
            requested_data=json.dumps({"name": issue.name}),
            actor_id=str(request.user.id),
            issue_id=str(issue.id),
            project_id=str(project.id),
            current_instance=None,
            epoch=int(timezone.now().timestamp()),
        )
        return Response(
            {"status": "created", "issue_id": str(issue.id), "project_id": str(project.id),
             "customer": customer.name, "sequence": f"{project.identifier}-{issue.sequence_id}"},
            status=status.HTTP_201_CREATED,
        )

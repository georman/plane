# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: lets a workspace admin log in as a member/guest without
# their password, to see exactly what they see and fix issues directly.
# Restricted to workspace admins, cannot target other admins, every
# session is audit-logged (ImpersonationLog), and a banner-visible
# session marker (impersonator_id) lets the admin return to their own
# account with one click.

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from plane.app.permissions import ROLE, allow_permission
from plane.authentication.session import BaseSessionAuthentication
from plane.authentication.utils.login import user_login
from plane.db.models import ImpersonationLog, User, Workspace, WorkspaceMember
from plane.utils.ip_address import get_client_ip


class ImpersonateMemberEndpoint(APIView):
    # Plain APIView falls back to the global DRF default
    # (rest_framework.authentication.SessionAuthentication), which enforces
    # CSRF. Every other mutation in this codebase uses BaseSessionAuthentication
    # instead (via BaseAPIView), which explicitly disables CSRF enforcement -
    # the app relies on SameSite cookies for CSRF defense instead. Without
    # this, the frontend's plain axios POST (no CSRF token attached, matching
    # every other mutation's service call) gets silently rejected: DRF treats
    # the CSRF failure as an authentication failure, request.user becomes
    # anonymous, and allow_permission's fallback returns a misleading 403.
    authentication_classes = [BaseSessionAuthentication]

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def post(self, request, slug, member_id):
        if request.session.get("impersonator_id"):
            return Response(
                {"error": "You are already impersonating a user. Return to your own account first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(member_id) == str(request.user.id):
            return Response(
                {"error": "You cannot impersonate yourself."}, status=status.HTTP_400_BAD_REQUEST
            )

        workspace = Workspace.objects.get(slug=slug)

        target_membership = (
            WorkspaceMember.objects.filter(workspace=workspace, member_id=member_id, is_active=True)
            .select_related("member")
            .first()
        )
        if not target_membership:
            return Response(
                {"error": "Member not found in this workspace."}, status=status.HTTP_404_NOT_FOUND
            )

        if target_membership.role >= ROLE.ADMIN.value:
            return Response(
                {"error": "You cannot impersonate another admin."}, status=status.HTTP_403_FORBIDDEN
            )

        target_user = target_membership.member
        impersonator_id = str(request.user.id)
        impersonator_email = request.user.email

        ImpersonationLog.objects.create(
            workspace=workspace,
            impersonator=request.user,
            target_user=target_user,
            ip_address=get_client_ip(request=request),
        )

        # Switches request.user/session to target_user. Django's login()
        # cycles the session key (session-fixation protection), so the
        # impersonator marker below is set AFTER this call, not before.
        user_login(request=request, user=target_user, is_app=True)

        request.session["impersonator_id"] = impersonator_id
        request.session["impersonator_email"] = impersonator_email
        request.session.save()

        return Response({"message": "Impersonation started."}, status=status.HTTP_200_OK)


class StopImpersonationEndpoint(APIView):
    authentication_classes = [BaseSessionAuthentication]

    def post(self, request):
        impersonator_id = request.session.get("impersonator_id")
        if not impersonator_id:
            return Response(
                {"error": "Not currently impersonating."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            impersonator = User.objects.get(id=impersonator_id)
        except User.DoesNotExist:
            request.session.flush()
            return Response(
                {"error": "Original account no longer exists."}, status=status.HTTP_400_BAD_REQUEST
            )

        ImpersonationLog.objects.filter(
            impersonator=impersonator, target_user=request.user, ended_at__isnull=True
        ).order_by("-started_at").update(ended_at=timezone.now())

        user_login(request=request, user=impersonator, is_app=True)

        return Response({"message": "Returned to your account."}, status=status.HTTP_200_OK)


class ImpersonationStatusEndpoint(APIView):
    def get(self, request):
        impersonator_email = request.session.get("impersonator_email")
        if not impersonator_email:
            return Response({"is_impersonating": False})
        return Response(
            {
                "is_impersonating": True,
                "impersonator_email": impersonator_email,
                "target_user_email": request.user.email,
                "target_user_display_name": request.user.display_name,
            }
        )

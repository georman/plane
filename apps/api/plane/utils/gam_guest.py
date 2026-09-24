# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: clients (project guests) only see work once it reaches
# Client approval or later; earlier internal stages (New request, Quotation,
# Approved, In progress, Internal review) stay staff-only. Every issue list a
# guest can reach goes through hide_internal_from_guests().

from django.db.models import Q

from plane.db.models import ProjectMember

GUEST_ROLE = 5

GAM_GUEST_VISIBLE_STATE_NAMES = [
    "Έγκριση πελάτη",
    "Διορθώσεις",
    "Έτοιμο για παράδοση",
    "Παραδόθηκε",
    "Τιμολογήθηκε",
    # English names, for projects created before the Greek rename
    "Client approval",
    "Corrections",
    "Ready for delivery",
    "Delivered",
    "Invoiced",
]


def hide_internal_from_guests(queryset, user, prefix=""):
    """Drop issues in projects where `user` is a guest unless they are in a client-visible state.

    `prefix` is the path to the issue when the queryset is of another model (e.g. "issue__").
    """
    guest_project_ids = list(
        ProjectMember.objects.filter(member=user, role=GUEST_ROLE, is_active=True).values_list("project_id", flat=True)
    )
    if not guest_project_ids:
        return queryset
    return queryset.exclude(
        Q(**{f"{prefix}project_id__in": guest_project_ids})
        & ~Q(**{f"{prefix}state__name__in": GAM_GUEST_VISIBLE_STATE_NAMES})
    )

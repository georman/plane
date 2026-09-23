# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: helpers for client approval by email.

from django.core import signing

from plane.db.models import State, StateGroup

# Entering one of these states sends the client an approval email
APPROVAL_STATE_NAMES = {"client approval", "for approval"}
# "Request changes" sends the item here; "Approve" skips over it
CORRECTIONS_STATE_NAME = "corrections"

# Same order the Plane UI shows states in: by group, then by sequence
GROUP_ORDER = [
    StateGroup.BACKLOG.value,
    StateGroup.UNSTARTED.value,
    StateGroup.STARTED.value,
    StateGroup.COMPLETED.value,
    StateGroup.CANCELLED.value,
]

TOKEN_SALT = "gam-client-approval"
TOKEN_MAX_AGE = 60 * 60 * 24 * 60  # links work for 60 days


def is_approval_state(state):
    return bool(state) and state.name.strip().lower() in APPROVAL_STATE_NAMES


def ordered_states(project_id):
    states = [s for s in State.objects.filter(project_id=project_id) if s.group in GROUP_ORDER]
    return sorted(states, key=lambda s: (GROUP_ORDER.index(s.group), s.sequence))


def next_state_after(state):
    """The next state in the project's own order, skipping Corrections (that's the changes path)."""
    states = ordered_states(state.project_id)
    ids = [s.id for s in states]
    if state.id not in ids:
        return None
    for candidate in states[ids.index(state.id) + 1 :]:
        if candidate.name.strip().lower() != CORRECTIONS_STATE_NAME:
            return candidate
    return None


def corrections_state(project_id):
    for state in State.objects.filter(project_id=project_id):
        if state.name.strip().lower() == CORRECTIONS_STATE_NAME:
            return state
    return None


def make_token(approval):
    """Signed link token. It carries the request's token_version, so bumping the version kills older links."""
    return signing.dumps(f"{approval.id}:{approval.token_version}", salt=TOKEN_SALT)


def read_token(token):
    """(approval request id, token version), or (None, None) if the link is invalid or expired."""
    try:
        value = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None, None
    approval_id, _, version = str(value).partition(":")
    return approval_id, int(version) if version.isdigit() else 1


def batch_posts(issue):
    """Sub-items that carry files are the proposals the client reviews one by one (e.g. IG posts).
    Sub-items without files are internal checklist steps and are left out."""
    from plane.db.models import FileAsset, Issue

    children = Issue.issue_objects.filter(parent=issue).exclude(state__group="cancelled").order_by("sequence_id")
    with_files = FileAsset.objects.filter(
        issue_id__in=children.values("id"),
        entity_type=FileAsset.EntityTypeContext.ISSUE_ATTACHMENT,
        is_uploaded=True,
        deleted_at__isnull=True,
    ).values_list("issue_id", flat=True)
    ids = set(with_files)
    return [child for child in children if child.id in ids]

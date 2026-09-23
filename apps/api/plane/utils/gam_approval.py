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


def make_token(approval_request_id):
    return signing.dumps(str(approval_request_id), salt=TOKEN_SALT)


def read_token(token):
    """Returns the approval request id, or None if the link is invalid or expired."""
    try:
        return signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None

# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: apply a state template to a project.

from django.db import transaction

from plane.db.models import Issue, State


@transaction.atomic
def apply_state_template(project, template, user):
    """Make the project's states match the template.

    Template states are added or updated (colour, group, order) by name.
    Other states are removed only if no work item uses them; the ones still
    in use are kept, so no work item ever loses its state.
    """
    items = list(template.items.all().order_by("sequence", "created_at"))
    if not items:
        return {"added": 0, "updated": 0, "removed": 0, "kept": []}

    existing = {state.name: state for state in State.objects.filter(project=project)}
    template_states = []
    added = updated = 0
    for item in items:
        state = existing.pop(item.name, None)
        if state is None:
            state = State.objects.create(
                name=item.name,
                color=item.color,
                group=item.group,
                project=project,
                workspace=project.workspace,
                created_by=user,
            )
            added += 1
        else:
            updated += 1
        # save() renumbers new states, so the template order is set afterwards
        State.objects.filter(pk=state.pk).update(color=item.color, group=item.group, sequence=item.sequence)
        template_states.append((item, state))

    default_item_state = next((state for item, state in template_states if item.default), None)
    if default_item_state:
        State.objects.filter(project=project).update(default=False)
        State.objects.filter(pk=default_item_state.pk).update(default=True)

    removed, kept = 0, []
    for state in existing.values():
        if Issue.all_objects.filter(state=state, deleted_at__isnull=True).exists():
            kept.append(state.name)
            continue
        if state.default and not default_item_state:
            kept.append(state.name)
            continue
        state.delete()
        removed += 1
    return {"added": added, "updated": updated, "removed": removed, "kept": kept}

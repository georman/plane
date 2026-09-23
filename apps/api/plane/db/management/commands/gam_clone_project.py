# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: "project template" script. Plane CE has no native project
# duplication, and every new dedicated client project (ClientA,
# ClientB, ClientC, ...) had its 11-state pipeline + Recurring
# label built by hand. This clones an existing project's states, labels,
# and feature flags into a brand new project so onboarding a new client
# is one command instead of ~15 manual steps.

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from plane.db.models import Label, Project, ProjectMember, State, User, Workspace


class Command(BaseCommand):
    help = "GAM: clone an existing project's pipeline states, labels, and feature flags into a new project"

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source_name", required=True, help="Name of the project to clone from")
        parser.add_argument("--name", required=True, help="Name for the new project")
        parser.add_argument("--identifier", required=True, help="Short identifier for the new project, e.g. ACME")
        parser.add_argument("--created-by", dest="created_by_email", required=True, help="Email of the admin who will own this project")
        parser.add_argument("--workspace", default="gam", help="Workspace slug (default: gam)")

    def handle(self, *args, **options):
        workspace_slug = options["workspace"]
        source_name = options["source_name"]
        name = options["name"]
        identifier = options["identifier"].upper()
        created_by_email = options["created_by_email"]

        try:
            workspace = Workspace.objects.get(slug=workspace_slug)
        except Workspace.DoesNotExist:
            raise CommandError(f"Workspace '{workspace_slug}' not found")

        try:
            source_project = Project.objects.get(workspace=workspace, name=source_name)
        except Project.DoesNotExist:
            raise CommandError(f"Source project '{source_name}' not found in workspace '{workspace_slug}'")
        except Project.MultipleObjectsReturned:
            raise CommandError(f"Multiple projects named '{source_name}' found - be more specific")

        try:
            created_by = User.objects.get(email=created_by_email)
        except User.DoesNotExist:
            raise CommandError(f"User '{created_by_email}' not found")

        if Project.objects.filter(workspace=workspace, name=name).exists():
            raise CommandError(f"A project named '{name}' already exists")
        if Project.objects.filter(workspace=workspace, identifier=identifier).exists():
            raise CommandError(f"Identifier '{identifier}' is already used by another project")

        with transaction.atomic():
            new_project = Project.objects.create(
                workspace=workspace,
                name=name,
                identifier=identifier,
                network=source_project.network,
                module_view=source_project.module_view,
                cycle_view=source_project.cycle_view,
                issue_views_view=source_project.issue_views_view,
                page_view=source_project.page_view,
                intake_view=source_project.intake_view,
                is_time_tracking_enabled=source_project.is_time_tracking_enabled,
                is_issue_type_enabled=source_project.is_issue_type_enabled,
                guest_view_all_features=source_project.guest_view_all_features,
                created_by=created_by,
                updated_by=created_by,
            )

            # Plane auto-creates 5 generic default states on project creation -
            # drop them, we're replacing with an exact copy of the source
            # project's pipeline.
            State.objects.filter(project=new_project).delete()

            for state in State.objects.filter(project=source_project, workspace=workspace):
                State.objects.create(
                    workspace=workspace,
                    project=new_project,
                    name=state.name,
                    color=state.color,
                    group=state.group,
                    sequence=state.sequence,
                    default=state.default,
                    created_by=created_by,
                    updated_by=created_by,
                )

            for label in Label.objects.filter(project=source_project, workspace=workspace):
                Label.objects.create(
                    workspace=workspace,
                    project=new_project,
                    name=label.name,
                    color=label.color,
                    created_by=created_by,
                    updated_by=created_by,
                )

            # workspace membership alone doesn't grant project visibility -
            # the creator needs an explicit ProjectMember row too (see
            # plane_stack.md memory's operational-gotcha note).
            ProjectMember.objects.create(
                project=new_project,
                workspace=workspace,
                member=created_by,
                role=20,
                created_by=created_by,
                updated_by=created_by,
            )

        state_count = State.objects.filter(project=new_project).count()
        label_count = Label.objects.filter(project=new_project).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created '{new_project.name}' ({new_project.identifier}), cloned from "
                f"'{source_project.name}': {state_count} states, {label_count} labels. "
                f"Remember: guest invites and project-member additions for anyone else "
                f"who needs access still need to be done separately."
            )
        )

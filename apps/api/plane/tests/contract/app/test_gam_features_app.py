"""GAM additions: contract tests for state templates, custom fields, the client
portal, legal pages and proof markup helpers."""

import io
import json

import pytest
from django.test import Client
from PIL import Image
from rest_framework import status

from plane.db.models import (
    CustomField,
    Customer,
    DraftIssue,
    Issue,
    IssueCustomerService,
    Project,
    ProjectMember,
    Service,
    State,
    StateTemplate,
    StateTemplateItem,
)
from plane.utils.gam_markup import draw_pins, parse_marks
from plane.utils.gam_state_templates import apply_state_template


@pytest.fixture(autouse=True)
def no_task_queue(mocker):
    # Soft deletes and activity logs queue Celery tasks; not needed here
    mocker.patch("celery.app.task.Task.delay")


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(name="GAM Test", identifier="GT", workspace=workspace, created_by=create_user)
    ProjectMember.objects.create(project=project, member=create_user, workspace=workspace, role=20)
    return project


@pytest.fixture
def template(db, workspace):
    template = StateTemplate.objects.create(workspace=workspace, name="Pipeline", is_default=True)
    for i, (name, group) in enumerate([("New", "backlog"), ("Doing", "started"), ("Done", "completed")]):
        StateTemplateItem.objects.create(template=template, name=name, group=group, sequence=(i + 1) * 1000, default=i == 0)
    return template


@pytest.mark.contract
class TestStateTemplates:
    @pytest.mark.django_db
    def test_new_project_starts_from_default_template(self, session_client, workspace, template):
        response = session_client.post(
            f"/api/workspaces/{workspace.slug}/projects/",
            {"name": "project.gam.gr (web) & co", "identifier": "PG", "network": 2},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        names = list(State.objects.filter(project_id=response.data["id"]).order_by("sequence").values_list("name", flat=True))
        assert names == ["New", "Doing", "Done"]

    @pytest.mark.django_db
    def test_apply_keeps_states_in_use(self, workspace, project, template, create_user):
        used = State.objects.create(name="Used", group="started", project=project, workspace=workspace)
        draft_only = State.objects.create(name="Draft only", group="started", project=project, workspace=workspace)
        State.objects.create(name="Unused", group="started", project=project, workspace=workspace)
        Issue.objects.create(name="x", project=project, workspace=workspace, state=used)
        DraftIssue.objects.create(name="d", project=project, workspace=workspace, state=draft_only)

        result = apply_state_template(project, template, create_user)

        assert result["added"] == 3 and result["removed"] == 1
        assert set(result["kept"]) == {"Used", "Draft only"}
        assert State.objects.get(project=project, default=True).name == "New"


@pytest.mark.contract
class TestCustomFields:
    @pytest.mark.django_db
    def test_values_are_validated_and_saved(self, session_client, workspace, project):
        base = f"/api/workspaces/{workspace.slug}/projects/{project.id}"
        number = session_client.post(f"{base}/custom-fields/", {"name": "Qty", "field_type": "number"}, format="json")
        select = session_client.post(
            f"{base}/custom-fields/", {"name": "Paper", "field_type": "select", "options": ["A", "B", "A"]}, format="json"
        )
        assert number.status_code == select.status_code == status.HTTP_201_CREATED
        assert select.data["options"] == ["A", "B"]
        qty, paper = str(number.data["id"]), str(select.data["id"])
        issue = Issue.objects.create(name="job", project=project, workspace=workspace)
        values_url = f"{base}/issues/{issue.id}/custom-field-values/"

        bad = session_client.patch(values_url, {qty: "abc"}, format="json")
        assert bad.status_code == status.HTTP_400_BAD_REQUEST
        ok = session_client.patch(values_url, {qty: "12,5", paper: "B"}, format="json")
        assert ok.status_code == status.HTTP_200_OK
        assert ok.data == {qty: "12.5", paper: "B"}

    @pytest.mark.django_db
    def test_deleted_field_name_can_be_reused(self, session_client, workspace, project):
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/custom-fields/"
        first = session_client.post(url, {"name": "Qty", "field_type": "number"}, format="json")
        assert session_client.post(url, {"name": "Qty", "field_type": "text"}, format="json").status_code == 400
        session_client.delete(f"{url}{first.data['id']}/")
        assert session_client.post(url, {"name": "Qty", "field_type": "text"}, format="json").status_code == 201
        assert CustomField.objects.filter(project=project, name="Qty").count() == 1


@pytest.mark.contract
class TestClientPortal:
    @pytest.mark.django_db
    def test_portal_link_shows_jobs_and_renew_revokes_it(self, session_client, workspace, project):
        customer = Customer.objects.create(workspace=workspace, name="Client", language="en")
        service = Service.objects.create(workspace=workspace, name="Logo")
        issue = Issue.objects.create(name="Logo job", project=project, workspace=workspace)
        IssueCustomerService.objects.create(issue=issue, customer=customer, service=service)
        link_url = f"/api/workspaces/{workspace.slug}/customers/{customer.id}/portal-link/"

        portal = session_client.get(link_url).data["url"].split("/api/gam/", 1)[1]
        page = Client().get(f"/api/gam/{portal}")
        assert page.status_code == 200 and "Logo job" in page.content.decode()

        session_client.post(link_url, {"action": "renew"}, format="json")
        assert "Logo job" not in Client().get(f"/api/gam/{portal}").content.decode()


@pytest.mark.contract
class TestLegalPages:
    @pytest.mark.django_db
    def test_pages_render_in_both_languages(self):
        client = Client()
        assert "Όροι Χρήσης" in client.get("/api/gam/legal/terms/?lang=el").content.decode()
        assert "Privacy Policy" in client.get("/api/gam/legal/privacy/?lang=en").content.decode()
        assert client.get("/api/gam/legal/other/").status_code == 404


@pytest.mark.unit
class TestProofMarkup:
    def test_marks_are_limited_to_known_images_and_clamped(self):
        raw = json.dumps([
            {"asset": "a", "x": 10, "y": 150, "text": "x" * 900},
            {"asset": "unknown", "x": 1, "y": 1},
            {"asset": "a", "x": "bad", "y": 1},
        ])
        marks = parse_marks(raw, {"a": object()})
        assert [(m["x"], m["y"], len(m["text"])) for m in marks] == [(10.0, 100.0, 500)]
        assert parse_marks("not json", {"a": object()}) == []

    def test_pins_are_drawn_and_large_images_shrunk(self):
        buffer = io.BytesIO()
        Image.new("RGB", (5000, 4000), "white").save(buffer, "PNG")
        out = Image.open(io.BytesIO(draw_pins(buffer.getvalue(), [{"x": 50, "y": 50, "text": ""}])))
        assert max(out.size) == 3000
        assert out.getpixel((1500 - 25, 1200)) == (220, 38, 38)

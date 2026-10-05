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
class TestCustomerProjects:
    @pytest.mark.django_db
    def test_projects_link_to_one_customer_in_the_same_workspace(self, session_client, workspace, project, create_user):
        first = Customer.objects.create(workspace=workspace, name="First")
        second = Customer.objects.create(workspace=workspace, name="Second")
        url = f"/api/workspaces/{workspace.slug}/customers/"

        response = session_client.patch(f"{url}{first.id}/", {"project_ids": [str(project.id)]}, format="json")
        assert response.status_code == 200 and response.data["project_ids"] == [project.id]
        project.refresh_from_db()
        assert project.customer_id == first.id

        # linking it to another customer moves it over
        session_client.patch(f"{url}{second.id}/", {"project_ids": [str(project.id)]}, format="json")
        project.refresh_from_db()
        assert project.customer_id == second.id
        listed = {c["name"]: c["project_ids"] for c in session_client.get(url).data}
        assert listed == {"First": [], "Second": [project.id]}

        session_client.patch(f"{url}{second.id}/", {"project_ids": []}, format="json")
        project.refresh_from_db()
        assert project.customer_id is None

        # a project from another workspace is refused
        other_workspace = type(workspace).objects.create(name="Other", slug="other-ws", owner=create_user)
        other = Project.objects.create(name="Other", identifier="OT", workspace=other_workspace)
        response = session_client.patch(f"{url}{first.id}/", {"project_ids": [str(other.id)]}, format="json")
        assert response.status_code == 400
        other.refresh_from_db()
        assert other.customer_id is None


@pytest.mark.contract
class TestServiceLabels:
    @pytest.mark.django_db
    def test_service_label_sets_and_clears_billing_link(self, session_client, workspace, project, create_user):
        from plane.db.models import CustomerServiceRate, IssueLabel, Label
        from plane.utils.gam_service_labels import sync_issue_service_from_labels

        customer = Customer.objects.create(workspace=workspace, name="Client")
        adaptation = Service.objects.create(workspace=workspace, name="Adaptation")
        url = f"/api/workspaces/{workspace.slug}/customers/{customer.id}/"
        session_client.patch(url, {"project_ids": [str(project.id)]}, format="json")
        # adding a price creates the label in the customer's projects
        session_client.post(f"{url}rates/", {"service": str(adaptation.id), "price": "20"}, format="json")
        label = Label.objects.get(project=project, name="Adaptation")
        other_label = Label.objects.create(project=project, workspace=workspace, name="Urgent")

        issue = Issue.objects.create(name="Box", project=project, workspace=workspace)
        IssueLabel.objects.create(issue=issue, label=other_label, project=project, workspace=workspace)
        sync_issue_service_from_labels(issue.id, create_user.id)
        assert not IssueCustomerService.objects.filter(issue=issue).exists()

        IssueLabel.objects.create(issue=issue, label=label, project=project, workspace=workspace)
        sync_issue_service_from_labels(issue.id, create_user.id)
        link = IssueCustomerService.objects.get(issue=issue)
        assert (link.customer_id, link.service_id) == (customer.id, adaptation.id)

        IssueLabel.objects.filter(issue=issue, label=label).delete()
        sync_issue_service_from_labels(issue.id, create_user.id)
        assert not IssueCustomerService.all_objects.filter(issue=issue).exists()

        # and it can be set again afterwards
        IssueLabel.all_objects.filter(issue=issue, label=label).delete()
        IssueLabel.objects.create(issue=issue, label=label, project=project, workspace=workspace)
        sync_issue_service_from_labels(issue.id, create_user.id)
        assert IssueCustomerService.objects.filter(issue=issue, service=adaptation).exists()


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

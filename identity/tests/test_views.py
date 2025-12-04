import pytest
from django.contrib.auth.models import Group, User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from audit_management.models import Audit
from core.models import Organization
from identity.adapters.models import (
    AuditorCompetenceEvaluation,
    AuditorQualification,
    AuditorTrainingRecord,
    ConflictOfInterest,
)


@pytest.mark.django_db
class TestDashboardViews:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def cb_admin_group(self):
        group, _ = Group.objects.get_or_create(name="cb_admin")
        return group

    @pytest.fixture
    def auditor_group(self):
        group, _ = Group.objects.get_or_create(name="lead_auditor")
        return group

    @pytest.fixture
    def client_group(self):
        group, _ = Group.objects.get_or_create(name="client_admin")
        return group

    @pytest.fixture
    def cb_admin_user(self, cb_admin_group):
        user = User.objects.create_user(username="cb_admin", password="password")
        user.groups.add(cb_admin_group)
        return user

    @pytest.fixture
    def auditor_user(self, auditor_group):
        user = User.objects.create_user(username="auditor", password="password")
        user.groups.add(auditor_group)
        return user

    @pytest.fixture
    def client_user(self, client_group):
        user = User.objects.create_user(username="client", password="password")
        user.groups.add(client_group)
        return user

    def test_dashboard_redirect_cb_admin(self, client, cb_admin_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:dashboard"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard_cb")

    def test_dashboard_redirect_auditor(self, client, auditor_user):
        client.force_login(auditor_user)
        response = client.get(reverse("identity:dashboard"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard_auditor")

    def test_dashboard_redirect_client(self, client, client_user):
        client.force_login(client_user)
        response = client.get(reverse("identity:dashboard"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard_client")

    def test_dashboard_redirect_no_group(self, client):
        user = User.objects.create_user(username="nogroup", password="password")
        client.force_login(user)
        response = client.get(reverse("identity:dashboard"))
        assert response.status_code == 200
        assert "identity/dashboard.html" in [t.name for t in response.templates]

    def test_dashboard_cb_access(self, client, cb_admin_user, auditor_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:dashboard_cb"))
        assert response.status_code == 200

        client.force_login(auditor_user)
        response = client.get(reverse("identity:dashboard_cb"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard")

    def test_dashboard_auditor_access(self, client, auditor_user, cb_admin_user):
        client.force_login(auditor_user)
        response = client.get(reverse("identity:dashboard_auditor"))
        assert response.status_code == 200

        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:dashboard_auditor"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard")

    def test_dashboard_client_access(self, client, client_user, cb_admin_user):
        client.force_login(client_user)
        response = client.get(reverse("identity:dashboard_client"))
        assert response.status_code == 200

        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:dashboard_client"))
        assert response.status_code == 302
        assert response.url == reverse("identity:dashboard")

    def test_dashboard_client_context(self, client, client_user):
        org = Organization.objects.create(name="Test Org", total_employee_count=10)
        client_user.profile.organization = org
        client_user.profile.save()

        Audit.objects.create(
            organization=org,
            total_audit_date_from=timezone.now().date(),
            total_audit_date_to=timezone.now().date(),
            created_by=client_user,
            lead_auditor=client_user,  # Just using client_user as lead auditor for this test
        )

        client.force_login(client_user)
        response = client.get(reverse("identity:dashboard_client"))
        assert response.status_code == 200
        assert response.context["organization"] == org
        assert response.context["audits"].count() == 1


@pytest.mark.django_db
class TestAuditorManagementViews:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def cb_admin_group(self):
        group, _ = Group.objects.get_or_create(name="cb_admin")
        return group

    @pytest.fixture
    def cb_admin_user(self, cb_admin_group):
        user = User.objects.create_user(username="cb_admin", password="password")
        user.groups.add(cb_admin_group)
        return user

    @pytest.fixture
    def auditor_user(self):
        user = User.objects.create_user(username="auditor", password="password")
        group, _ = Group.objects.get_or_create(name="lead_auditor")
        user.groups.add(group)
        return user

    def test_qualification_list(self, client, cb_admin_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:qualification_list"))
        assert response.status_code == 200

    def test_qualification_create(self, client, cb_admin_user, auditor_user):
        client.force_login(cb_admin_user)
        data = {
            "auditor": auditor_user.id,
            "qualification_type": "lead_auditor_cert",
            "issuing_body": "IRCA",
            "certificate_number": "12345",
            "issue_date": timezone.now().date(),
            "status": "active",
        }
        response = client.post(reverse("identity:qualification_create"), data)
        assert response.status_code == 302
        assert AuditorQualification.objects.count() == 1

    def test_training_list(self, client, cb_admin_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:training_list"))
        assert response.status_code == 200

    def test_training_create(self, client, cb_admin_user, auditor_user):
        client.force_login(cb_admin_user)
        data = {
            "auditor": auditor_user.id,
            "course_title": "ISO 9001 Lead Auditor",
            "training_provider": "BSI",
            "course_date": timezone.now().date(),
            "cpd_points": 10.0,
        }
        response = client.post(reverse("identity:training_create"), data)
        assert response.status_code == 302
        assert AuditorTrainingRecord.objects.count() == 1

    def test_competence_list(self, client, cb_admin_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:competence_list"))
        assert response.status_code == 200

    def test_competence_create(self, client, cb_admin_user, auditor_user):
        client.force_login(cb_admin_user)
        data = {
            "auditor": auditor_user.id,
            "evaluation_date": timezone.now().date(),
            "evaluator": cb_admin_user.id,
            "technical_knowledge_score": 4,
            "audit_skills_score": 4,
            "communication_skills_score": 4,
            "report_writing_score": 4,
            "overall_assessment": "meets",
        }
        response = client.post(reverse("identity:competence_create"), data)
        assert response.status_code == 302
        assert AuditorCompetenceEvaluation.objects.count() == 1

    def test_coi_list(self, client, cb_admin_user):
        client.force_login(cb_admin_user)
        response = client.get(reverse("identity:coi_list"))
        assert response.status_code == 200

    def test_coi_create(self, client, cb_admin_user, auditor_user):
        org = Organization.objects.create(name="Conflict Org", total_employee_count=10)
        client.force_login(cb_admin_user)
        data = {
            "auditor": auditor_user.id,
            "organization": org.id,
            "relationship_type": "former_employee",
            "description": "Worked there 2 years ago",
            "impartiality_risk": "low",
        }
        response = client.post(reverse("identity:coi_create"), data)
        assert response.status_code == 302
        assert ConflictOfInterest.objects.count() == 1

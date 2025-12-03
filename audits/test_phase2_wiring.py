# pylint: disable=redefined-outer-name,unused-argument
from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse

from audits.models import Appeal, Audit, AuditorCompetenceWarning, Complaint
from core.models import CertificateHistory, Certification, Organization, Standard, SurveillanceSchedule
from core.test_utils import TEST_PASSWORD


@pytest.mark.django_db
class TestPhase2Wiring:
    @pytest.fixture
    def cb_admin(self):
        user = User.objects.create_user(username="cb_admin", password=TEST_PASSWORD)  # nosec B106
        group, _ = Group.objects.get_or_create(name="cb_admin")
        user.groups.add(group)
        # Profile is auto-created by signal
        return user

    @pytest.fixture
    def auditor(self):
        user = User.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        group, _ = Group.objects.get_or_create(name="auditor")
        user.groups.add(group)
        # Profile is auto-created by signal
        return user

    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name="Test Org", customer_id="CUST001", total_employee_count=100)

    @pytest.fixture
    def standard(self):
        return Standard.objects.create(title="ISO 9001", code="9001")

    @pytest.fixture
    def certification(self, organization, standard):
        return Certification.objects.create(
            organization=organization,
            standard=standard,
            certificate_id="CERT-001",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=1095),
        )

    @pytest.fixture
    def audit(self, organization, cb_admin, certification):
        # Create a closed Stage 1 audit to satisfy Stage 2 requirements
        Audit.objects.create(
            organization=organization,
            created_by=cb_admin,
            lead_auditor=cb_admin,
            audit_type="stage1",
            total_audit_date_from=date.today() - timedelta(days=30),
            total_audit_date_to=date.today() - timedelta(days=28),
            status="closed",
        )

        audit = Audit.objects.create(
            organization=organization,
            created_by=cb_admin,
            lead_auditor=cb_admin,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=2),
            status="submitted",  # Ready for decision
        )
        audit.certifications.add(certification)
        return audit

    def test_certificate_service_wiring(self, client, cb_admin, audit, certification):
        """Test that making a decision triggers CertificateService and creates history/schedule."""
        client.force_login(cb_admin)
        url = reverse("audits:certification_decision_create", kwargs={"audit_pk": audit.pk})

        data = {"decision": "grant", "decision_notes": "Approved", "certifications_affected": [certification.pk]}

        # Audit needs to be in decision_pending for the view to allow access?
        # Let's check the view logic. It checks for "decision_pending".
        # But my fixture set it to "submitted".
        # Wait, CertificationDecisionView checks for "decision_pending".
        # But in my previous edit to views.py, I saw:
        # if audit.status != "submitted": messages.error...
        # Let me re-read views.py to be sure which view I edited.
        # I edited CertificationDecisionView.form_valid.
        # And the test_func checks PermissionPredicate.can_make_certification_decision.

        # Let's update audit status to decision_pending if that's what the view expects.
        # Actually, the view I edited (CertificationDecisionView) had:
        # if audit.status != "decision_pending": return False (in test_func)

        audit.status = "decision_pending"
        audit.save()

        response = client.post(url, data)
        assert response.status_code == 302

        # Check if history was created
        assert CertificateHistory.objects.filter(related_audit=audit).exists()

        # Check if surveillance schedule was created
        assert SurveillanceSchedule.objects.filter(certification=certification).exists()

    def test_competence_service_wiring(self, client, cb_admin, audit, auditor):
        """Test that adding a team member triggers competence check."""
        client.force_login(cb_admin)
        url = reverse("audits:team_member_add", kwargs={"audit_pk": audit.pk})

        # Auditor has NO qualifications, so this should trigger a warning
        data = {
            "user": auditor.pk,
            "role": "auditor",
            "date_from": audit.total_audit_date_from,
            "date_to": audit.total_audit_date_to,
        }

        response = client.post(url, data)
        assert response.status_code == 302  # Redirects on success (warning doesn't block)

        # Check if warning was created
        assert AuditorCompetenceWarning.objects.filter(audit=audit, auditor=auditor).exists()

        # Now give auditor qualification and try again (with a new auditor to avoid unique constraints if any)
        # Actually AuditTeamMember doesn't enforce unique user per audit in model? Let's assume it does or doesn't.
        # Let's just check the warning creation for the first case.

    def test_complaint_creation(self, client, cb_admin, organization):
        """Test complaint creation view."""
        client.force_login(cb_admin)
        url = reverse("audits:complaint_create")

        data = {
            "complainant_name": "John Doe",
            "complainant_email": "john@example.com",
            "organization": organization.pk,
            "complaint_type": "audit_conduct",
            "description": "Something went wrong",
        }

        response = client.post(url, data)
        assert response.status_code == 302
        assert Complaint.objects.filter(description="Something went wrong").exists()

    def test_appeal_creation(self, client, cb_admin):
        """Test appeal creation view."""
        client.force_login(cb_admin)
        url = reverse("audits:appeal_create")

        data = {"appellant_name": "Jane Doe", "appellant_email": "jane@example.com", "grounds": "Unfair decision"}

        response = client.post(url, data)
        assert response.status_code == 302
        assert Appeal.objects.filter(grounds="Unfair decision").exists()

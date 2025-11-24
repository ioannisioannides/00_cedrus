"""
Test Suite for Sprint 9: Findings Management

Tests cover:
- US-012: Create Nonconformity
- US-013: Create Observation
- US-014: Create Opportunity for Improvement
- US-015: Client Response to Nonconformity
- US-016: Auditor Verification of Response
- Finding CRUD operations
- Permission checks (auditor, client roles)
- Form validation
- Status transitions with findings validation
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from audits.finding_forms import (
    NonconformityForm,
    NonconformityResponseForm,
    NonconformityVerificationForm,
    ObservationForm,
    OpportunityForImprovementForm,
)
from accounts.models import Profile
from audits.models import Audit, Nonconformity, Observation, OpportunityForImprovement
from audits.workflows import AuditWorkflow
from core.models import Certification, Organization, Standard

User = get_user_model()


class NonconformityFormTests(TestCase):
    """Test NonconformityForm validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-001",
            total_employee_count=10,
        )
        # Create an auditor for the created_by and lead_auditor fields
        self.auditor = User.objects.create_user(username="auditor_setup", password="testpass123")
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )
        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

    def test_form_valid_major_nc(self):
        """Test form with valid major NC data."""
        form_data = {
            "standard": self.standard.id,
            "clause": "4.1",
            "category": "major",
            "objective_evidence": "Records show systematic failure",
            "statement_of_nc": "Quality records not maintained",
            "auditor_explanation": "Clause 4.1 requires documented information",
        }
        form = NonconformityForm(data=form_data, audit=self.audit)
        self.assertTrue(form.is_valid())

    def test_form_requires_all_fields(self):
        """Test form validation fails when required fields missing."""
        form_data = {"clause": "4.1", "category": "minor"}
        form = NonconformityForm(data=form_data, audit=self.audit)
        self.assertFalse(form.is_valid())
        self.assertIn("objective_evidence", form.errors)
        self.assertIn("statement_of_nc", form.errors)
        self.assertIn("auditor_explanation", form.errors)


class NonconformityViewTests(TestCase):
    """Test nonconformity CRUD views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()

        # Create organization
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-002",
            total_employee_count=10,
        )

        # Create users and groups
        self.auditor = User.objects.create_user(
            username="auditor1", password="testpass123", first_name="Test", last_name="Auditor"
        )
        self.auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(self.auditor_group)

        self.client_user = User.objects.create_user(username="client1", password="testpass123")
        self.client_group = Group.objects.create(name="client")
        self.client_user.groups.add(self.client_group)

        self.regular_user = User.objects.create_user(username="regular1", password="testpass123")

        # Create audit
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            lead_auditor=self.auditor,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
        )

        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

    def test_auditor_can_add_nc(self):
        """Test auditor can access NC add form."""
        self.client.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_add_nc(self):
        """Test client cannot add findings."""
        self.client.login(username="client1", password="testpass123")
        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_regular_user_cannot_add_nc(self):
        """Test regular user cannot add findings."""
        self.client.login(username="regular1", password="testpass123")
        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_add_nc_post(self):
        """Test creating NC via POST."""
        self.client.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_create", kwargs={"audit_pk": self.audit.pk})
        data = {
            "standard": self.standard.id,
            "clause": "4.1",
            "category": "major",
            "objective_evidence": "Records show systematic failure",
            "statement_of_nc": "Quality records not maintained",
            "auditor_explanation": "Clause 4.1 requires documented information",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Nonconformity.objects.filter(audit=self.audit, clause="4.1").exists())

    def test_edit_nc_by_creator(self):
        """Test NC creator can edit."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        self.client.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_update", kwargs={"pk": nc.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_nc_after_client_response(self):
        """Test NC cannot be edited after client responds."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="client_responded",
        )

        self.client.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_update", kwargs={"pk": nc.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden - can't edit after client response

    def test_delete_nc_by_creator(self):
        """Test NC creator can delete."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        self.client.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_delete", kwargs={"pk": nc.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Nonconformity.objects.filter(pk=nc.pk).exists())


class ClientResponseTests(TestCase):
    """Test client response to nonconformities."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_http = Client()

        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-003",
            total_employee_count=10,
        )

        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.client_user = User.objects.create_user(username="client1", password="testpass123")
        client_group = Group.objects.create(name="client_user")
        self.client_user.groups.add(client_group)
        # Get or create profile and set organization
        profile, _ = Profile.objects.get_or_create(user=self.client_user)
        profile.organization = self.org
        profile.save()

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="client_review",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

        self.nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="open",
        )

    def test_client_can_respond(self):
        """Test client can access response form."""
        self.client_http.login(username="client1", password="testpass123")
        url = reverse("audits:nonconformity_respond", kwargs={"pk": self.nc.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_auditor_cannot_respond(self):
        """Test auditor cannot submit client response."""
        self.client_http.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_respond", kwargs={"pk": self.nc.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_client_submit_response(self):
        """Test client can submit response."""
        self.client_http.login(username="client1", password="testpass123")
        url = reverse("audits:nonconformity_respond", kwargs={"pk": self.nc.pk})
        data = {
            "client_root_cause": "Lack of training on documentation requirements",
            "client_correction": "Updated all missing records",
            "client_corrective_action": "Implemented training program for all staff",
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        response = self.client_http.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check NC status updated
        self.nc.refresh_from_db()
        self.assertEqual(self.nc.verification_status, "client_responded")
        self.assertIsNotNone(self.nc.client_root_cause)

    def test_cannot_respond_twice(self):
        """Test cannot respond to already responded NC."""
        self.nc.verification_status = "client_responded"
        self.nc.save()

        self.client_http.login(username="client1", password="testpass123")
        url = reverse("audits:nonconformity_respond", kwargs={"pk": self.nc.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect with error


class AuditorVerificationTests(TestCase):
    """Test auditor verification of client responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_http = Client()

        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-004",
            total_employee_count=10,
        )

        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.client_user = User.objects.create_user(username="client1", password="testpass123")
        client_group = Group.objects.create(name="client_user")
        self.client_user.groups.add(client_group)
        # Get or create profile and set organization
        profile, _ = Profile.objects.get_or_create(user=self.client_user)
        profile.organization = self.org
        profile.save()

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="client_review",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

        self.nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="client_responded",
            client_root_cause="Lack of training",
            client_correction="Updated records",
            client_corrective_action="Training program",
            due_date=date.today() + timedelta(days=30),
        )

    def test_auditor_can_verify(self):
        """Test auditor can access verification form."""
        self.client_http.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_verify", kwargs={"pk": self.nc.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_verify(self):
        """Test client cannot verify responses."""
        self.client_http.login(username="client1", password="testpass123")
        url = reverse("audits:nonconformity_verify", kwargs={"pk": self.nc.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_auditor_accept_response(self):
        """Test auditor can accept response."""
        self.client_http.login(username="auditor1", password="testpass123")
        url = reverse("audits:nonconformity_verify", kwargs={"pk": self.nc.pk})
        data = {
            "verification_status": "accepted",
            "verification_notes": "Corrective action plan is acceptable",
        }
        response = self.client_http.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Check NC status updated
        self.nc.refresh_from_db()
        self.assertEqual(self.nc.verification_status, "accepted")
        self.assertIsNotNone(self.nc.verified_by)
        self.assertIsNotNone(self.nc.verified_at)


class ObservationViewTests(TestCase):
    """Test observation CRUD views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_http = Client()

        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-005",
            total_employee_count=10,
        )

        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

    def test_add_observation(self):
        """Test creating observation."""
        self.client_http.login(username="auditor1", password="testpass123")
        url = reverse("audits:observation_add", kwargs={"audit_pk": self.audit.pk})
        data = {
            "standard": self.standard.id,
            "clause": "4.2",
            "statement": "Documentation could be improved",
            "explanation": "While compliant, better organization would help",
        }
        response = self.client_http.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Observation.objects.filter(audit=self.audit, clause="4.2").exists())


class WorkflowIntegrationTests(TestCase):
    """Test workflow integration with findings."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-006",
            total_employee_count=10,
        )

        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")
        lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor.groups.add(lead_auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="scheduled",
            lead_auditor=self.auditor,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
        )

        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality management systems - Requirements"
        )
        # Create certification and link to audit
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Quality Management",
            certificate_status="active",
        )
        self.audit.certifications.add(self.certification)

    def test_cannot_submit_with_open_major_nc(self):
        """Test workflow blocks submission with open major NCs."""
        # Create open major NC
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        workflow = AuditWorkflow(self.audit)
        can_transition, reason = workflow.can_transition("client_review", self.auditor)

        self.assertFalse(can_transition)
        self.assertIn("major nonconformity", reason.lower())

    def test_can_submit_with_responded_major_nc(self):
        """Test workflow allows submission when major NCs have responses."""
        # Create major NC with client response
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="client_responded",
            client_root_cause="Lack of training",
            client_correction="Updated records",
            client_corrective_action="Training program",
            due_date=date.today() + timedelta(days=30),
        )

        workflow = AuditWorkflow(self.audit)
        can_transition, reason = workflow.can_transition("client_review", self.auditor)

        self.assertTrue(can_transition)

    def test_can_submit_with_minor_ncs_only(self):
        """Test workflow allows submission with only minor NCs."""
        # Create minor NC (open is OK)
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="minor",
            objective_evidence="Test evidence",
            statement_of_nc="Test statement",
            auditor_explanation="Test explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        workflow = AuditWorkflow(self.audit)
        can_transition, reason = workflow.can_transition("client_review", self.auditor)

        self.assertTrue(can_transition)

"""
Workflow transition testing.

Tests AuditWorkflow state machine and status validation.
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase

from audits.workflows import AuditWorkflow
from core.models import Certification, Organization, Site, Standard
from core.test_utils import TEST_PASSWORD
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService


class AuditWorkflowTest(TestCase):
    """Test AuditWorkflow state machine."""

    def setUp(self):
        """Set up test data."""
        # Create groups
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        auditor_group = Group.objects.create(name="auditor")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password=TEST_PASSWORD)  # nosec B106
        self.lead_auditor.groups.add(lead_group)

        self.auditor = User.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        self.auditor.groups.add(auditor_group)

        # Create organization data
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Test",
            certificate_status="active",
        )

        self.site = Site.objects.create(organization=self.org, site_name="Site 1", site_address="123 St")

        # Create base audit (stage1 doesn't require prior audits)
        self.audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage1",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )
        self.audit.lead_auditor = self.lead_auditor
        self.audit.save()

    def test_valid_transition_draft_to_client_review(self):
        """Test valid transition from draft to client_review."""
        workflow = AuditWorkflow(self.audit)

        can_transition, _ = workflow.can_transition("scheduled", self.lead_auditor)
        self.assertTrue(can_transition)

        workflow.transition("scheduled", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

    def test_invalid_transition_draft_to_decided(self):
        """Test invalid transition from draft to decided (skipping steps)."""
        workflow = AuditWorkflow(self.audit)

        can_transition, reason = workflow.can_transition("decided", self.cb_admin)
        self.assertFalse(can_transition)
        self.assertIn("Invalid transition", reason)

        with self.assertRaises(ValidationError):
            workflow.transition("decided", self.cb_admin)

    def test_lead_auditor_can_transition_draft_to_client_review(self):
        """Test lead auditor can transition draft to client_review."""
        workflow = AuditWorkflow(self.audit)

        can_transition, _ = workflow.can_transition("scheduled", self.lead_auditor)
        self.assertTrue(can_transition)

    def test_regular_auditor_cannot_transition(self):
        """Test regular auditor cannot make status transitions."""
        workflow = AuditWorkflow(self.audit)

        can_transition, _ = workflow.can_transition("scheduled", self.auditor)
        self.assertFalse(can_transition)

    def test_cb_admin_can_override_transitions(self):
        """Test CB admin can make any transition."""
        workflow = AuditWorkflow(self.audit)

        # CB Admin can do draft → client_review
        can_transition, _ = workflow.can_transition("scheduled", self.cb_admin)
        self.assertTrue(can_transition)

    def test_backward_transition_requires_cb_admin(self):
        """Test backward transition (client_review → report_draft) allows lead auditor."""
        # First move to client_review
        self.audit.status = "client_review"
        self.audit.save()

        workflow = AuditWorkflow(self.audit)

        # Lead auditor CAN go backward to report_draft (for corrections)
        can_transition, _ = workflow.can_transition("report_draft", self.lead_auditor)
        self.assertTrue(can_transition)

        # CB admin can also
        can_transition, _ = workflow.can_transition("report_draft", self.cb_admin)
        self.assertTrue(can_transition)

    def test_complete_workflow_progression(self):
        """Test complete audit workflow from draft to decided."""
        from audits.models import CertificationDecision, TechnicalReview

        # draft → scheduled
        workflow = AuditWorkflow(self.audit)
        workflow.transition("scheduled", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

        # scheduled → in_progress
        workflow = AuditWorkflow(self.audit)
        workflow.transition("in_progress", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "in_progress")

        # Create at least one finding (required for report_draft transition)
        FindingService.create_observation(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "4.1",
                "statement": "Test observation statement",
                "explanation": "Test explanation",
            },
        )

        # in_progress → report_draft
        workflow = AuditWorkflow(self.audit)
        workflow.transition("report_draft", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "report_draft")

        # report_draft → client_review
        workflow = AuditWorkflow(self.audit)
        workflow.transition("client_review", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "client_review")

        # Create approved technical review (required before submission per ISO 17021-1)
        TechnicalReview.objects.create(
            audit=self.audit,
            reviewer=self.cb_admin,
            scope_verified=True,
            objectives_verified=True,
            findings_reviewed=True,
            conclusion_clear=True,
            status="approved",
        )

        # client_review → submitted (requires technical review)
        workflow = AuditWorkflow(self.audit)
        workflow.transition("submitted", self.cb_admin)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "submitted")

        # submitted → technical_review
        workflow = AuditWorkflow(self.audit)
        workflow.transition("technical_review", self.cb_admin)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "technical_review")

        # technical_review → decision_pending
        workflow = AuditWorkflow(self.audit)
        workflow.transition("decision_pending", self.cb_admin)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "decision_pending")

        # Create certification decision
        CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.cb_admin,
            decision="grant",
            decision_notes="Approved",
        )

        # decision_pending → closed
        workflow = AuditWorkflow(self.audit)
        workflow.transition("closed", self.cb_admin)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "closed")

    def test_transitions_from_decided(self):
        """Test transitions from decided status."""
        self.audit.status = "decided"
        self.audit.save()

        workflow = AuditWorkflow(self.audit)
        available = workflow.get_available_transitions(self.cb_admin)

        # Should allow transition to closed
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0][0], "closed")


class AuditWorkflowValidationTest(TestCase):
    """Test AuditWorkflow business rule validation."""

    def setUp(self):
        """Set up test data."""
        # Create groups
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password=TEST_PASSWORD)  # nosec B106
        self.lead_auditor.groups.add(lead_group)

        # Create organization data
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Test",
            certificate_status="active",
        )

        self.site = Site.objects.create(organization=self.org, site_name="Site 1", site_address="123 St")

        # Create audit
        self.audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )
        self.audit.lead_auditor = self.lead_auditor
        self.audit.save()

    def test_cannot_submit_with_open_major_nc(self):
        """Test cannot transition to submitted_to_cb with open major NCs."""
        # Create major NC
        FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Major NC",
                "auditor_explanation": "Test explanation",
            },
        )

        # Move to report_draft (required before client_review)
        self.audit.status = "report_draft"
        self.audit.save()

        # Try to transition to client_review (should succeed per ISO 17021-1)
        workflow = AuditWorkflow(self.audit)
        can_transition, _ = workflow.can_transition("client_review", self.lead_auditor)

        # ISO 17021-1: Reports WITH findings must be sent to clients for response
        self.assertTrue(can_transition)

    def test_can_submit_after_major_nc_responded(self):
        """Test can transition to submitted_to_cb after major NC is responded to."""
        # Create major NC
        nc = FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Major NC",
                "auditor_explanation": "Test explanation",
            },
        )

        # Respond to NC
        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Corrective action",
            },
        )

        # Move to report_draft (required before client_review)
        self.audit.status = "report_draft"
        self.audit.save()

        # Should be able to transition now
        workflow = AuditWorkflow(self.audit)
        can_transition, _ = workflow.can_transition("client_review", self.lead_auditor)

        self.assertTrue(can_transition)

    def test_minor_nc_does_not_block_submission(self):
        """Test minor NC without response does not block submission."""
        # Create minor NC (not responded)
        FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "minor",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Minor NC",
                "auditor_explanation": "Test explanation",
            },
        )

        # Move to report_draft (required before client_review)
        self.audit.status = "report_draft"
        self.audit.save()

        # Should be able to transition (minor NC doesn't block)
        workflow = AuditWorkflow(self.audit)
        can_transition, _ = workflow.can_transition("client_review", self.lead_auditor)

        self.assertTrue(can_transition)


class AuditWorkflowAvailableTransitionsTest(TestCase):
    """Test get_available_transitions method."""

    def setUp(self):
        """Set up test data."""
        # Create groups
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password=TEST_PASSWORD)  # nosec B106
        self.lead_auditor.groups.add(lead_group)

        # Create organization data
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Test",
            certificate_status="active",
        )

        self.site = Site.objects.create(organization=self.org, site_name="Site 1", site_address="123 St")

        # Create audit
        self.audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )
        self.audit.lead_auditor = self.lead_auditor
        self.audit.save()

    def test_available_transitions_for_lead_auditor_in_draft(self):
        """Test available transitions for lead auditor in draft status."""
        workflow = AuditWorkflow(self.audit)
        available = workflow.get_available_transitions(self.lead_auditor)

        # Should have client_review available
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0][0], "scheduled")

    def test_available_transitions_for_cb_admin_in_client_review(self):
        """Test available transitions for CB admin in scheduled status."""
        self.audit.status = "scheduled"
        self.audit.save()

        workflow = AuditWorkflow(self.audit)
        available = workflow.get_available_transitions(self.cb_admin)

        # From scheduled: can go to in_progress or cancelled
        self.assertEqual(len(available), 2)
        status_codes = [t[0] for t in available]
        self.assertIn("in_progress", status_codes)
        self.assertIn("cancelled", status_codes)

    def test_available_transitions_in_decided(self):
        """Test available transitions when audit is decided."""
        self.audit.status = "decided"
        self.audit.save()

        workflow = AuditWorkflow(self.audit)
        available = workflow.get_available_transitions(self.cb_admin)

        # Should allow transition to closed
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0][0], "closed")

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from audit_management.models import Audit, Nonconformity
from certification.models import TechnicalReview
from core.models import Certification, Organization, Site, Standard
from core.test_utils import TEST_PASSWORD
from trunk.workflows.audit_workflow import AuditWorkflow


class AuditWorkflowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password=TEST_PASSWORD)
        self.org = Organization.objects.create(name="Test Org", customer_id="CUST-001", total_employee_count=10)
        self.standard = Standard.objects.create(title="ISO 9001", code="ISO9001")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.site = Site.objects.create(organization=self.org, site_name="Main Site", site_address="123 Main St")

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=2),
            lead_auditor=self.user,
            created_by=self.user,
            status="draft",
        )
        self.audit.certifications.add(self.cert)
        self.audit.sites.add(self.site)

        self.workflow = AuditWorkflow(self.audit)

    def test_can_transition_to(self):
        self.assertTrue(self.workflow.can_transition_to("scheduled"))
        self.assertTrue(self.workflow.can_transition_to("cancelled"))
        self.assertFalse(self.workflow.can_transition_to("in_progress"))
        self.assertFalse(self.workflow.can_transition_to("closed"))

    def test_validate_transition_invalid(self):
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("in_progress")
        self.assertIn("Cannot transition from 'draft' to 'in_progress'", str(cm.exception))

    def test_validate_scheduled_success(self):
        # Setup is already valid for scheduled
        try:
            self.workflow.validate_transition("scheduled")
        except ValidationError:
            self.fail("validate_transition('scheduled') raised ValidationError unexpectedly!")

    def test_validate_scheduled_missing_dates(self):
        self.audit.total_audit_date_from = None
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("scheduled")
        self.assertIn("Cannot schedule audit without audit dates", str(cm.exception))

    def test_validate_scheduled_missing_lead_auditor(self):
        self.audit.lead_auditor = None
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("scheduled")
        self.assertIn("Cannot schedule audit without a lead auditor assigned", str(cm.exception))

    def test_validate_in_progress_success(self):
        self.audit.status = "scheduled"
        try:
            self.workflow.validate_transition("in_progress")
        except ValidationError:
            self.fail("validate_transition('in_progress') raised ValidationError unexpectedly!")

    def test_validate_in_progress_missing_lead_auditor(self):
        self.audit.status = "scheduled"
        self.audit.lead_auditor = None
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("in_progress")
        self.assertIn("Cannot start audit without a lead auditor assigned", str(cm.exception))

    def test_validate_report_draft_success(self):
        self.audit.status = "in_progress"
        # Add a finding
        Nonconformity.objects.create(
            audit=self.audit,
            category="minor",
            clause="4.1",
            created_by=self.user,
            standard=self.standard,
            site=self.site,
        )
        try:
            self.workflow.validate_transition("report_draft")
        except ValidationError:
            self.fail("validate_transition('report_draft') raised ValidationError unexpectedly!")

    def test_validate_report_draft_no_findings(self):
        self.audit.status = "in_progress"
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("report_draft")
        self.assertIn("Cannot move to report draft without at least one finding", str(cm.exception))

    def test_validate_submitted_success(self):
        self.audit.status = "client_review"
        # Add a major NC with response
        Nonconformity.objects.create(
            audit=self.audit,
            category="major",
            clause="4.1",
            created_by=self.user,
            standard=self.standard,
            site=self.site,
            client_root_cause="Cause",
            client_corrective_action="Action",
        )
        try:
            self.workflow.validate_transition("submitted")
        except ValidationError:
            self.fail("validate_transition('submitted') raised ValidationError unexpectedly!")

    def test_validate_submitted_missing_response(self):
        self.audit.status = "client_review"
        # Add a major NC without response
        Nonconformity.objects.create(
            audit=self.audit,
            category="major",
            clause="4.1",
            created_by=self.user,
            standard=self.standard,
            site=self.site,
        )
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("submitted")
        self.assertIn("missing client response", str(cm.exception))

    def test_validate_decision_pending_success(self):
        self.audit.status = "technical_review"
        # Create approved technical review
        TechnicalReview.objects.create(audit=self.audit, reviewer=self.user, status="approved")
        try:
            self.workflow.validate_transition("decision_pending")
        except ValidationError:
            self.fail("validate_transition('decision_pending') raised ValidationError unexpectedly!")

    def test_validate_decision_pending_no_review(self):
        self.audit.status = "technical_review"
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("decision_pending")
        self.assertIn("Technical review is required", str(cm.exception))

    def test_validate_decision_pending_review_not_approved(self):
        self.audit.status = "technical_review"
        TechnicalReview.objects.create(audit=self.audit, reviewer=self.user, status="rejected")
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("decision_pending")
        self.assertIn("must be 'Approved'", str(cm.exception))

    def test_validate_closed_stage2_success(self):
        self.audit.status = "decision_pending"
        self.audit.audit_type = "stage2"
        # Create completed stage 1
        Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="closed",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            lead_auditor=self.user,
            created_by=self.user,
        )
        try:
            self.workflow.validate_transition("closed")
        except ValidationError:
            self.fail("validate_transition('closed') raised ValidationError unexpectedly!")

    def test_validate_closed_stage2_missing_stage1(self):
        self.audit.status = "decision_pending"
        self.audit.audit_type = "stage2"
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("closed")
        self.assertIn("Stage 2 audit requires a completed Stage 1 audit", str(cm.exception))

    def test_validate_closed_surveillance_success(self):
        self.audit.status = "decision_pending"
        self.audit.audit_type = "surveillance"
        # Active cert already exists from setUp
        try:
            self.workflow.validate_transition("closed")
        except ValidationError:
            self.fail("validate_transition('closed') raised ValidationError unexpectedly!")

    def test_validate_closed_surveillance_no_active_cert(self):
        self.audit.status = "decision_pending"
        self.audit.audit_type = "surveillance"
        self.cert.certificate_status = "expired"
        self.cert.save()
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("closed")
        self.assertIn("Surveillance audit requires active certifications", str(cm.exception))

    def test_validate_closed_open_major_nc(self):
        self.audit.status = "decision_pending"
        Nonconformity.objects.create(
            audit=self.audit,
            category="major",
            clause="4.1",
            created_by=self.user,
            standard=self.standard,
            site=self.site,
            verification_status="open",
        )
        with self.assertRaises(ValidationError) as cm:
            self.workflow.validate_transition("closed")
        self.assertIn("major NC(s) still open", str(cm.exception))

    def test_validate_decided_open_nc(self):
        # This tests the legacy 'decided' status validation logic
        # We need to force status to something that can transition to decided?
        # Wait, 'decided' is a legacy state, but validate_decided is called if we transition TO decided.
        # But there is no transition TO decided in TRANSITIONS map except maybe from... wait.
        # TRANSITIONS = { ... "decision_pending": ["closed", "technical_review"], ... }
        # There is no transition TO "decided" in the current map!
        # "decided": ["closed"] is a FROM transition.

        # Let's check if I can test validate_decided directly.
        self.audit.status = "decision_pending"  # Or whatever

        # Add open NC
        Nonconformity.objects.create(
            audit=self.audit,
            category="minor",
            clause="4.1",
            created_by=self.user,
            standard=self.standard,
            site=self.site,
            verification_status="open",
        )

        # Since validate_decided is an internal method called by validate_transition if new_status is 'decided'
        # But 'decided' is not in any allowed transition list.
        # So validate_transition("decided") will fail at can_transition_to check first.

        # However, I can test _validate_decided directly if I want to cover it.
        with self.assertRaises(ValidationError) as cm:
            self.workflow._validate_decided()
        self.assertIn("still open", str(cm.exception))

    def test_transition_to(self):
        self.audit.status = "draft"
        self.workflow.transition_to("scheduled")
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

    def test_get_available_transitions(self):
        self.audit.status = "draft"
        transitions = self.workflow.get_available_transitions()
        codes = [t["code"] for t in transitions]
        self.assertIn("scheduled", codes)
        self.assertIn("cancelled", codes)

        # Check structure
        scheduled = next(t for t in transitions if t["code"] == "scheduled")
        self.assertTrue(scheduled["available"])
        self.assertIsNone(scheduled["reason"])

    def test_get_all_statuses(self):
        statuses = AuditWorkflow.get_all_statuses()
        codes = [s["code"] for s in statuses]
        self.assertIn("draft", codes)
        self.assertIn("closed", codes)

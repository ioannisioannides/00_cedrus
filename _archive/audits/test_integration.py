"""
Integration tests for complete audit workflow.

Tests the full audit lifecycle from creation through decision-making,
including findings, client responses, and verification.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import Nonconformity, Observation, OpportunityForImprovement
from core.models import Certification, Organization, Site, Standard
from core.test_utils import TEST_PASSWORD
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService


class AuditWorkflowIntegrationTest(TestCase):
    """Test complete audit workflow end-to-end."""

    def setUp(self):
        """Set up test data."""
        # Create groups
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_admin_group = Group.objects.create(name="client_admin")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin.groups.add(self.cb_admin_group)

        self.lead_auditor = User.objects.create_user(username="lead", password=TEST_PASSWORD)  # nosec B106
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.client_admin = User.objects.create_user(username="clientadmin", password=TEST_PASSWORD)  # nosec B106
        self.client_admin.groups.add(self.client_admin_group)

        # Create organization
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="ORG001",
            total_employee_count=50,
        )

        # Create standard
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

        # Create certification
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Manufacturing",
            certificate_status="active",
        )

        # Create site
        self.site = Site.objects.create(organization=self.org, site_name="Main Site", site_address="123 Test St")

        # Link client to organization
        self.client_admin.profile.organization = self.org
        self.client_admin.profile.save()

        self.client = Client()

    def _create_audit(self):
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        return AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "surveillance",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=3),
                "planned_duration_hours": 24.0,
                "lead_auditor": self.lead_auditor,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

    def _create_findings(self, audit):
        self.client.login(username="lead", password=TEST_PASSWORD)  # nosec B106
        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "No documented procedure for document control",
                "statement_of_nc": "Clause 7.5.1 requirement not met",
                "auditor_explanation": "Organization lacks documented information control",
            },
        )
        FindingService.create_observation(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "8.2.1",
                "statement": "Customer requirements are identified",
                "explanation": "Process works well but could be documented better",
            },
        )
        FindingService.create_ofi(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "9.1.1",
                "description": "Consider implementing automated monitoring",
            },
        )
        return nc

    def _transition_audit(self, audit, status):
        self.client.post(reverse("audits:audit_transition_status", args=[audit.pk, status]))
        audit.refresh_from_db()
        self.assertEqual(audit.status, status)

    def test_complete_audit_workflow(self):
        """Test full audit workflow from creation to decision."""

        # Step 1: CB Admin creates audit
        audit = self._create_audit()

        self.assertEqual(audit.status, "draft")
        self.assertEqual(audit.lead_auditor, self.lead_auditor)

        # Step 2 & 3: Lead Auditor adds findings
        nc = self._create_findings(audit)

        self.assertEqual(nc.verification_status, "open")
        self.assertEqual(nc.category, "major")
        self.assertIsNotNone(nc)

        # Step 4: Lead Auditor transitions through workflow
        # draft → scheduled
        self._transition_audit(audit, "scheduled")

        # scheduled → in_progress
        self._transition_audit(audit, "in_progress")

        # in_progress → report_draft (requires findings, which we have)
        self._transition_audit(audit, "report_draft")

        # report_draft → client_review
        self._transition_audit(audit, "client_review")

        # Step 5: Client responds to nonconformity
        self.client.login(username="clientadmin", password=TEST_PASSWORD)  # nosec B106

        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Staff turnover led to knowledge gap",
                "client_correction": "Implemented temporary procedure",
                "client_corrective_action": "Will develop and implement full documented procedure",
                "due_date": date.today() + timedelta(days=30),
            },
        )

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "client_responded")
        self.assertIsNotNone(nc.client_root_cause)

        # Step 6: Lead Auditor verifies response (accepts)
        self.client.login(username="lead", password=TEST_PASSWORD)  # nosec B106

        FindingService.verify_nonconformity(
            nc=nc,
            user=self.lead_auditor,
            action="accept",
            notes="Corrective action plan is adequate",
        )

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "accepted")
        self.assertEqual(nc.verified_by, self.lead_auditor)

        # Step 7: Create and approve technical review (required before submission)
        from audits.models import TechnicalReview

        TechnicalReview.objects.create(
            audit=audit,
            reviewer=self.cb_admin,
            scope_verified=True,
            objectives_verified=True,
            findings_reviewed=True,
            conclusion_clear=True,
            reviewer_notes="All requirements met",
            status="approved",
        )

        # Step 8: CB Admin or Lead Auditor moves to submitted (after technical review)
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106

        self._transition_audit(audit, "submitted")

        # Step 8.1: Move to technical_review
        self._transition_audit(audit, "technical_review")

        # Step 8.2: Move to decision_pending
        self._transition_audit(audit, "decision_pending")

        # Step 9: Create certification decision (audit is now in 'submitted' status)
        from audits.models import CertificationDecision

        decision = CertificationDecision.objects.create(
            audit=audit,
            decision_maker=self.cb_admin,
            decision="grant",
            decision_notes="All audit findings addressed, certification approved",
        )
        decision.certifications_affected.add(self.cert)

        # Step 12: Transition to closed
        self._transition_audit(audit, "closed")

        # Verify the complete workflow
        self.assertEqual(Nonconformity.objects.filter(audit=audit).count(), 1)
        self.assertEqual(Observation.objects.filter(audit=audit).count(), 1)
        self.assertEqual(OpportunityForImprovement.objects.filter(audit=audit).count(), 1)

    def test_workflow_with_rejected_response(self):
        """Test workflow when auditor rejects client response."""

        # Create audit with NC
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=3),
                "planned_duration_hours": 24.0,
                "lead_auditor": self.lead_auditor,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.client.login(username="lead", password=TEST_PASSWORD)  # nosec B106

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "minor",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        # Submit to client
        self.client.post(reverse("audits:audit_transition_status", args=[audit.pk, "scheduled"]))

        # Client responds
        self.client.login(username="clientadmin", password=TEST_PASSWORD)  # nosec B106
        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Insufficient analysis",
                "client_correction": "Quick fix",
                "client_corrective_action": "Will look into it",
            },
        )

        # Lead Auditor rejects response
        self.client.login(username="lead", password=TEST_PASSWORD)  # nosec B106
        FindingService.verify_nonconformity(
            nc=nc,
            user=self.lead_auditor,
            action="request_changes",
            notes="Root cause analysis insufficient, corrective action too vague",
        )

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "open")
        self.assertIn("insufficient", nc.verification_notes.lower())

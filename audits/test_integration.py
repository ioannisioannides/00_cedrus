"""
Integration tests for complete audit workflow.

Tests the full audit lifecycle from creation through decision-making,
including findings, client responses, and verification.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import Audit, Nonconformity, Observation, OpportunityForImprovement
from core.models import Certification, Organization, Site, Standard
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
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.cb_admin.groups.add(self.cb_admin_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.client_admin = User.objects.create_user(username="clientadmin", password="pass123")
        self.client_admin.groups.add(self.client_admin_group)

        # Create organization
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="ORG001",
            total_employee_count=50,
        )

        # Create standard
        self.standard = Standard.objects.create(
            code="ISO 9001:2015", title="Quality Management Systems"
        )

        # Create certification
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Manufacturing",
            certificate_status="active",
        )

        # Create site
        self.site = Site.objects.create(
            organization=self.org, site_name="Main Site", site_address="123 Test St"
        )

        # Link client to organization
        self.client_admin.profile.organization = self.org
        self.client_admin.profile.save()

        self.client = Client()

    def test_complete_audit_workflow(self):
        """Test full audit workflow from creation to decision."""

        # Step 1: CB Admin creates audit
        self.client.login(username="cbadmin", password="pass123")

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "surveillance",  # Use surveillance to avoid stage1 requirement
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=3),
                "planned_duration_hours": 24.0,
                "lead_auditor": self.lead_auditor,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.assertEqual(audit.status, "draft")
        self.assertEqual(audit.lead_auditor, self.lead_auditor)

        # Step 2: Lead Auditor adds a major nonconformity
        self.client.login(username="lead", password="pass123")

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

        self.assertEqual(nc.verification_status, "open")
        self.assertEqual(nc.category, "major")

        # Step 3: Lead Auditor adds observations and OFIs
        obs = FindingService.create_observation(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "8.2.1",
                "statement": "Customer requirements are identified",
                "explanation": "Process works well but could be documented better",
            },
        )

        ofi = FindingService.create_ofi(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "9.1.1",
                "description": "Consider implementing automated monitoring",
            },
        )

        self.assertIsNotNone(obs)
        self.assertIsNotNone(ofi)

        # Step 4: Lead Auditor transitions through workflow
        # draft → scheduled
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "scheduled"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "scheduled")

        # scheduled → in_progress
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "in_progress"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "in_progress")

        # in_progress → report_draft (requires findings, which we have)
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "report_draft"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "report_draft")

        # report_draft → client_review
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "client_review"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "client_review")

        # Step 5: Client responds to nonconformity
        self.client.login(username="clientadmin", password="pass123")

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
        self.client.login(username="lead", password="pass123")

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

        tech_review = TechnicalReview.objects.create(
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
        self.client.login(username="cbadmin", password="pass123")

        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "submitted"])
        )

        audit.refresh_from_db()
        self.assertEqual(audit.status, "submitted")

        # Step 8.1: Move to technical_review
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "technical_review"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "technical_review")

        # Step 8.2: Move to decision_pending
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "decision_pending"])
        )
        audit.refresh_from_db()
        self.assertEqual(audit.status, "decision_pending")

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
        response = self.client.post(
            reverse("audits:audit_transition_status", args=[audit.pk, "closed"])
        )

        audit.refresh_from_db()
        self.assertEqual(audit.status, "closed")

        # Verify the complete workflow
        self.assertEqual(Nonconformity.objects.filter(audit=audit).count(), 1)
        self.assertEqual(Observation.objects.filter(audit=audit).count(), 1)
        self.assertEqual(OpportunityForImprovement.objects.filter(audit=audit).count(), 1)

    def test_workflow_with_rejected_response(self):
        """Test workflow when auditor rejects client response."""

        # Create audit with NC
        self.client.login(username="cbadmin", password="pass123")

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

        self.client.login(username="lead", password="pass123")

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
        self.client.login(username="clientadmin", password="pass123")
        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Insufficient analysis",
                "client_correction": "Quick fix",
                "client_corrective_action": "Will look into it",
            },
        )

        # Lead Auditor rejects response
        self.client.login(username="lead", password="pass123")
        FindingService.verify_nonconformity(
            nc=nc,
            user=self.lead_auditor,
            action="request_changes",
            notes="Root cause analysis insufficient, corrective action too vague",
        )

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "open")
        self.assertIn("insufficient", nc.verification_notes.lower())

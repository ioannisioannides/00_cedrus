"""
Tests for Priority 2 features: Status Workflow, Documentation UI, Recommendations & Decisions, File Management.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Profile
from audits.models import (
    Audit,
    AuditChanges,
    AuditPlanReview,
    AuditRecommendation,
    AuditSummary,
    EvidenceFile,
    Nonconformity,
)
from audits.workflows import AuditWorkflow
from core.models import Certification, Organization, Standard


class AuditWorkflowTest(TestCase):
    """Test audit status workflow and transitions."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Test scope",
            certificate_status="active",
        )

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.auditor = User.objects.create_user(username="auditor", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        auditor_group = Group.objects.create(name="auditor")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.audit.certifications.add(self.cert)

    def test_workflow_draft_to_in_review(self):
        """Test transition from draft to in_review."""
        workflow = AuditWorkflow(self.audit)
        allowed, _ = workflow.can_transition("scheduled", self.lead_auditor)
        self.assertTrue(allowed)

        workflow.transition("scheduled", self.lead_auditor)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

    def test_workflow_requires_major_nc_responses(self):
        """Test that major NCs must have responses before submitting to CB."""
        # Create major NC without response
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            auditor_explanation="Explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        # Transition through workflow to report_draft
        self.audit.status = "report_draft"
        self.audit.save()

        # Transition to client_review
        workflow = AuditWorkflow(self.audit)
        workflow.transition("client_review", self.lead_auditor)
        self.audit.refresh_from_db()

        # Try to submit - should fail without technical review and NC responses
        from audits.models import TechnicalReview
        TechnicalReview.objects.create(
            audit=self.audit,
            reviewer=self.cb_admin,
            scope_verified=True,
            objectives_verified=True,
            findings_reviewed=True,
            conclusion_clear=True,
            status="approved",
        )

        workflow = AuditWorkflow(self.audit)
        allowed, reason = workflow.can_transition("submitted", self.lead_auditor)
        self.assertFalse(allowed)
        self.assertIn("major", reason.lower())

        # Add response
        nc.verification_status = "client_responded"
        nc.client_root_cause = "Root cause"
        nc.client_correction = "Correction"
        nc.client_corrective_action = "Action"
        nc.save()

        # Now should be able to submit
        workflow = AuditWorkflow(self.audit)
        allowed, _ = workflow.can_transition("submitted", self.lead_auditor)
        self.assertTrue(allowed)

    def test_workflow_permission_checks(self):
        """Test that only authorized users can perform transitions."""
        workflow = AuditWorkflow(self.audit)

        # Lead auditor can submit to client
        allowed, _ = workflow.can_transition("scheduled", self.lead_auditor)
        self.assertTrue(allowed)

        # Regular auditor cannot submit to client
        allowed, _ = workflow.can_transition("scheduled", self.auditor)
        self.assertFalse(allowed)

        # Move to client_review
        self.audit.status = "client_review"
        self.audit.save()

        # Create approved technical review (required for transition)
        from audits.models import TechnicalReview
        TechnicalReview.objects.create(
            audit=self.audit,
            reviewer=self.cb_admin,
            scope_verified=True,
            objectives_verified=True,
            findings_reviewed=True,
            conclusion_clear=True,
            status="approved",
        )

        # Create new workflow instance with updated status
        workflow = AuditWorkflow(self.audit)

        # Both CB Admin and Lead Auditor can submit after technical review
        allowed, _ = workflow.can_transition("submitted", self.cb_admin)
        self.assertTrue(allowed)

        allowed, _ = workflow.can_transition("submitted", self.lead_auditor)
        self.assertTrue(allowed)

    def test_workflow_decided_is_final(self):
        """Test that decided status cannot be changed."""
        self.audit.status = "decided"
        self.audit.save()

        workflow = AuditWorkflow(self.audit)
        allowed, _ = workflow.can_transition("draft", self.cb_admin)
        self.assertFalse(allowed)


class AuditDocumentationViewTest(TestCase):
    """Test audit documentation views (Changes, Plan Review, Summary)."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_audit_changes_view_get(self):
        """Test GET audit changes edit view."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_changes_edit", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIn("audit", response.context)

    def test_audit_changes_view_post(self):
        """Test POST audit changes edit view."""
        self.client.login(username="lead", password="pass123")
        data = {
            "change_of_name": True,
            "change_of_scope": False,
            "change_of_sites": False,
            "change_of_ms_rep": False,
            "change_of_signatory": False,
            "change_of_employee_count": True,
            "change_of_contact_info": False,
            "other_has_change": True,
            "other_description": "Test description",
        }
        response = self.client.post(
            reverse("audits:audit_changes_edit", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

        changes = AuditChanges.objects.get(audit=self.audit)
        self.assertTrue(changes.change_of_name)
        self.assertTrue(changes.change_of_employee_count)
        self.assertTrue(changes.other_has_change)
        self.assertEqual(changes.other_description, "Test description")

    def test_audit_plan_review_view(self):
        """Test audit plan review edit view."""
        self.client.login(username="lead", password="pass123")
        data = {
            "deviations_yes_no": True,
            "deviations_details": "Deviation details here",
            "issues_affecting_yes_no": False,
            "issues_affecting_details": "",
            "next_audit_date_from": (date.today() + timedelta(days=365)).isoformat(),
            "next_audit_date_to": (date.today() + timedelta(days=368)).isoformat(),
        }
        response = self.client.post(
            reverse("audits:audit_plan_review_edit", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)

        plan_review = AuditPlanReview.objects.get(audit=self.audit)
        self.assertTrue(plan_review.deviations_yes_no)
        self.assertEqual(plan_review.deviations_details, "Deviation details here")

    def test_audit_summary_view(self):
        """Test audit summary edit view."""
        self.client.login(username="lead", password="pass123")
        data = {
            "objectives_met": True,
            "objectives_comments": "Objectives met",
            "scope_appropriate": True,
            "scope_comments": "Scope appropriate",
            "ms_meets_requirements": True,
            "ms_comments": "MS meets requirements",
            "management_review_effective": True,
            "management_review_comments": "Effective",
            "internal_audit_effective": True,
            "internal_audit_comments": "Effective",
            "ms_effective": True,
            "ms_effective_comments": "Overall effective",
            "correct_use_of_logos": True,
            "logos_comments": "Correct usage",
            "promoted_to_committee": False,
            "committee_comments": "",
            "general_commentary": "General commentary here",
        }
        response = self.client.post(
            reverse("audits:audit_summary_edit", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)

        summary = AuditSummary.objects.get(audit=self.audit)
        self.assertTrue(summary.objectives_met)
        self.assertTrue(summary.ms_effective)
        self.assertEqual(summary.general_commentary, "General commentary here")


class AuditRecommendationTest(TestCase):
    """Test audit recommendations and certification decision workflow."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Test scope",
            certificate_status="active",
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",  # Use surveillance to avoid stage1 requirement
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="client_review",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.audit.certifications.add(self.cert)

    def test_recommendation_view_lead_auditor(self):
        """Test lead auditor can edit recommendations."""
        self.client.login(username="lead", password="pass123")
        data = {
            "special_audit_required": True,
            "special_audit_details": "Special audit needed",
            "suspension_recommended": False,
            "suspension_certificates": "",
            "revocation_recommended": False,
            "revocation_certificates": "",
            "stage2_required": False,
            "decision_notes": "Additional notes",
        }
        response = self.client.post(
            reverse("audits:audit_recommendation_edit", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)

        recommendation = AuditRecommendation.objects.get(audit=self.audit)
        self.assertTrue(recommendation.special_audit_required)
        self.assertEqual(recommendation.special_audit_details, "Special audit needed")

    def test_recommendation_view_cb_admin(self):
        """Test CB admin can edit recommendations."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(
            reverse("audits:audit_recommendation_edit", args=[self.audit.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_decision_view_requires_decision_pending_status(self):
        """Test decision can only be made when status is decision_pending."""
        self.audit.status = "draft"
        self.audit.save()

        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(
            reverse("audits:certification_decision_create", args=[self.audit.pk])
        )
        # Should return 403 Forbidden (UserPassesTestMixin returns False)
        self.assertEqual(response.status_code, 403)

    def test_decision_view_cb_admin_only(self):
        """Test only CB admin can make decisions."""
        self.audit.status = "decision_pending"
        self.audit.save()

        self.client.login(username="lead", password="pass123")
        response = self.client.get(
            reverse("audits:certification_decision_create", args=[self.audit.pk])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_make_decision_changes_status(self):
        """Test making decision changes audit status to closed."""
        from audits.models import TechnicalReview

        self.client.login(username="cbadmin", password="pass123")

        # Move audit to client_review
        self.audit.status = "client_review"
        self.audit.save()

        # Move to submitted
        self.client.post(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "submitted"])
        )
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "submitted")

        # Move to technical_review
        self.client.post(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "technical_review"])
        )
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "technical_review")

        # Create approved technical review (required)
        TechnicalReview.objects.create(
            audit=self.audit,
            reviewer=self.cb_admin,
            scope_verified=True,
            objectives_verified=True,
            findings_reviewed=True,
            conclusion_clear=True,
            status="approved",
        )

        # Move to decision_pending
        self.client.post(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "decision_pending"])
        )
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "decision_pending")

        # Create certification decision via view
        data = {
            "decision": "grant",
            "decision_notes": "Certification granted",
            "certifications_affected": [self.cert.pk],
        }
        self.client.post(
            reverse("audits:certification_decision_create", args=[self.audit.pk]), data
        )

        # Verify status is closed
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "closed")


class EvidenceFileManagementTest(TestCase):
    """Test evidence file upload, download, and deletion."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.client_user = User.objects.create_user(username="client", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        client_group = Group.objects.create(name="client_admin")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)
        self.client_user.groups.add(client_group)

        # Create profile for client
        profile, _ = Profile.objects.get_or_create(user=self.client_user)
        profile.organization = self.org
        profile.save()

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_file_upload_auditor(self):
        """Test auditor can upload evidence files."""
        self.client.login(username="lead", password="pass123")

        # Create a test file
        test_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")

        data = {"file": test_file, "finding": ""}  # General evidence
        response = self.client.post(
            reverse("audits:evidence_file_upload", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check file was created
        files = EvidenceFile.objects.filter(audit=self.audit)
        self.assertEqual(files.count(), 1)
        self.assertEqual(files.first().uploaded_by, self.lead_auditor)

    def test_file_upload_client(self):
        """Test client can upload evidence files."""
        self.client.login(username="client", password="pass123")

        test_file = SimpleUploadedFile(
            "client_doc.pdf", b"client_content", content_type="application/pdf"
        )

        data = {"file": test_file, "finding": ""}
        response = self.client.post(
            reverse("audits:evidence_file_upload", args=[self.audit.pk]), data
        )
        self.assertEqual(response.status_code, 302)

        files = EvidenceFile.objects.filter(audit=self.audit)
        self.assertEqual(files.count(), 1)

    def test_file_download_permission(self):
        """Test file download requires proper permissions."""
        # Create evidence file
        test_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        evidence = EvidenceFile.objects.create(
            audit=self.audit, uploaded_by=self.lead_auditor, file=test_file
        )

        # CB Admin can download
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:evidence_file_download", args=[evidence.pk]))
        self.assertEqual(response.status_code, 200)

        # Lead auditor can download
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:evidence_file_download", args=[evidence.pk]))
        self.assertEqual(response.status_code, 200)

        # Client can download their org's files
        self.client.login(username="client", password="pass123")
        response = self.client.get(reverse("audits:evidence_file_download", args=[evidence.pk]))
        self.assertEqual(response.status_code, 200)

    def test_file_delete_uploader(self):
        """Test uploader can delete their own files."""
        test_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        evidence = EvidenceFile.objects.create(
            audit=self.audit, uploaded_by=self.lead_auditor, file=test_file
        )

        self.client.login(username="lead", password="pass123")
        response = self.client.post(reverse("audits:evidence_file_delete", args=[evidence.pk]))
        self.assertEqual(response.status_code, 302)

        # File should be deleted
        self.assertFalse(EvidenceFile.objects.filter(pk=evidence.pk).exists())

    def test_file_delete_cb_admin(self):
        """Test CB admin can delete any file."""
        test_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        evidence = EvidenceFile.objects.create(
            audit=self.audit, uploaded_by=self.lead_auditor, file=test_file
        )

        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(reverse("audits:evidence_file_delete", args=[evidence.pk]))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(EvidenceFile.objects.filter(pk=evidence.pk).exists())


class StatusTransitionViewTest(TestCase):
    """Test status transition view."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_transition_draft_to_in_review(self):
        """Test transition from draft to in_review via view."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "scheduled"])
        )
        self.assertEqual(response.status_code, 302)  # Redirect

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

    def test_transition_invalid(self):
        """Test invalid transition shows error."""
        self.client.login(username="lead", password="pass123")
        # Try to go straight to decided (invalid)
        response = self.client.get(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "decided"])
        )
        self.assertEqual(response.status_code, 302)

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "draft")  # Should remain draft

    def test_transition_permission_denied(self):
        """Test transition requires proper permissions."""
        self.audit.status = "client_review"
        self.audit.save()

        # Lead auditor cannot make decision
        self.client.login(username="lead", password="pass123")
        response = self.client.get(
            reverse("audits:audit_transition_status", args=[self.audit.pk, "decided"])
        )
        self.assertEqual(response.status_code, 302)

        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "client_review")  # Should remain

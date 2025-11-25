"""
Phase 2A Complete Integration Tests

Tests for the "Ultimate Logic" implementation of ISO 17021-1 requirements:
1. Auditor Competence (Clause 7) - Accounts App
2. Certificate Lifecycle (Clause 9.6) - Core App
3. Complaints & Appeals (Clause 9.8) - Audits App
4. Impartiality (Clause 5.2) - Accounts App
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import AuditorQualification, ConflictOfInterest
from audits.models import Appeal, Audit, CertificationDecision, Complaint
from core.models import CertificateHistory, Certification, Organization, Standard, SurveillanceSchedule
from trunk.services.certificate_service import CertificateService
from trunk.services.competence_service import CompetenceService
from trunk.services.complaint_service import ComplaintService


class AuditorCompetenceTests(TestCase):
    """Test Auditor Competence and Impartiality logic (Clause 7 & 5.2)."""

    def setUp(self):
        self.auditor = User.objects.create_user(username="auditor_jane", password="password")
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="QMS")
        self.org = Organization.objects.create(name="Test Org", customer_id="C001", total_employee_count=10)

    def test_auditor_qualification_tracking(self):
        """Test recording and retrieving auditor qualifications."""
        qual = AuditorQualification.objects.create(
            auditor=self.auditor,
            qualification_type="lead_auditor_cert",
            issuing_body="IRCA",
            certificate_number="12345",
            issue_date=date.today() - timedelta(days=100),
            status="active"
        )
        qual.standards.add(self.standard)

        active_quals = CompetenceService.get_active_qualifications(self.auditor)
        self.assertIn(qual, active_quals)
        self.assertEqual(active_quals[0].qualification_type, "lead_auditor_cert")

    def test_competence_validation_service(self):
        """Test the service that validates auditor competence for an audit."""
        # Create an audit requiring ISO 9001
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            created_by=self.auditor,
            lead_auditor=self.auditor
        )
        cert = Certification.objects.create(
            organization=self.org, standard=self.standard, certification_scope="Scope"
        )
        audit.certifications.add(cert)

        # Auditor has NO qualifications yet -> Should fail
        with self.assertRaises(ValidationError) as cm:
            CompetenceService.ensure_auditor_has_active_qualification(self.auditor, audit)
        self.assertIn("lacks active qualifications", str(cm.exception))

        # Add qualification
        qual = AuditorQualification.objects.create(
            auditor=self.auditor,
            qualification_type="lead_auditor_cert",
            issuing_body="IRCA",
            certificate_number="12345",
            issue_date=date.today(),
            status="active"
        )
        qual.standards.add(self.standard)

        # Now should pass
        try:
            CompetenceService.ensure_auditor_has_active_qualification(self.auditor, audit)
        except ValidationError:
            self.fail("CompetenceService raised ValidationError unexpectedly!")

    def test_conflict_of_interest_declaration(self):
        """Test COI declaration logic."""
        coi = ConflictOfInterest.objects.create(
            auditor=self.auditor,
            organization=self.org,
            relationship_type="former_employee",
            description="Worked there 2 years ago",
            impartiality_risk="high"
        )
        self.assertEqual(coi.impartiality_risk, "high")
        self.assertTrue(coi.is_active)


class CertificateLifecycleTests(TestCase):
    """Test Certificate Lifecycle logic (Clause 9.6)."""

    def setUp(self):
        self.cb_admin = User.objects.create_user(username="admin", password="password")
        self.org = Organization.objects.create(name="Cert Org", customer_id="C002", total_employee_count=50)
        self.standard = Standard.objects.create(code="ISO 14001:2015", title="EMS")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Environmental Management",
            certificate_status="draft",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=1095)
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            created_by=self.cb_admin,
            lead_auditor=self.cb_admin
        )
        self.audit.certifications.add(self.cert)

    def test_certificate_history_creation(self):
        """Test that a certification decision creates a history entry."""
        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.cb_admin,
            decision="grant",
            decision_notes="All good"
        )

        # Simulate service call (usually triggered by signal or view)
        CertificateService.record_decision(decision)

        history = CertificateHistory.objects.filter(certification=self.cert).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.action, "issued")
        self.assertEqual(history.related_decision, decision)

    def test_surveillance_schedule_generation(self):
        """Test that a surveillance schedule is automatically generated."""
        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.cb_admin,
            decision="grant",
            decision_notes="Granting certification"
        )

        CertificateService.record_decision(decision)

        schedule = SurveillanceSchedule.objects.filter(certification=self.cert).first()
        self.assertIsNotNone(schedule)

        # Check dates (approximate)
        expected_surv1 = self.cert.issue_date + timedelta(days=365)
        self.assertEqual(schedule.surveillance_1_due_date, expected_surv1)
        self.assertEqual(schedule.cycle_end, self.cert.issue_date + timedelta(days=1095))


class ComplaintsAndAppealsTests(TestCase):
    """Test Complaints and Appeals logic (Clause 9.8)."""

    def setUp(self):
        self.user = User.objects.create_user(username="client_user", password="password")
        self.org = Organization.objects.create(name="Complaint Org", customer_id="C003", total_employee_count=20)

    def test_complaint_creation_service(self):
        """Test creating a complaint via service."""
        data = {
            "complainant_name": "John Doe",
            "complainant_email": "john@example.com",
            "organization": self.org,
            "complaint_type": "auditor_behavior",
            "description": "Auditor was rude."
        }

        complaint = ComplaintService.create_complaint(data, self.user)

        self.assertTrue(complaint.complaint_number.startswith("COMP-"))
        self.assertEqual(complaint.status, "received")
        self.assertEqual(complaint.submitted_by, self.user)

    def test_complaint_status_workflow(self):
        """Test updating complaint status."""
        complaint = Complaint.objects.create(
            complaint_number="COMP-TEST",
            complainant_name="Jane Doe",
            complaint_type="other",
            description="Test",
            submitted_by=self.user
        )

        updated_complaint = ComplaintService.update_complaint_status(
            complaint, "under_investigation", self.user, notes="Starting investigation"
        )

        self.assertEqual(updated_complaint.status, "under_investigation")
        self.assertEqual(updated_complaint.resolution_notes, "Starting investigation")

    def test_appeal_creation_service(self):
        """Test creating an appeal."""
        data = {
            "appellant_name": "John Doe",
            "grounds": "Disagree with decision"
        }

        appeal = ComplaintService.create_appeal(data, self.user)

        self.assertTrue(appeal.appeal_number.startswith("APP-"))
        self.assertEqual(appeal.status, "received")

    def test_appeal_decision(self):
        """Test recording an appeal decision."""
        appeal = Appeal.objects.create(
            appeal_number="APP-TEST",
            appellant_name="Jane Doe",
            grounds="Test",
            submitted_by=self.user
        )

        decided_appeal = ComplaintService.decide_appeal(
            appeal, "upheld", self.user, notes="Panel agrees with appellant"
        )

        self.assertEqual(decided_appeal.status, "closed")
        self.assertIn("Decision: upheld", decided_appeal.resolution_notes)

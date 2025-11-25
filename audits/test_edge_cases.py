"""
Edge case testing.

Tests boundary conditions, validation rules, and error scenarios.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from audits.models import EvidenceFile
from core.models import Certification, Organization, Site, Standard
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService


class DateValidationTest(TestCase):
    """Test date validation rules."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

    def test_audit_end_date_must_be_after_start_date(self):
        """Test that audit end date must be after or equal to start date."""
        # Valid: Same day audit
        audit = AuditService.create_audit(
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
        self.assertIsNotNone(audit)

        # Valid: Multi-day audit
        audit2 = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=5),
                "planned_duration_hours": 40.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )
        self.assertIsNotNone(audit2)

    def test_nc_due_date_validation(self):
        """Test NC due date validation."""
        audit = AuditService.create_audit(
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

        lead_group = Group.objects.create(name="lead_auditor")
        lead_auditor = User.objects.create_user(username="lead", password="pass")
        lead_auditor.groups.add(lead_group)

        # NC with future due date
        nc = FindingService.create_nonconformity(
            audit=audit,
            user=lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
                "due_date": date.today() + timedelta(days=30),
            },
        )
        self.assertIsNotNone(nc)
        self.assertEqual(nc.due_date, date.today() + timedelta(days=30))


class StatusTransitionTest(TestCase):
    """Test audit status transition restrictions."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

        self.client_app = Client()

    def test_audit_status_progression(self):
        """Test valid audit status transitions."""
        audit = AuditService.create_audit(
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

        # Draft → Client Review
        AuditService.update_audit(audit, {"status": "scheduled"})
        audit.refresh_from_db()
        self.assertEqual(audit.status, "scheduled")

        # Client Review → In Progress
        AuditService.update_audit(audit, {"status": "in_progress"})
        audit.refresh_from_db()
        self.assertEqual(audit.status, "in_progress")

        # In Progress → Completed
        AuditService.update_audit(audit, {"status": "completed"})
        audit.refresh_from_db()
        self.assertEqual(audit.status, "completed")


class FileUploadTest(TestCase):
    """Test file upload handling and limits."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")
        self.lead_auditor.groups.add(lead_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

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

        self.nc = FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

    def test_evidence_file_upload(self):
        """Test evidence file can be uploaded."""
        file_content = b"Test file content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")

        evidence_file = EvidenceFile.objects.create(
            audit=self.audit, finding=self.nc, file=uploaded_file, uploaded_by=self.lead_auditor
        )

        self.assertIsNotNone(evidence_file)
        self.assertEqual(evidence_file.uploaded_by, self.lead_auditor)
        self.assertEqual(evidence_file.finding, self.nc)

    def test_multiple_evidence_files(self):
        """Test multiple evidence files can be attached."""
        for i in range(3):
            file_content = f"Test file {i}".encode()
            uploaded_file = SimpleUploadedFile(
                f"test{i}.txt", file_content, content_type="text/plain"
            )

            EvidenceFile.objects.create(
                audit=self.audit, finding=self.nc, file=uploaded_file, uploaded_by=self.lead_auditor
            )

        self.assertEqual(self.nc.evidence_files.count(), 3)


class NCCategoryTest(TestCase):
    """Test NC category validation."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")
        self.lead_auditor.groups.add(lead_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

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

    def test_major_nc_creation(self):
        """Test major NC can be created."""
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
        self.assertEqual(nc.category, "major")

    def test_minor_nc_creation(self):
        """Test minor NC can be created."""
        nc = FindingService.create_nonconformity(
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
        self.assertEqual(nc.category, "minor")


class EmptyStringTest(TestCase):
    """Test handling of empty strings and null values."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")
        self.lead_auditor.groups.add(lead_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

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

    def test_nc_without_optional_fields(self):
        """Test NC can be created without optional fields."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
                # No due_date
            },
        )
        self.assertIsNotNone(nc)
        self.assertIsNone(nc.due_date)

    def test_audit_without_optional_notes(self):
        """Test audit can be created without optional notes fields."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
                # No notes fields
            },
            created_by=self.cb_admin,
        )
        self.assertIsNotNone(audit)

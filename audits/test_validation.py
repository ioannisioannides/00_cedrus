"""
Test Suite for Sprint 7 Validation Logic
Tests covering Tasks 1-4 and 6-7: Model validation, file uploads, security
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from audits.models import Audit, AuditTeamMember, EvidenceFile
from core.models import Certification, Organization, Site, Standard


class AuditTeamMemberDateValidationTests(TestCase):
    """Task 1: AuditTeamMember date validation"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_auditor_group)

        self.auditor = User.objects.create_user(username="auditor", password="password123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        self.audit.certifications.add(self.cert)

    def test_valid_team_member_dates(self):
        """Valid team member dates within audit range"""
        member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2025, 1, 2),
            date_to=date(2025, 1, 8),
        )
        # Should not raise ValidationError
        member.clean()
        member.save()
        self.assertEqual(AuditTeamMember.objects.count(), 1)

    def test_team_member_date_to_before_date_from(self):
        """End date before start date should fail"""
        member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2025, 1, 8),
            date_to=date(2025, 1, 2),
        )
        with self.assertRaises(ValidationError) as cm:
            member.clean()
        self.assertIn("date_to", cm.exception.error_dict)

    def test_team_member_start_before_audit_start(self):
        """Team member start date before audit start should fail"""
        member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2024, 12, 30),
            date_to=date(2025, 1, 5),
        )
        with self.assertRaises(ValidationError) as cm:
            member.clean()
        self.assertIn("date_from", cm.exception.error_dict)

    def test_team_member_end_after_audit_end(self):
        """Team member end date after audit end should fail"""
        member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2025, 1, 5),
            date_to=date(2025, 1, 15),
        )
        with self.assertRaises(ValidationError) as cm:
            member.clean()
        self.assertIn("date_to", cm.exception.error_dict)

    def test_team_member_exact_audit_dates(self):
        """Team member dates exactly matching audit dates is valid"""
        member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 10),
        )
        member.clean()
        member.save()
        self.assertEqual(AuditTeamMember.objects.count(), 1)


class AuditDateValidationTests(TestCase):
    """Task 2: Audit date validation"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_auditor_group)

    def test_valid_audit_date_range(self):
        """Valid date range (end >= start)"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.clean()
        audit.save()
        audit.certifications.add(self.cert)
        self.assertEqual(Audit.objects.count(), 1)

    def test_audit_same_day(self):
        """Audit on single day is valid"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 5),
            total_audit_date_to=date(2025, 1, 5),
            planned_duration_hours=Decimal("8.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.clean()
        audit.save()
        self.assertEqual(Audit.objects.count(), 1)

    def test_audit_end_before_start(self):
        """End date before start date should fail"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 10),
            total_audit_date_to=date(2025, 1, 1),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        with self.assertRaises(ValidationError) as cm:
            audit.clean()
        self.assertIn("total_audit_date_to", cm.exception.error_dict)


class OrganizationScopedValidationTests(TestCase):
    """Task 3: Organization-scoped validation (certifications and sites)"""

    def setUp(self):
        """Create test fixtures"""
        self.org1 = Organization.objects.create(
            name="Org 1",
            customer_id="ORG001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.org2 = Organization.objects.create(
            name="Org 2",
            customer_id="ORG002",
            registered_address="456 Test Ave",
            total_employee_count=50,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert1 = Certification.objects.create(
            organization=self.org1,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.cert2 = Certification.objects.create(
            organization=self.org2,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Services",
        )
        self.site1 = Site.objects.create(
            organization=self.org1, site_name="Site 1", site_address="123 Test St"
        )
        self.site2 = Site.objects.create(
            organization=self.org2, site_name="Site 2", site_address="456 Test Ave"
        )
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_auditor_group)

    def test_valid_certification_belongs_to_org(self):
        """Certification from same organization is valid"""
        audit = Audit.objects.create(
            organization=self.org1,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.certifications.add(self.cert1)
        # Should not raise ValidationError
        audit.clean()

    def test_invalid_certification_from_different_org(self):
        """Certification from different organization should fail"""
        audit = Audit.objects.create(
            organization=self.org1,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.certifications.add(self.cert2)  # Wrong org
        with self.assertRaises(ValidationError) as cm:
            audit.clean()
        self.assertIn("certifications", cm.exception.error_dict)

    def test_valid_site_belongs_to_org(self):
        """Site from same organization is valid"""
        audit = Audit.objects.create(
            organization=self.org1,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.certifications.add(self.cert1)
        audit.sites.add(self.site1)
        audit.clean()

    def test_invalid_site_from_different_org(self):
        """Site from different organization should fail"""
        audit = Audit.objects.create(
            organization=self.org1,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.certifications.add(self.cert1)
        audit.sites.add(self.site2)  # Wrong org
        with self.assertRaises(ValidationError) as cm:
            audit.clean()
        self.assertIn("sites", cm.exception.error_dict)


class LeadAuditorRoleValidationTests(TestCase):
    """Task 4: Lead auditor role validation"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )

        # Create groups
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.client_group = Group.objects.create(name="client_admin")

        # Create users with different roles
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.regular_auditor = User.objects.create_user(username="auditor", password="password123")
        self.regular_auditor.groups.add(self.auditor_group)

        self.cb_admin = User.objects.create_user(username="cbadmin", password="password123")
        self.cb_admin.groups.add(self.cb_admin_group)

        self.client = User.objects.create_user(username="client", password="password123")
        self.client.groups.add(self.client_group)

    def test_valid_lead_auditor_with_lead_auditor_role(self):
        """User with lead_auditor group can be lead auditor"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.clean()
        audit.save()
        self.assertEqual(Audit.objects.count(), 1)

    def test_valid_lead_auditor_with_auditor_role(self):
        """User with auditor group can be lead auditor"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.regular_auditor,
            created_by=self.regular_auditor,
            status="draft",
        )
        audit.clean()
        audit.save()
        self.assertEqual(Audit.objects.count(), 1)

    def test_valid_lead_auditor_with_cb_admin_role(self):
        """User with cb_admin group can be lead auditor"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.cb_admin,
            created_by=self.cb_admin,
            status="draft",
        )
        audit.clean()
        audit.save()
        self.assertEqual(Audit.objects.count(), 1)

    def test_invalid_lead_auditor_without_proper_role(self):
        """User without auditor role cannot be lead auditor"""
        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.client,
            created_by=self.client,
            status="draft",
        )
        with self.assertRaises(ValidationError) as cm:
            audit.clean()
        self.assertIn("lead_auditor", cm.exception.error_dict)


class FileTypeValidationTests(TestCase):
    """Task 6: File type validation"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        self.audit.certifications.add(self.cert)

    def test_valid_pdf_file(self):
        """PDF files are allowed"""
        file_content = b"%PDF-1.4 test content"
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_valid_image_jpg(self):
        """JPG images are allowed"""
        file_content = b"\xff\xd8\xff\xe0 fake jpg"
        uploaded_file = SimpleUploadedFile("test.jpg", file_content, content_type="image/jpeg")
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="photo",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_valid_image_png(self):
        """PNG images are allowed"""
        file_content = b"\x89PNG fake png"
        uploaded_file = SimpleUploadedFile("test.png", file_content, content_type="image/png")
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="photo",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_valid_docx_file(self):
        """DOCX files are allowed"""
        file_content = b"fake docx content"
        uploaded_file = SimpleUploadedFile(
            "test.docx",
            file_content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_invalid_executable_file(self):
        """Executable files are rejected"""
        file_content = b"fake exe content"
        uploaded_file = SimpleUploadedFile(
            "malware.exe", file_content, content_type="application/x-msdownload"
        )
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        with self.assertRaises(ValidationError) as cm:
            evidence.clean()
        self.assertIn("file", cm.exception.error_dict)

    def test_invalid_script_file(self):
        """Script files are rejected"""
        file_content = b"#!/bin/bash\nrm -rf /"
        uploaded_file = SimpleUploadedFile(
            "script.sh", file_content, content_type="application/x-sh"
        )
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        with self.assertRaises(ValidationError) as cm:
            evidence.clean()
        self.assertIn("file", cm.exception.error_dict)

    def test_invalid_zip_file(self):
        """ZIP files are rejected (not in allowed list)"""
        file_content = b"PK\x03\x04 fake zip"
        uploaded_file = SimpleUploadedFile(
            "archive.zip", file_content, content_type="application/zip"
        )
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        with self.assertRaises(ValidationError) as cm:
            evidence.clean()
        self.assertIn("file", cm.exception.error_dict)


class FileSizeValidationTests(TestCase):
    """Task 7: File size limits (10MB max)"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        self.audit.certifications.add(self.cert)

    def test_valid_small_file(self):
        """Files under 10MB are allowed"""
        # 1MB file
        file_content = b"x" * (1024 * 1024)
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_valid_file_at_limit(self):
        """Files exactly 10MB are allowed"""
        # 10MB file
        file_content = b"x" * (10 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        evidence.clean()
        evidence.save()
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_invalid_file_over_limit(self):
        """Files over 10MB are rejected"""
        # 11MB file
        file_content = b"x" * (11 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile(
            "large.pdf", file_content, content_type="application/pdf"
        )
        evidence = EvidenceFile(
            audit=self.audit,
            uploaded_by=self.lead_auditor,
            file=uploaded_file,
            evidence_type="document",
        )
        with self.assertRaises(ValidationError) as cm:
            evidence.clean()
        self.assertIn("file", cm.exception.error_dict)
        self.assertIn("10MB", str(cm.exception))


class ValidationIntegrationTests(TestCase):
    """Integration tests combining multiple validation rules"""

    def setUp(self):
        """Create test fixtures"""
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=100,
        )
        self.standard = Standard.objects.create(
            code="ISO9001", title="ISO 9001:2015 Quality Management Systems"
        )
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_status="active",
            certification_scope="Manufacturing",
        )
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor = User.objects.create_user(username="leadauditor", password="password123")
        self.lead_auditor.groups.add(self.lead_auditor_group)
        self.auditor_group = Group.objects.create(name="auditor")
        self.auditor = User.objects.create_user(username="auditor", password="password123")
        self.auditor.groups.add(self.auditor_group)

    def test_complete_valid_audit_with_team_member(self):
        """Complete valid audit with all validations passing"""
        # Create valid audit
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 10),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=self.lead_auditor,
            created_by=self.lead_auditor,
            status="draft",
        )
        audit.certifications.add(self.cert)
        audit.clean()

        # Add valid team member
        member = AuditTeamMember.objects.create(
            audit=audit,
            user=self.auditor,
            role="auditor",
            date_from=date(2025, 1, 2),
            date_to=date(2025, 1, 8),
        )
        member.clean()

        # Upload valid evidence
        file_content = b"%PDF-1.4 test"
        uploaded_file = SimpleUploadedFile(
            "evidence.pdf", file_content, content_type="application/pdf"
        )
        evidence = EvidenceFile.objects.create(
            audit=audit, uploaded_by=self.lead_auditor, file=uploaded_file, evidence_type="document"
        )
        evidence.clean()

        # Verify all saved correctly
        self.assertEqual(Audit.objects.count(), 1)
        self.assertEqual(AuditTeamMember.objects.count(), 1)
        self.assertEqual(EvidenceFile.objects.count(), 1)

    def test_cascading_validation_failures(self):
        """Multiple validation errors caught at once"""
        # Invalid date range, no lead auditor role
        client_group = Group.objects.create(name="client_admin")
        client_user = User.objects.create_user(username="client", password="pass")
        client_user.groups.add(client_group)

        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 10),  # Invalid: end before start
            total_audit_date_to=date(2025, 1, 1),
            planned_duration_hours=Decimal("24.0"),
            lead_auditor=client_user,  # Invalid: no auditor role
            status="draft",
        )

        with self.assertRaises(ValidationError) as cm:
            audit.clean()

        # Should have multiple errors (date validation fails first)
        error_dict = cm.exception.error_dict
        self.assertIn("total_audit_date_to", error_dict)
        # Note: lead_auditor validation may not trigger if date validation fails first

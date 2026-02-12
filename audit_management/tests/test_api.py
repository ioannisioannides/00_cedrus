"""
Tests for audit_management REST API ViewSets and Serializers.

Covers AuditProgram, Audit (with actions), Nonconformity, Observation,
OFI, AuditTeamMember, and EvidenceFile endpoints.
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from audit_management.models import (
    Audit,
    AuditProgram,
    AuditTeamMember,
    EvidenceFile,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
)
from core.models import Certification, Organization, Site, Standard


class AuditAPITestBase(TestCase):
    """Shared setup for audit management API tests."""

    def setUp(self):
        self.client = APIClient()

        # Groups
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.auditor_group = Group.objects.create(name="auditor")
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")

        # Users
        self.admin_user = User.objects.create_user(username="admin", password="pass", email="admin@cb.com")
        self.admin_user.groups.add(self.cb_admin_group)

        self.auditor_user = User.objects.create_user(username="auditor", password="pass", email="auditor@cb.com")
        self.auditor_user.groups.add(self.auditor_group)

        self.lead_auditor_user = User.objects.create_user(username="lead", password="pass", email="lead@cb.com")
        self.lead_auditor_user.groups.add(self.lead_auditor_group)

        self.regular_user = User.objects.create_user(username="regular", password="pass")

        # Core data
        self.org = Organization.objects.create(
            name="Test Org", customer_id="ORG001", total_employee_count=50, registered_address="addr"
        )
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT-001",
            issue_date=date(2025, 1, 1),
            expiry_date=date(2028, 1, 1),
        )
        self.site = Site.objects.create(organization=self.org, site_name="HQ", site_address="addr")

        # Audit data
        self.program = AuditProgram.objects.create(
            organization=self.org,
            title="2025 Program",
            year=2025,
            objectives="Quality objectives",
            risks_opportunities="Risks",
            created_by=self.admin_user,
        )
        self.audit = Audit.objects.create(
            program=self.program,
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 3, 1),
            total_audit_date_to=date(2025, 3, 5),
            created_by=self.admin_user,
            lead_auditor=self.lead_auditor_user,
        )


class TestIsAuditorOrAdminPermission(AuditAPITestBase):
    """Test the IsAuditorOrAdmin permission class."""

    def test_unauthenticated_denied(self):
        response = self.client.get("/api/v1/audit-management/audits/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_can_read(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/audits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            "/api/v1/audit-management/programs/",
            {
                "organization": self.org.pk,
                "title": "Test",
                "year": 2026,
                "objectives": "obj",
                "risks_opportunities": "risk",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_auditor_can_create(self):
        self.client.force_authenticate(user=self.auditor_user)
        response = self.client.post(
            "/api/v1/audit-management/programs/",
            {
                "organization": self.org.pk,
                "title": "Auditor Program",
                "year": 2026,
                "objectives": "obj",
                "risks_opportunities": "risk",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_lead_auditor_can_create(self):
        self.client.force_authenticate(user=self.lead_auditor_user)
        response = self.client.post(
            "/api/v1/audit-management/programs/",
            {
                "organization": self.org.pk,
                "title": "Lead Program",
                "year": 2026,
                "objectives": "obj",
                "risks_opportunities": "risk",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestAuditProgramViewSet(AuditAPITestBase):
    """Test AuditProgram API endpoints."""

    def test_list_programs(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/programs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_organization(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/programs/?organization={self.org.pk}")
        self.assertEqual(len(response.data), 1)

    def test_filter_by_year(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/programs/?year=2025")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/audit-management/programs/?year=2099")
        self.assertEqual(len(response.data), 0)

    def test_create_sets_created_by(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/v1/audit-management/programs/",
            {
                "organization": self.org.pk,
                "title": "New",
                "year": 2026,
                "objectives": "obj",
                "risks_opportunities": "risk",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        program = AuditProgram.objects.get(pk=response.data["id"])
        self.assertEqual(program.created_by, self.admin_user)

    def test_retrieve_program(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/programs/{self.program.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "2025 Program")
        self.assertEqual(response.data["organization_name"], "Test Org")


class TestAuditViewSet(AuditAPITestBase):
    """Test Audit API endpoints."""

    def test_list_audits(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/audits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_uses_lightweight_serializer(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/audits/")
        # List serializer should NOT include nested findings
        self.assertNotIn("nonconformities", response.data[0])

    def test_filter_by_organization(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/?organization={self.org.pk}")
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/audits/?status=draft")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/audit-management/audits/?status=closed")
        self.assertEqual(len(response.data), 0)

    def test_filter_by_audit_type(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/audits/?audit_type=stage1")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/audit-management/audits/?audit_type=surveillance")
        self.assertEqual(len(response.data), 0)

    def test_retrieve_audit_detail(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/{self.audit.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["audit_type"], "stage1")
        self.assertIn("nonconformities", response.data)
        self.assertIn("observations", response.data)
        self.assertIn("ofis", response.data)
        self.assertIn("nc_count", response.data)
        self.assertIn("open_nc_count", response.data)

    def test_create_audit(self):
        self.client.force_authenticate(user=self.admin_user)
        count_before = Audit.objects.count()
        response = self.client.post(
            "/api/v1/audit-management/audits/",
            {
                "organization": self.org.pk,
                "audit_type": "surveillance",
                "total_audit_date_from": "2025-06-01",
                "total_audit_date_to": "2025-06-05",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Audit.objects.count(), count_before + 1)
        audit = Audit.objects.latest("pk")
        self.assertEqual(audit.created_by, self.admin_user)

    def test_findings_action(self):
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="evidence",
            statement_of_nc="statement",
            auditor_explanation="explanation",
            created_by=self.admin_user,
        )
        Observation.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="5.1",
            statement="obs statement",
            created_by=self.admin_user,
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/{self.audit.pk}/findings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["nonconformities"]), 1)
        self.assertEqual(len(response.data["observations"]), 1)
        self.assertEqual(len(response.data["ofis"]), 0)

    def test_team_action(self):
        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.lead_auditor_user,
            name="Lead",
            role="lead_auditor",
            date_from=date(2025, 3, 1),
            date_to=date(2025, 3, 5),
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/{self.audit.pk}/team/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_evidence_action(self):
        EvidenceFile.objects.create(
            audit=self.audit,
            uploaded_by=self.admin_user,
            file=SimpleUploadedFile("test.pdf", b"content"),
            evidence_type="document",
            description="Test evidence",
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/{self.audit.pk}/evidence/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_transition_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f"/api/v1/audit-management/audits/{self.audit.pk}/transition/",
            {"status": "scheduled"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["previous_status"], "draft")
        self.assertEqual(response.data["new_status"], "scheduled")
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "scheduled")

    def test_transition_missing_status(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f"/api/v1/audit-management/audits/{self.audit.pk}/transition/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_transition_invalid_status(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f"/api/v1/audit-management/audits/{self.audit.pk}/transition/",
            {"status": "nonexistent_status"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestNonconformityViewSet(AuditAPITestBase):
    """Test Nonconformity API endpoints."""

    def setUp(self):
        super().setUp()
        self.nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="evidence",
            statement_of_nc="statement",
            auditor_explanation="explanation",
            created_by=self.admin_user,
        )

    def test_list_nonconformities(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/nonconformities/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_audit(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/nonconformities/?audit={self.audit.pk}")
        self.assertEqual(len(response.data), 1)

    def test_filter_by_verification_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/nonconformities/?verification_status=open")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/audit-management/nonconformities/?verification_status=closed")
        self.assertEqual(len(response.data), 0)

    def test_create_nc(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/v1/audit-management/nonconformities/",
            {
                "audit": self.audit.pk,
                "standard": self.standard.pk,
                "clause": "7.1",
                "category": "minor",
                "objective_evidence": "ev",
                "statement_of_nc": "st",
                "auditor_explanation": "exp",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        nc = Nonconformity.objects.get(pk=response.data["id"])
        self.assertEqual(nc.created_by, self.admin_user)

    def test_retrieve_nc(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/nonconformities/{self.nc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["category"], "major")
        self.assertIn("standard_code", response.data)


class TestObservationViewSet(AuditAPITestBase):
    """Test Observation API endpoints."""

    def setUp(self):
        super().setUp()
        self.obs = Observation.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="5.1",
            statement="Observation statement",
            created_by=self.admin_user,
        )

    def test_list_observations(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/observations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_audit(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/observations/?audit={self.audit.pk}")
        self.assertEqual(len(response.data), 1)

    def test_create_observation(self):
        self.client.force_authenticate(user=self.auditor_user)
        response = self.client.post(
            "/api/v1/audit-management/observations/",
            {
                "audit": self.audit.pk,
                "clause": "6.1",
                "statement": "new obs",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obs = Observation.objects.get(pk=response.data["id"])
        self.assertEqual(obs.created_by, self.auditor_user)


class TestOFIViewSet(AuditAPITestBase):
    """Test OFI API endpoints."""

    def setUp(self):
        super().setUp()
        self.ofi = OpportunityForImprovement.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="8.1",
            description="Improvement suggestion",
            created_by=self.admin_user,
        )

    def test_list_ofis(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/ofis/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_audit(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/ofis/?audit={self.audit.pk}")
        self.assertEqual(len(response.data), 1)

    def test_create_ofi(self):
        self.client.force_authenticate(user=self.auditor_user)
        response = self.client.post(
            "/api/v1/audit-management/ofis/",
            {
                "audit": self.audit.pk,
                "clause": "9.1",
                "description": "new ofi",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ofi = OpportunityForImprovement.objects.get(pk=response.data["id"])
        self.assertEqual(ofi.created_by, self.auditor_user)


class TestAuditTeamMemberViewSet(AuditAPITestBase):
    """Test AuditTeamMember API endpoints."""

    def setUp(self):
        super().setUp()
        self.member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.lead_auditor_user,
            name="Lead Auditor",
            role="lead_auditor",
            date_from=date(2025, 3, 1),
            date_to=date(2025, 3, 5),
        )

    def test_list_team_members(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/team-members/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_audit(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/team-members/?audit={self.audit.pk}")
        self.assertEqual(len(response.data), 1)


class TestEvidenceFileViewSet(AuditAPITestBase):
    """Test EvidenceFile API endpoints."""

    def setUp(self):
        super().setUp()
        self.evidence = EvidenceFile.objects.create(
            audit=self.audit,
            uploaded_by=self.admin_user,
            file=SimpleUploadedFile("evidence.pdf", b"content"),
            evidence_type="document",
            description="Test file",
        )

    def test_list_evidence(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/audit-management/evidence/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_audit(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/evidence/?audit={self.audit.pk}")
        self.assertEqual(len(response.data), 1)

    def test_evidence_includes_uploaded_by_name(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/evidence/{self.evidence.pk}/")
        self.assertIn("uploaded_by_name", response.data)


class TestAuditDetailSerializerFields(AuditAPITestBase):
    """Test AuditDetailSerializer computed fields."""

    def test_nc_count_and_open_nc_count(self):
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
            verification_status="open",
        )
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.2",
            category="minor",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
            verification_status="closed",
        )
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/audit-management/audits/{self.audit.pk}/")
        self.assertEqual(response.data["nc_count"], 2)
        self.assertEqual(response.data["open_nc_count"], 1)

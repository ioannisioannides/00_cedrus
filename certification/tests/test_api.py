"""
Tests for certification REST API ViewSets and Serializers.

Covers Complaint, Appeal, CertificationDecision, TechnicalReview,
and TransferCertification endpoints.
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from audit_management.models import Audit, AuditProgram
from certification.models import Appeal, CertificationDecision, Complaint, TechnicalReview, TransferCertification
from core.models import Certification, Organization, Standard


class CertificationAPITestBase(TestCase):
    """Shared setup for certification API tests."""

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

        self.regular_user = User.objects.create_user(username="regular", password="pass")

        self.decision_maker = User.objects.create_user(username="decision_maker", password="pass", email="dm@cb.com")
        self.decision_maker.groups.add(self.cb_admin_group)

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

        # Audit (needed for decisions and reviews)
        self.program = AuditProgram.objects.create(
            organization=self.org,
            title="2025",
            year=2025,
            objectives="obj",
            risks_opportunities="risk",
            created_by=self.admin_user,
        )
        self.audit = Audit.objects.create(
            program=self.program,
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 3, 1),
            total_audit_date_to=date(2025, 3, 5),
            created_by=self.admin_user,
            lead_auditor=self.auditor_user,
        )

        # Complaint
        self.complaint = Complaint.objects.create(
            complaint_number="COMP-001",
            organization=self.org,
            complainant_name="John Doe",
            complaint_type="audit_conduct",
            description="Test complaint",
            submitted_by=self.admin_user,
        )


class TestIsCBStaffPermission(CertificationAPITestBase):
    """Test the IsCBStaff permission class."""

    def test_unauthenticated_denied(self):
        response = self.client.get("/api/v1/certification/complaints/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_can_read(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/complaints/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_write(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            "/api/v1/certification/complaints/",
            {
                "complaint_number": "COMP-002",
                "complainant_name": "Jane",
                "complaint_type": "other",
                "description": "desc",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cb_admin_can_write(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/v1/certification/complaints/",
            {
                "complaint_number": "COMP-002",
                "complainant_name": "Jane",
                "complaint_type": "other",
                "description": "desc",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_auditor_can_write(self):
        self.client.force_authenticate(user=self.auditor_user)
        response = self.client.post(
            "/api/v1/certification/complaints/",
            {
                "complaint_number": "COMP-003",
                "complainant_name": "Bob",
                "complaint_type": "other",
                "description": "desc",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestComplaintViewSet(CertificationAPITestBase):
    """Test Complaint API endpoints."""

    def test_list_complaints(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/complaints/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_uses_lightweight_serializer(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/complaints/")
        # List serializer has limited fields
        self.assertIn("complaint_number", response.data[0])
        self.assertNotIn("investigation_notes", response.data[0])

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/complaints/?status=received")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/certification/complaints/?status=closed")
        self.assertEqual(len(response.data), 0)

    def test_filter_by_organization(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/complaints/?organization={self.org.pk}")
        self.assertEqual(len(response.data), 1)

    def test_retrieve_complaint_detail(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/complaints/{self.complaint.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["complaint_number"], "COMP-001")
        self.assertIn("organization_name", response.data)
        self.assertIn("submitted_by_name", response.data)
        self.assertIn("investigation_notes", response.data)

    def test_create_sets_submitted_by(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/v1/certification/complaints/",
            {
                "complaint_number": "COMP-010",
                "complainant_name": "Test",
                "complaint_type": "other",
                "description": "desc",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint = Complaint.objects.get(pk=response.data["id"])
        self.assertEqual(complaint.submitted_by, self.admin_user)


class TestAppealViewSet(CertificationAPITestBase):
    """Test Appeal API endpoints."""

    def setUp(self):
        super().setUp()
        self.appeal = Appeal.objects.create(
            appeal_number="APP-001",
            related_complaint=self.complaint,
            appellant_name="Jane",
            grounds="Unfair decision",
            submitted_by=self.admin_user,
        )

    def test_list_appeals(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/appeals/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/appeals/?status=received")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/certification/appeals/?status=decided")
        self.assertEqual(len(response.data), 0)

    def test_create_appeal(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/api/v1/certification/appeals/",
            {
                "appeal_number": "APP-002",
                "appellant_name": "Bob",
                "grounds": "Grounds for appeal",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        appeal = Appeal.objects.get(pk=response.data["id"])
        self.assertEqual(appeal.submitted_by, self.admin_user)

    def test_retrieve_appeal(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/appeals/{self.appeal.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["appeal_number"], "APP-001")


class TestCertificationDecisionViewSet(CertificationAPITestBase):
    """Test CertificationDecision API endpoints."""

    def setUp(self):
        super().setUp()
        self.decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.decision_maker,
            decision="grant",
            decision_notes="All good",
        )

    def test_list_decisions(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_decision(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/decisions/?decision=grant")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/certification/decisions/?decision=refuse")
        self.assertEqual(len(response.data), 0)

    def test_retrieve_decision(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/decisions/{self.decision.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["decision"], "grant")
        self.assertIn("decision_maker_name", response.data)
        self.assertIn("audit_display", response.data)


class TestTechnicalReviewViewSet(CertificationAPITestBase):
    """Test TechnicalReview API endpoints."""

    def setUp(self):
        super().setUp()
        # Need a separate audit since TechnicalReview is OneToOne
        self.audit2 = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=date(2025, 6, 1),
            total_audit_date_to=date(2025, 6, 3),
            created_by=self.admin_user,
        )
        self.review = TechnicalReview.objects.create(
            audit=self.audit2,
            reviewer=self.admin_user,
            status="pending",
            scope_verified=True,
        )

    def test_list_reviews(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/technical-reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/technical-reviews/?status=pending")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/certification/technical-reviews/?status=approved")
        self.assertEqual(len(response.data), 0)

    def test_retrieve_review(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/technical-reviews/{self.review.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reviewer_name", response.data)
        self.assertEqual(response.data["scope_verified"], True)


class TestTransferCertificationViewSet(CertificationAPITestBase):
    """Test TransferCertification API endpoints."""

    def setUp(self):
        super().setUp()
        self.transfer_audit = Audit.objects.create(
            organization=self.org,
            audit_type="transfer",
            total_audit_date_from=date(2025, 7, 1),
            total_audit_date_to=date(2025, 7, 3),
            created_by=self.admin_user,
        )
        self.transfer = TransferCertification.objects.create(
            transfer_audit=self.transfer_audit,
            previous_cb_name="Old CB Ltd",
            previous_certificate_expiry_date=date(2025, 12, 31),
        )

    def test_list_transfers(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certification/transfers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_transfer(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certification/transfers/{self.transfer.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["previous_cb_name"], "Old CB Ltd")

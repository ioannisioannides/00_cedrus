from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase

from audit_management.api.views.audit import AuditCreateView, AuditDetailView, AuditUpdateView
from audit_management.application.schemas import AuditCreateDTO, AuditUpdateDTO
from audit_management.models import Audit, AuditProgram
from core.models import Certification, Organization, Site, Standard


class AuditViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="cb_admin", password="password")
        group = Group.objects.create(name="cb_admin")
        self.user.groups.add(group)

        self.organization = Organization.objects.create(name="Test Org", customer_id="ORG001", total_employee_count=10)
        self.standard = Standard.objects.create(title="ISO 9001", code="ISO9001")
        self.certification = Certification.objects.create(
            organization=self.organization,
            standard=self.standard,
            certificate_id="CERT001",
            issue_date=date.today(),
            expiry_date=date.today(),
        )
        self.site = Site.objects.create(organization=self.organization, site_name="HQ", site_address="123 Main St")
        self.program = AuditProgram.objects.create(
            organization=self.organization, title="2025 Program", year=2025, created_by=self.user
        )

    @patch("audit_management.api.views.audit.AuditService")
    def test_create_audit_view(self, MockAuditService):
        """Test that AuditCreateView calls AuditService.create_audit with correct DTO."""

        # Mock the service return value
        mock_audit = MagicMock(spec=Audit)
        mock_audit.pk = 1
        MockAuditService.create_audit.return_value = mock_audit

        data = {
            "organization": self.organization.id,
            "program": self.program.id,
            "certifications": [self.certification.id],
            "sites": [self.site.id],
            "audit_type": "stage1",
            "total_audit_date_from": "2025-01-01",
            "total_audit_date_to": "2025-01-05",
            "planned_duration_hours": 8.0,
            "lead_auditor": self.user.id,
            "status": "draft",
        }

        request = self.factory.post("/audits/create/", data)
        request.user = self.user

        view = AuditCreateView.as_view()

        # Mock get_success_url to avoid NoReverseMatch
        with patch.object(AuditCreateView, "get_success_url", return_value="/audits/1/"):
            response = view(request)

        self.assertEqual(response.status_code, 302)  # Redirects on success

        # Verify service call
        self.assertTrue(MockAuditService.create_audit.called)
        call_args = MockAuditService.create_audit.call_args
        self.assertIsNotNone(call_args)

        # Check arguments
        kwargs = call_args.kwargs
        self.assertIn("data", kwargs)
        self.assertIn("created_by", kwargs)

        dto = kwargs["data"]
        self.assertIsInstance(dto, AuditCreateDTO)
        self.assertEqual(dto.organization_id, self.organization.id)
        self.assertEqual(dto.program_id, self.program.id)
        self.assertEqual(dto.audit_type, "stage1")

    @patch("audit_management.api.views.audit.AuditService")
    def test_update_audit_view(self, MockAuditService):
        """Test that AuditUpdateView calls AuditService.update_audit with correct DTO."""

        # Create a completed Stage 1 audit to satisfy validation
        Audit.objects.create(
            organization=self.organization,
            audit_type="stage1",
            status="closed",
            total_audit_date_from=date(2024, 1, 1),
            total_audit_date_to=date(2024, 1, 5),
            created_by=self.user,
        )

        audit = Audit.objects.create(
            organization=self.organization,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 5),
            created_by=self.user,
        )

        # Mock the service return value
        MockAuditService.update_audit.return_value = audit

        data = {
            "organization": self.organization.id,
            "program": self.program.id,
            "certifications": [self.certification.id],
            "sites": [self.site.id],
            "audit_type": "stage2",  # Changed
            "total_audit_date_from": "2025-02-01",
            "total_audit_date_to": "2025-02-05",
            "planned_duration_hours": 16.0,
            "lead_auditor": self.user.id,
        }

        request = self.factory.post(f"/audits/{audit.pk}/edit/", data)
        request.user = self.user

        view = AuditUpdateView.as_view()

        # Mock get_success_url
        with patch.object(AuditUpdateView, "get_success_url", return_value=f"/audits/{audit.pk}/"):
            response = view(request, pk=audit.pk)

        if response.status_code == 200:
            print(response.context_data["form"].errors)

        self.assertEqual(response.status_code, 302)

        # Verify service call
        self.assertTrue(MockAuditService.update_audit.called)
        call_args = MockAuditService.update_audit.call_args

        kwargs = call_args.kwargs
        self.assertIn("data", kwargs)

        dto = kwargs["data"]
        self.assertIsInstance(dto, AuditUpdateDTO)
        self.assertEqual(dto.audit_type, "stage2")

    @patch("audit_management.api.views.audit.AuditService")
    def test_detail_audit_view(self, MockAuditService):
        """Test that AuditDetailView calls AuditService.get_available_transitions."""

        audit = Audit.objects.create(
            organization=self.organization,
            audit_type="stage1",
            total_audit_date_from=date(2025, 1, 1),
            total_audit_date_to=date(2025, 1, 5),
            created_by=self.user,
        )

        # Mock service methods
        MockAuditService.get_available_transitions.return_value = []

        request = self.factory.get(f"/audits/{audit.pk}/")
        request.user = self.user

        view = AuditDetailView.as_view()
        response = view(request, pk=audit.pk)

        self.assertEqual(response.status_code, 200)

        # Verify service call
        self.assertTrue(MockAuditService.get_available_transitions.called)
        MockAuditService.get_available_transitions.assert_called_with(audit, self.user)

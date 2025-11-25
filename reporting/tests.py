from django.contrib.auth.models import Group, Permission, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from audits.models import Audit
from core.models import Certification, Organization, Site, Standard


class ReportingViewTests(TestCase):
    def setUp(self):
        # Create user with permissions
        self.user = User.objects.create_user(username='auditor', password='password')
        permission = Permission.objects.get(codename='view_audit')
        self.user.user_permissions.add(permission)
        self.client = Client()
        self.client.login(username='auditor', password='password')

        # Create test data
        self.org = Organization.objects.create(
            name="Test Org",
            total_employee_count=100
        )
        self.standard = Standard.objects.create(title="ISO 9001", code="ISO 9001:2015")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT-001",
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
            certificate_status="active"
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Main St"
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=timezone.now().date(),
            total_audit_date_to=timezone.now().date(),
            lead_auditor=self.user,
            created_by=self.user
        )
        self.audit.certifications.add(self.cert)
        self.audit.sites.add(self.site)

    def test_audit_report_pdf_generation(self):
        url = reverse('reporting:audit_report_pdf', args=[self.audit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.has_header('Content-Disposition'))

    def test_certificate_pdf_generation(self):
        url = reverse('reporting:certificate_pdf', args=[self.audit.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.has_header('Content-Disposition'))

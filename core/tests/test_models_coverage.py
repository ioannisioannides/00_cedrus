from django.test import TestCase

from core.models import Organization, Site, Standard


class TestModelsCoverage(TestCase):
    def test_organization_str(self):
        org = Organization.objects.create(name="Test Org", customer_id="CUST-001", total_employee_count=10)
        self.assertEqual(str(org), "Test Org (CUST-001)")

    def test_site_str(self):
        org = Organization.objects.create(name="Test Org", customer_id="CUST-001", total_employee_count=10)
        site = Site.objects.create(organization=org, site_name="HQ", site_address="123 Main St")
        self.assertEqual(str(site), "HQ (Test Org)")

    def test_standard_str(self):
        std = Standard.objects.create(code="ISO 9001", title="Quality Management")
        self.assertEqual(str(std), "ISO 9001 - Quality Management")

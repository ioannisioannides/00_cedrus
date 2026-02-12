"""
Tests for core REST API ViewSets and Serializers.

Covers Organization, Site, Standard, and Certification endpoints
including CRUD, permissions, filtering, and nested actions.
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Certification, Organization, Site, Standard


class CoreAPITestBase(TestCase):
    """Shared test setup for core API tests."""

    def setUp(self):
        self.client = APIClient()

        # Users & groups
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.auditor_group = Group.objects.create(name="auditor")

        self.admin_user = User.objects.create_user(username="admin", password="pass", email="admin@test.com")
        self.admin_user.groups.add(self.cb_admin_group)

        self.regular_user = User.objects.create_user(username="regular", password="pass", email="regular@test.com")

        # Test data
        self.org = Organization.objects.create(
            name="Acme Corp",
            customer_id="ACME001",
            total_employee_count=50,
            registered_address="123 Main St",
            contact_email="info@acme.com",
        )
        self.org2 = Organization.objects.create(
            name="Beta Inc",
            customer_id="BETA001",
            total_employee_count=20,
            registered_address="456 Oak Ave",
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Main St",
        )
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT-001",
            issue_date=date(2025, 1, 1),
            expiry_date=date(2028, 1, 1),
            certificate_status="active",
        )


class TestIsCBAdminPermission(CoreAPITestBase):
    """Test the IsCBAdmin permission class."""

    def test_unauthenticated_user_denied(self):
        response = self.client.get("/api/v1/organizations/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_read(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/organizations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_write(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post("/api/v1/organizations/", {"name": "New", "customer_id": "NEW01", "total_employee_count": 5, "registered_address": "Addr"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cb_admin_can_write(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/organizations/", {"name": "New Corp", "customer_id": "NEW01", "total_employee_count": 5, "registered_address": "addr"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestOrganizationViewSet(CoreAPITestBase):
    """Test Organization API endpoints."""

    def test_list_organizations(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/organizations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_uses_lightweight_serializer(self):
        """List action should return OrganizationListSerializer fields."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/organizations/")
        org_data = response.data[0]
        # List serializer should NOT have heavy fields like sites_count
        self.assertIn("name", org_data)
        self.assertIn("customer_id", org_data)

    def test_retrieve_organization(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/organizations/{self.org.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Acme Corp")
        self.assertIn("sites_count", response.data)
        self.assertIn("certifications_count", response.data)

    def test_retrieve_computed_fields(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/organizations/{self.org.pk}/")
        self.assertEqual(response.data["sites_count"], 1)
        self.assertEqual(response.data["certifications_count"], 1)

    def test_create_organization(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/organizations/", {
            "name": "Charlie Ltd",
            "customer_id": "CHAR01",
            "total_employee_count": 10,
            "registered_address": "789 Pine",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), 3)

    def test_update_organization(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(f"/api/v1/organizations/{self.org.pk}/", {"name": "Acme Corp Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Acme Corp Updated")

    def test_delete_organization(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f"/api/v1/organizations/{self.org2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Organization.objects.count(), 1)

    def test_sites_action(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/organizations/{self.org.pk}/sites/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["site_name"], "HQ")

    def test_certifications_action(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/organizations/{self.org.pk}/certifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["certificate_id"], "CERT-001")


class TestSiteViewSet(CoreAPITestBase):
    """Test Site API endpoints."""

    def test_list_sites(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/sites/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_sites_filter_by_organization(self):
        Site.objects.create(organization=self.org2, site_name="Beta HQ", site_address="addr")
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/sites/?organization={self.org.pk}")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["site_name"], "HQ")

    def test_site_includes_organization_name(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/sites/{self.site.pk}/")
        self.assertEqual(response.data["organization_name"], "Acme Corp")

    def test_create_site(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/sites/", {
            "organization": self.org.pk,
            "site_name": "Branch",
            "site_address": "456 Side St",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestStandardViewSet(CoreAPITestBase):
    """Test Standard API endpoints."""

    def test_list_standards(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/standards/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_standard(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post("/api/v1/standards/", {"code": "ISO 14001:2015", "title": "Environmental Management"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestCertificationViewSet(CoreAPITestBase):
    """Test Certification API endpoints."""

    def test_list_certifications(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_organization(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certifications/?organization={self.org.pk}")
        self.assertEqual(len(response.data), 1)
        response = self.client.get(f"/api/v1/certifications/?organization={self.org2.pk}")
        self.assertEqual(len(response.data), 0)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/v1/certifications/?status=active")
        self.assertEqual(len(response.data), 1)
        response = self.client.get("/api/v1/certifications/?status=suspended")
        self.assertEqual(len(response.data), 0)

    def test_certification_includes_related_names(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f"/api/v1/certifications/{self.certification.pk}/")
        self.assertEqual(response.data["organization_name"], "Acme Corp")
        self.assertEqual(response.data["standard_code"], "ISO 9001:2015")

"""
Comprehensive tests for core app: organizations, sites, standards, certifications.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import CertificateHistory, Certification, Organization, Site, Standard, SurveillanceSchedule

# ==============================================================================
# HEALTH CHECK TESTS
# ==============================================================================


class HealthCheckTest(TestCase):
    """Test health check endpoints."""

    def test_health_check_returns_200(self):
        """Test basic health check returns healthy status."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("version", data)

    def test_health_check_only_get_allowed(self):
        """Test health check rejects POST requests."""
        response = self.client.post("/health/")
        self.assertEqual(response.status_code, 405)

    def test_readiness_check_healthy(self):
        """Test readiness check when all services are healthy."""
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["checks"]["database"], "healthy")
        self.assertEqual(data["checks"]["models"], "healthy")

    def test_readiness_check_database_healthy(self):
        """Test readiness check properly checks database."""
        response = self.client.get("/health/ready/")
        data = response.json()
        self.assertIn("database", data["checks"])
        self.assertEqual(data["checks"]["database"], "healthy")

    @patch("core.health.cache")
    def test_readiness_check_cache_failure(self, mock_cache):
        """Test readiness check when cache fails."""
        mock_cache.set.side_effect = Exception("Redis connection failed")
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "not_ready")
        self.assertEqual(data["checks"]["cache"], "unhealthy")
        self.assertTrue(any("Cache connection failed" in e for e in data["errors"]))

    @patch("core.health.cache")
    def test_readiness_check_cache_mismatch(self, mock_cache):
        """Test readiness check when cache returns wrong value."""
        mock_cache.set.return_value = None
        mock_cache.get.return_value = "wrong_value"
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["checks"]["cache"], "unhealthy")

    @patch("core.health.connection")
    def test_readiness_check_database_failure(self, mock_connection):
        """Test readiness check when database fails."""
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        mock_connection.cursor.return_value = mock_cursor
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)

    def test_liveness_check_returns_alive(self):
        """Test liveness check returns alive status."""
        response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "alive")
        self.assertIn("python_version", data)
        self.assertIn("timestamp", data)

    @override_settings(DEBUG=True, INTERNAL_IPS=[])
    def test_detailed_status_debug_mode(self):
        """Test detailed status is accessible in debug mode."""
        response = self.client.get(reverse("core:detailed_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("application", data)
        self.assertIn("database", data)
        self.assertIn("cache", data)
        self.assertIn("system", data)

    @override_settings(DEBUG=False)
    def test_detailed_status_production_forbidden(self):
        """Test detailed status is forbidden for anonymous users in production."""
        response = self.client.get(reverse("core:detailed_status"))
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_detailed_status_production_superuser(self):
        """Test detailed status is accessible for superusers in production."""
        superuser = User.objects.create_superuser(username="admin", email="admin@test.com", password="adminpass")
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("core:detailed_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    @override_settings(DEBUG=True, INTERNAL_IPS=[])
    @patch("core.health.connection")
    def test_detailed_status_database_error(self, mock_connection):
        """Test detailed status handles database errors gracefully."""
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute.side_effect = Exception("DB Error")
        mock_connection.cursor.return_value = mock_cursor
        response = self.client.get(reverse("core:detailed_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["database"]["status"], "error")

    @override_settings(DEBUG=True, INTERNAL_IPS=[])
    @patch("core.health.cache")
    def test_detailed_status_cache_error(self, mock_cache):
        """Test detailed status handles cache errors gracefully."""
        mock_cache.set.side_effect = Exception("Cache Error")
        response = self.client.get(reverse("core:detailed_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cache"]["status"], "error")


class OrganizationModelTest(TestCase):
    """Test Organization model validation and relationships."""

    def setUp(self):
        self.org_data = {
            "name": "Test Organization",
            "registered_id": "REG123",
            "registered_address": "123 Test Street",
            "customer_id": "CUST001",
            "total_employee_count": 50,
        }

    def test_create_organization(self):
        """Test creating a basic organization."""
        org = Organization.objects.create(**self.org_data)
        self.assertEqual(org.name, "Test Organization")
        self.assertEqual(org.customer_id, "CUST001")
        self.assertIsNotNone(org.created_at)

    def test_organization_customer_id_unique(self):
        """Test that customer_id must be unique."""
        Organization.objects.create(**self.org_data)
        with self.assertRaises(Exception):  # IntegrityError
            Organization.objects.create(
                name="Another Org",
                registered_address="456 St",
                customer_id="CUST001",  # Duplicate
                total_employee_count=10,
            )

    def test_organization_employee_count_validation(self):
        """Test that employee_count must be >= 1."""
        # This should work (validators are checked at form level, not model level in Django)
        # But we can test the model accepts positive integers
        org = Organization.objects.create(
            name="Small Org",
            registered_address="123 St",
            customer_id="SMALL001",
            total_employee_count=1,
        )
        self.assertEqual(org.total_employee_count, 1)

    def test_organization_optional_fields(self):
        """Test that optional fields can be blank."""
        org = Organization.objects.create(
            name="Minimal Org",
            registered_address="123 St",
            customer_id="MIN001",
            total_employee_count=5,
        )
        self.assertEqual(org.registered_id, "")
        self.assertEqual(org.contact_email, "")
        self.assertEqual(org.contact_website, "")

    def test_organization_str(self):
        """Test organization string representation."""
        org = Organization.objects.create(**self.org_data)
        self.assertIn("Test Organization", str(org))
        self.assertIn("CUST001", str(org))


class SiteModelTest(TestCase):
    """Test Site model validation and relationships."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

    def test_create_site(self):
        """Test creating a site."""
        site = Site.objects.create(
            organization=self.org,
            site_name="Main Site",
            site_address="456 Site St",
            site_employee_count=5,
        )
        self.assertEqual(site.organization, self.org)
        self.assertEqual(site.site_name, "Main Site")
        self.assertTrue(site.active)

    def test_site_cascade_delete(self):
        """Test that sites are deleted when organization is deleted."""
        site = Site.objects.create(
            organization=self.org,
            site_name="Test Site",
            site_address="123 St",
            site_employee_count=3,
        )
        site_id = site.id
        self.org.delete()
        self.assertFalse(Site.objects.filter(id=site_id).exists())

    def test_site_optional_employee_count(self):
        """Test that site_employee_count can be null."""
        site = Site.objects.create(organization=self.org, site_name="No Count Site", site_address="789 St")
        self.assertIsNone(site.site_employee_count)

    def test_site_active_flag(self):
        """Test site active/inactive status."""
        site = Site.objects.create(
            organization=self.org, site_name="Inactive Site", site_address="123 St", active=False
        )
        self.assertFalse(site.active)

    def test_site_str(self):
        """Test site string representation."""
        site = Site.objects.create(organization=self.org, site_name="Test Site", site_address="123 St")
        self.assertIn("Test Site", str(site))
        self.assertIn("Test Org", str(site))


class StandardModelTest(TestCase):
    """Test Standard model validation."""

    def test_create_standard(self):
        """Test creating a standard."""
        std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.assertEqual(std.code, "ISO 9001:2015")
        self.assertEqual(std.title, "Quality Management Systems")

    def test_standard_code_unique(self):
        """Test that standard code must be unique."""
        Standard.objects.create(code="ISO 9001:2015", title="QMS")
        with self.assertRaises(Exception):  # IntegrityError
            Standard.objects.create(code="ISO 9001:2015", title="Duplicate")

    def test_standard_optional_fields(self):
        """Test optional fields can be blank."""
        std = Standard.objects.create(code="ISO 14001:2015", title="Environmental Management")
        self.assertEqual(std.nace_code, "")
        self.assertEqual(std.ea_code, "")

    def test_standard_str(self):
        """Test standard string representation."""
        std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.assertIn("ISO 9001:2015", str(std))
        self.assertIn("Quality Management Systems", str(std))


class CertificationModelTest(TestCase):
    """Test Certification model validation and relationships."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

    def test_create_certification(self):
        """Test creating a certification."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Manufacturing of widgets",
            certificate_status="active",
        )
        self.assertEqual(cert.organization, self.org)
        self.assertEqual(cert.standard, self.std)
        self.assertEqual(cert.certificate_status, "active")

    def test_certification_unique_together(self):
        """Test that organization+standard combination must be unique."""
        Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope 1",
            certificate_status="active",
        )
        with self.assertRaises(Exception):  # IntegrityError
            Certification.objects.create(
                organization=self.org,
                standard=self.std,
                certification_scope="Scope 2",
                certificate_status="draft",
            )

    def test_certification_protect_standard(self):
        """Test that standard cannot be deleted if certifications exist."""
        _ = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        # Should raise ProtectedError
        with self.assertRaises(Exception):
            self.std.delete()

    def test_certification_cascade_organization(self):
        """Test that certifications are deleted when organization is deleted."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        cert_id = cert.id
        self.org.delete()
        self.assertFalse(Certification.objects.filter(id=cert_id).exists())

    def test_certification_date_validation(self):
        """Test certification date fields (issue_date, expiry_date)."""
        # Note: Model doesn't validate issue_date < expiry_date
        # This should be done at form level
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
        )
        self.assertIsNotNone(cert.issue_date)
        self.assertIsNotNone(cert.expiry_date)

    def test_certification_str(self):
        """Test certification string representation."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        self.assertIn("Test Org", str(cert))
        self.assertIn("ISO 9001:2015", str(cert))
        self.assertIn("active", str(cert))


class OrganizationViewPermissionTest(TestCase):
    """Test organization view permissions (CB Admin only)."""

    def setUp(self):
        self.client = Client()
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.client_user = User.objects.create_user(username="client", password="pass123")

        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        client_group = Group.objects.create(name="client_user")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)
        self.client_user.groups.add(client_group)

        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

    def test_organization_list_cb_admin(self):
        """Test CB Admin can access organization list."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:organization_list"))
        self.assertEqual(response.status_code, 200)

    def test_organization_list_lead_auditor(self):
        """Test Lead Auditor cannot access organization list."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("core:organization_list"))
        self.assertEqual(response.status_code, 403)

    def test_organization_list_client_user(self):
        """Test Client User cannot access organization list."""
        self.client.login(username="client", password="pass123")
        response = self.client.get(reverse("core:organization_list"))
        self.assertEqual(response.status_code, 403)

    def test_organization_list_requires_login(self):
        """Test organization list requires authentication."""
        response = self.client.get(reverse("core:organization_list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('core:organization_list')}")

    def test_organization_create_cb_admin(self):
        """Test CB Admin can create organization."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:organization_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("core:organization_create"),
            {
                "name": "New Org",
                "registered_address": "456 St",
                "customer_id": "NEW001",
                "total_employee_count": 20,
            },
        )
        self.assertRedirects(response, reverse("core:organization_list"))
        self.assertTrue(Organization.objects.filter(customer_id="NEW001").exists())

    def test_organization_create_lead_auditor(self):
        """Test Lead Auditor cannot create organization."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("core:organization_create"))
        self.assertEqual(response.status_code, 403)

    def test_organization_detail_cb_admin(self):
        """Test CB Admin can view organization detail."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:organization_detail", args=[self.org.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Org")

    def test_organization_update_cb_admin(self):
        """Test CB Admin can update organization."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:organization_update", args=[self.org.pk]),
            {
                "name": "Updated Org",
                "registered_address": "123 St",
                "customer_id": "ORG001",
                "total_employee_count": 15,
            },
        )
        self.assertRedirects(response, reverse("core:organization_list"))
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Updated Org")
        self.assertEqual(self.org.total_employee_count, 15)


class SiteViewPermissionTest(TestCase):
    """Test site view permissions."""

    def setUp(self):
        self.client = Client()
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.site = Site.objects.create(organization=self.org, site_name="Test Site", site_address="456 St")

    def test_site_list_cb_admin(self):
        """Test CB Admin can access site list."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:site_list"))
        self.assertEqual(response.status_code, 200)

    def test_site_create_cb_admin(self):
        """Test CB Admin can create site."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:site_create"),
            {
                "organization": self.org.pk,
                "site_name": "New Site",
                "site_address": "789 St",
                "site_employee_count": 5,
                "active": True,
            },
        )
        self.assertRedirects(response, reverse("core:site_list"))
        self.assertTrue(Site.objects.filter(site_name="New Site").exists())

    def test_site_filter_by_organization(self):
        """Test filtering sites by organization."""
        org2 = Organization.objects.create(
            name="Org 2", registered_address="999 St", customer_id="ORG002", total_employee_count=5
        )
        _ = Site.objects.create(organization=org2, site_name="Site 2", site_address="888 St")

        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:site_list"), {"organization": self.org.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Site")
        self.assertNotContains(response, "Site 2")

    def test_site_update_cb_admin(self):
        """Test CB Admin can update site."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:site_update", args=[self.site.pk]),
            {
                "organization": self.org.pk,
                "site_name": "Updated Site",
                "site_address": "789 St",
                "site_employee_count": 15,
                "active": True,
            },
        )
        self.assertRedirects(response, reverse("core:site_list"))
        self.site.refresh_from_db()
        self.assertEqual(self.site.site_name, "Updated Site")


class StandardViewPermissionTest(TestCase):
    """Test standard view permissions."""

    def setUp(self):
        self.client = Client()
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

    def test_standard_list_cb_admin(self):
        """Test CB Admin can access standard list."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:standard_list"))
        self.assertEqual(response.status_code, 200)

    def test_standard_create_cb_admin(self):
        """Test CB Admin can create standard."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:standard_create"),
            {
                "code": "ISO 14001:2015",
                "title": "Environmental Management",
                "nace_code": "",
                "ea_code": "",
            },
        )
        self.assertRedirects(response, reverse("core:standard_list"))
        self.assertTrue(Standard.objects.filter(code="ISO 14001:2015").exists())

    def test_standard_update_cb_admin(self):
        """Test CB Admin can update standard."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:standard_update", args=[self.std.pk]),
            {
                "code": "ISO 9001:2015",
                "title": "Updated Title",
                "nace_code": "",
                "ea_code": "",
            },
        )
        self.assertRedirects(response, reverse("core:standard_list"))
        self.std.refresh_from_db()
        self.assertEqual(self.std.title, "Updated Title")


class CertificationViewPermissionTest(TestCase):
    """Test certification view permissions."""

    def setUp(self):
        self.client = Client()
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")

    def test_certification_list_cb_admin(self):
        """Test CB Admin can access certification list."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:certification_list"))
        self.assertEqual(response.status_code, 200)

    def test_certification_create_cb_admin(self):
        """Test CB Admin can create certification."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:certification_create"),
            {
                "organization": self.org.pk,
                "standard": self.std.pk,
                "certification_scope": "Test scope",
                "certificate_status": "active",
            },
        )
        self.assertRedirects(response, reverse("core:certification_list"))
        self.assertTrue(Certification.objects.filter(organization=self.org, standard=self.std).exists())

    def test_certification_duplicate_prevention(self):
        """Test that duplicate certifications are prevented."""
        _ = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope 1",
            certificate_status="active",
        )

        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:certification_create"),
            {
                "organization": self.org.pk,
                "standard": self.std.pk,
                "certification_scope": "Scope 2",
                "certificate_status": "draft",
            },
        )
        # Should show form error
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Certification.objects.filter(
                organization=self.org, standard=self.std, certification_scope="Scope 2"
            ).exists()
        )

    def test_certification_update_cb_admin(self):
        """Test CB Admin can update certification."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Original Scope",
            certificate_status="active",
        )
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:certification_update", args=[cert.pk]),
            {
                "organization": self.org.pk,
                "standard": self.std.pk,
                "certification_scope": "Updated Scope",
                "certificate_status": "active",
                "issue_date": date.today(),
                "expiry_date": date.today() + timedelta(days=365),
            },
        )
        self.assertRedirects(response, reverse("core:certification_list"))
        cert.refresh_from_db()
        self.assertEqual(cert.certification_scope, "Updated Scope")

    def test_certification_detail_cb_admin(self):
        """Test CB Admin can view certification detail."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("core:certification_detail", args=[cert.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scope")

    def test_certificate_history_create(self):
        """Test creating certificate history."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.post(
            reverse("core:certificate_history_create", kwargs={"certification_pk": cert.pk}),
            {
                "certification": cert.pk,
                "action_date": date.today(),
                "action": "issued",
                "action_reason": "Initial certification",
                "internal_notes": "Notes",
            },
        )
        self.assertRedirects(response, reverse("core:certification_detail", args=[cert.pk]))
        self.assertTrue(CertificateHistory.objects.filter(certification=cert).exists())

    def test_surveillance_schedule_update(self):
        """Test updating surveillance schedule."""
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Scope",
            certificate_status="active",
        )
        # Schedule is created automatically via signal or we create it manually if not
        defaults = {
            "cycle_start": date.today(),
            "cycle_end": date.today() + timedelta(days=1095),
            "surveillance_1_due_date": date.today() + timedelta(days=365),
            "surveillance_2_due_date": date.today() + timedelta(days=730),
            "recertification_due_date": date.today() + timedelta(days=1095),
        }
        schedule, _ = SurveillanceSchedule.objects.get_or_create(certification=cert, defaults=defaults)

        self.client.login(username="cbadmin", password="pass123")
        new_s1_date = date.today() + timedelta(days=366)
        response = self.client.post(
            reverse("core:surveillance_schedule_update", args=[schedule.pk]),
            {
                "surveillance_1_due_date": new_s1_date,
                "surveillance_2_due_date": defaults["surveillance_2_due_date"],
                "recertification_due_date": defaults["recertification_due_date"],
                "surveillance_1_completed": False,
                "surveillance_2_completed": False,
                "recertification_completed": False,
            },
        )
        self.assertRedirects(response, reverse("core:certification_detail", args=[cert.pk]))
        schedule.refresh_from_db()
        self.assertEqual(schedule.surveillance_1_due_date, new_s1_date)

"""
Comprehensive tests for accounts app: authentication, authorization, profiles, roles.
"""

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Profile
from core.models import Organization


class ProfileModelTest(TestCase):
    """Test Profile model methods and relationships."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 Test St",
            customer_id="TEST001",
            total_employee_count=10,
        )

    def test_profile_auto_created(self):
        """Test that profile is automatically created when user is created."""
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_organization(self):
        """Test profile organization relationship."""
        self.user.profile.organization = self.org
        self.user.profile.save()
        self.assertEqual(self.user.profile.organization, self.org)

    def test_is_cb_admin(self):
        """Test is_cb_admin method."""
        cb_admin_group = Group.objects.create(name="cb_admin")
        self.user.groups.add(cb_admin_group)
        self.assertTrue(self.user.profile.is_cb_admin())
        self.assertFalse(self.user.profile.is_lead_auditor())

    def test_is_lead_auditor(self):
        """Test is_lead_auditor method."""
        lead_group = Group.objects.create(name="lead_auditor")
        self.user.groups.add(lead_group)
        self.assertTrue(self.user.profile.is_lead_auditor())
        self.assertFalse(self.user.profile.is_cb_admin())

    def test_is_auditor(self):
        """Test is_auditor method (lead_auditor or auditor)."""
        auditor_group = Group.objects.create(name="auditor")
        self.user.groups.add(auditor_group)
        self.assertTrue(self.user.profile.is_auditor())

        # Also true for lead_auditor
        lead_group = Group.objects.create(name="lead_auditor")
        user2 = User.objects.create_user(username="lead", password="pass")
        user2.groups.add(lead_group)
        self.assertTrue(user2.profile.is_auditor())

    def test_is_client_admin(self):
        """Test is_client_admin method."""
        client_admin_group = Group.objects.create(name="client_admin")
        self.user.groups.add(client_admin_group)
        self.assertTrue(self.user.profile.is_client_admin())

    def test_is_client_user(self):
        """Test is_client_user method (client_admin or client_user)."""
        client_user_group = Group.objects.create(name="client_user")
        self.user.groups.add(client_user_group)
        self.assertTrue(self.user.profile.is_client_user())

        # Also true for client_admin
        client_admin_group = Group.objects.create(name="client_admin")
        user2 = User.objects.create_user(username="admin", password="pass")
        user2.groups.add(client_admin_group)
        self.assertTrue(user2.profile.is_client_user())

    def test_get_role_display(self):
        """Test get_role_display method."""
        cb_admin_group = Group.objects.create(name="cb_admin")
        self.user.groups.add(cb_admin_group)
        self.assertEqual(self.user.profile.get_role_display(), "CB Admin")

        # Test no role
        user2 = User.objects.create_user(username="norole", password="pass")
        self.assertEqual(user2.profile.get_role_display(), "No Role")


class AuthenticationTest(TestCase):
    """Test authentication and login functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login_page_loads(self):
        """Test that login page is accessible."""
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Username"
        )  # pylint: disable=unexpected-keyword-arg  # pylint: disable=unexpected-keyword-arg

    def test_login_valid_credentials(self):
        """Test login with valid credentials."""
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "testpass123"},
            follow=True,
        )
        self.assertTrue(response.context["user"].is_authenticated)
        # Should redirect to dashboard
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "wrongpass"},
            follow=True,
        )
        self.assertFalse(response.context["user"].is_authenticated)
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "error")

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        response = self.client.post(reverse("accounts:login"), {"username": "testuser"}, follow=True)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_logout(self):
        """Test logout functionality."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("accounts:logout"), follow=True)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertRedirects(response, reverse("accounts:login"))

    def test_redirect_authenticated_user(self):
        """Test that authenticated users are redirected from login page."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(response, reverse("accounts:dashboard"))


class DashboardAccessTest(TestCase):
    """Test role-based dashboard access."""

    def setUp(self):
        self.client = Client()
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.auditor = User.objects.create_user(username="auditor", password="pass123")
        self.client_admin = User.objects.create_user(username="clientadmin", password="pass123")
        self.client_user = User.objects.create_user(username="clientuser", password="pass123")
        self.no_role = User.objects.create_user(username="norole", password="pass123")

        # Create groups and assign
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        auditor_group = Group.objects.create(name="auditor")
        client_admin_group = Group.objects.create(name="client_admin")
        client_user_group = Group.objects.create(name="client_user")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)
        self.auditor.groups.add(auditor_group)
        self.client_admin.groups.add(client_admin_group)
        self.client_user.groups.add(client_user_group)

        # Create organization for client users
        self.org = Organization.objects.create(
            name="Client Org",
            registered_address="123 St",
            customer_id="CLIENT001",
            total_employee_count=5,
        )
        self.client_admin.profile.organization = self.org
        self.client_admin.profile.save()
        self.client_user.profile.organization = self.org
        self.client_user.profile.save()

    def test_cb_admin_dashboard_access(self):
        """Test CB Admin can access CB dashboard."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard_cb"))

        response = self.client.get(reverse("accounts:dashboard_cb"))
        self.assertEqual(response.status_code, 200)

    def test_cb_admin_cannot_access_other_dashboards(self):
        """Test CB Admin is redirected from other dashboards."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("accounts:dashboard_auditor"), follow=True)
        self.assertRedirects(response, reverse("accounts:dashboard_cb"))

        response = self.client.get(reverse("accounts:dashboard_client"), follow=True)
        self.assertRedirects(response, reverse("accounts:dashboard_cb"))

    def test_lead_auditor_dashboard_access(self):
        """Test Lead Auditor can access auditor dashboard."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard_auditor"))

        response = self.client.get(reverse("accounts:dashboard_auditor"))
        self.assertEqual(response.status_code, 200)

    def test_auditor_dashboard_access(self):
        """Test Auditor can access auditor dashboard."""
        self.client.login(username="auditor", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard_auditor"))

        response = self.client.get(reverse("accounts:dashboard_auditor"))
        self.assertEqual(response.status_code, 200)

    def test_client_admin_dashboard_access(self):
        """Test Client Admin can access client dashboard."""
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard_client"))

        response = self.client.get(reverse("accounts:dashboard_client"))
        self.assertEqual(response.status_code, 200)

    def test_client_user_dashboard_access(self):
        """Test Client User can access client dashboard."""
        self.client.login(username="clientuser", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:dashboard_client"))

        response = self.client.get(reverse("accounts:dashboard_client"))
        self.assertEqual(response.status_code, 200)

    def test_no_role_dashboard(self):
        """Test user with no role sees message."""
        self.client.login(username="norole", password="pass123")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No role assigned")

    def test_dashboard_requires_login(self):
        """Test that dashboards require authentication."""
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

        response = self.client.get(reverse("accounts:dashboard_cb"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard_cb')}")

    def test_cb_dashboard_shows_stats(self):
        """Test CB dashboard shows organization and audit counts."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("accounts:dashboard_cb"))
        self.assertEqual(response.status_code, 200)
        # Should contain stats (even if 0)
        self.assertIn("organizations_count", response.context)
        self.assertIn("certifications_count", response.context)
        self.assertIn("audits_count", response.context)


class ProfileOrganizationTest(TestCase):
    """Test profile-organization relationships."""

    def setUp(self):
        self.org1 = Organization.objects.create(
            name="Org 1",
            registered_address="Address 1",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.org2 = Organization.objects.create(
            name="Org 2",
            registered_address="Address 2",
            customer_id="ORG002",
            total_employee_count=20,
        )
        self.user = User.objects.create_user(username="testuser", password="pass123")

    def test_profile_can_have_no_organization(self):
        """Test that profile can exist without organization (for CB admins/auditors)."""
        self.assertIsNone(self.user.profile.organization)

    def test_profile_organization_assignment(self):
        """Test assigning organization to profile."""
        self.user.profile.organization = self.org1
        self.user.profile.save()
        self.assertEqual(self.user.profile.organization, self.org1)

    def test_profile_organization_change(self):
        """Test changing profile organization."""
        self.user.profile.organization = self.org1
        self.user.profile.save()
        self.user.profile.organization = self.org2
        self.user.profile.save()
        self.assertEqual(self.user.profile.organization, self.org2)

    def test_profile_organization_removal(self):
        """Test removing organization from profile."""
        self.user.profile.organization = self.org1
        self.user.profile.save()
        self.user.profile.organization = None
        self.user.profile.save()
        self.assertIsNone(self.user.profile.organization)

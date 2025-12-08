from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from core.models import Organization

User = get_user_model()


class TestIdentityModelsCoverage(TestCase):
    def test_profile_str_with_org(self):
        user = User.objects.create_user(username="testuser", first_name="Test", last_name="User")
        org = Organization.objects.create(name="Test Org", customer_id="CUST-001", total_employee_count=10)
        profile = user.profile
        profile.organization = org
        profile.save()
        self.assertEqual(str(profile), "Test User (Test Org (CUST-001))")

    def test_profile_str_no_org(self):
        user = User.objects.create_user(username="testuser2", first_name="Test", last_name="User")
        profile = user.profile
        self.assertEqual(str(profile), "Test User (No Org)")

    def test_profile_str_no_name(self):
        user = User.objects.create_user(username="testuser3")
        profile = user.profile
        self.assertEqual(str(profile), "testuser3 (No Org)")

    def test_get_role_display_client_user(self):
        user = User.objects.create_user(username="clientuser")
        group = Group.objects.create(name="client_user")
        user.groups.add(group)
        self.assertEqual(user.profile.get_role_display(), "Client User")

    def test_get_role_display_no_role(self):
        user = User.objects.create_user(username="norole")
        self.assertEqual(user.profile.get_role_display(), "No Role")

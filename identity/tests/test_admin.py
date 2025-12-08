import pytest
from django.contrib import admin
from django.contrib.auth.models import User

from identity.adapters.admin import ProfileInline, UserAdmin


@pytest.mark.django_db
class TestIdentityAdmin:
    def test_user_admin_registered(self):
        """Test that UserAdmin is registered for User model."""
        registry = admin.site._registry
        assert User in registry
        assert isinstance(registry[User], UserAdmin)

    def test_profile_inline_configured(self):
        """Test that ProfileInline is configured in UserAdmin."""
        assert ProfileInline in UserAdmin.inlines

    def test_get_inline_instances_existing_user(self, admin_user):
        """Test get_inline_instances returns inline for existing user."""
        user_admin = UserAdmin(User, admin.site)
        request = None  # Request is not used in the default implementation for this check

        inlines = user_admin.get_inline_instances(request, admin_user)
        assert len(inlines) == 1
        assert isinstance(inlines[0], ProfileInline)

    def test_get_inline_instances_new_user(self):
        """Test get_inline_instances returns empty list for new user."""
        user_admin = UserAdmin(User, admin.site)
        request = None

        inlines = user_admin.get_inline_instances(request, obj=None)
        assert len(inlines) == 0

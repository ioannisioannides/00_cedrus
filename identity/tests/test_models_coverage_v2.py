from unittest.mock import Mock

import pytest
from django.contrib.auth.models import User

from identity.adapters.models import Profile


class TestIdentityModelsCoverageV2:
    @pytest.mark.django_db
    def test_get_role_display_technical_reviewer(self):
        """Test get_role_display for Technical Reviewer."""
        user = User.objects.create_user(username="tech_reviewer", password="password")
        profile = Profile(user=user)

        # Mock methods on the instance
        profile.is_cb_admin = Mock(return_value=False)
        profile.is_lead_auditor = Mock(return_value=False)
        profile.is_technical_reviewer = Mock(return_value=True)

        # We need to mock user.groups.filter.exists()
        # Since user is real, we can mock the groups attribute or just ensure it returns empty
        # But user.groups is a ManyRelatedManager.
        # Easier to just mock the whole user object but ensure it passes isinstance check?
        # No, let's just use the real user and ensure no groups are assigned.

        assert profile.get_role_display() == "Technical Reviewer"

    @pytest.mark.django_db
    def test_get_role_display_decision_maker(self):
        """Test get_role_display for Decision Maker."""
        user = User.objects.create_user(username="decision_maker", password="password")
        profile = Profile(user=user)

        profile.is_cb_admin = Mock(return_value=False)
        profile.is_lead_auditor = Mock(return_value=False)
        profile.is_technical_reviewer = Mock(return_value=False)
        profile.is_decision_maker = Mock(return_value=True)

        assert profile.get_role_display() == "Decision Maker"

    @pytest.mark.django_db
    def test_save_user_profile_missing_profile(self):
        """Test save_user_profile signal when profile is missing."""
        # Create a user (this creates a profile via signal)
        user = User.objects.create_user(username="test_no_profile", password="password")

        # Delete the profile
        if hasattr(user, "profile"):
            user.profile.delete()
            # Refresh user from db to ensure profile cache is cleared
            user.refresh_from_db()

        # Now save the user again. The signal should run, check hasattr(instance, "profile"),
        # find it false, and do nothing (hitting the else/exit branch).
        user.save()

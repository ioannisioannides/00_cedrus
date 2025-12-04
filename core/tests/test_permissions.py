from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Group, User

from core.models import Organization
from core.permissions.mixins import AuditorRequiredMixin, CBAdminRequiredMixin, ClientRequiredMixin
from core.permissions.policies import PBACPolicy
from core.permissions.predicates import PermissionPredicate


@pytest.mark.django_db
class TestPermissionPredicate:
    def setup_method(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        # Profile is created by signal
        self.profile = self.user.profile

        self.cb_admin_group = Group.objects.create(name="cb_admin")

        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_admin_group = Group.objects.create(name="client_admin")
        self.client_user_group = Group.objects.create(name="client_user")
        self.technical_reviewer_group = Group.objects.create(name="technical_reviewer")
        self.decision_maker_group = Group.objects.create(name="decision_maker")

    def test_is_cb_admin(self):
        assert not PermissionPredicate.is_cb_admin(self.user)
        self.user.groups.add(self.cb_admin_group)
        assert PermissionPredicate.is_cb_admin(self.user)

    def test_is_lead_auditor(self):
        assert not PermissionPredicate.is_lead_auditor(self.user)
        self.user.groups.add(self.lead_auditor_group)
        assert PermissionPredicate.is_lead_auditor(self.user)

    def test_is_auditor(self):
        assert not PermissionPredicate.is_auditor(self.user)
        self.user.groups.add(self.auditor_group)
        assert PermissionPredicate.is_auditor(self.user)
        self.user.groups.clear()
        self.user.groups.add(self.lead_auditor_group)
        assert PermissionPredicate.is_auditor(self.user)

    def test_is_client_user(self):
        assert not PermissionPredicate.is_client_user(self.user)
        self.user.groups.add(self.client_user_group)
        assert PermissionPredicate.is_client_user(self.user)
        self.user.groups.clear()
        self.user.groups.add(self.client_admin_group)
        assert PermissionPredicate.is_client_user(self.user)

    def test_is_technical_reviewer(self):
        assert not PermissionPredicate.is_technical_reviewer(self.user)
        self.user.groups.add(self.technical_reviewer_group)
        assert PermissionPredicate.is_technical_reviewer(self.user)

    def test_is_decision_maker(self):
        assert not PermissionPredicate.is_decision_maker(self.user)
        self.user.groups.add(self.decision_maker_group)
        assert PermissionPredicate.is_decision_maker(self.user)

    def test_can_conduct_technical_review(self):
        assert not PermissionPredicate.can_conduct_technical_review(self.user)
        self.user.groups.add(self.technical_reviewer_group)
        assert PermissionPredicate.can_conduct_technical_review(self.user)
        self.user.groups.clear()
        self.user.groups.add(self.cb_admin_group)
        assert PermissionPredicate.can_conduct_technical_review(self.user)

    def test_can_make_certification_decision(self):
        assert not PermissionPredicate.can_make_certification_decision(self.user)
        self.user.groups.add(self.decision_maker_group)
        assert PermissionPredicate.can_make_certification_decision(self.user)
        self.user.groups.clear()
        self.user.groups.add(self.cb_admin_group)
        assert PermissionPredicate.can_make_certification_decision(self.user)

    def test_can_view_audit(self):
        audit = MagicMock()
        audit.lead_auditor = None
        audit.team_members.filter.return_value.exists.return_value = False

        # Create a real organization for comparison
        org1 = Organization.objects.create(name="Org 1", customer_id="ORG1", total_employee_count=10)
        org2 = Organization.objects.create(name="Org 2", customer_id="ORG2", total_employee_count=10)
        audit.organization = org1

        # No permissions
        assert not PermissionPredicate.can_view_audit(self.user, audit)

        # CB Admin
        self.user.groups.add(self.cb_admin_group)
        assert PermissionPredicate.can_view_audit(self.user, audit)
        self.user.groups.clear()

        # Lead Auditor
        audit.lead_auditor = self.user
        assert PermissionPredicate.can_view_audit(self.user, audit)
        audit.lead_auditor = None

        # Team Member
        audit.team_members.filter.return_value.exists.return_value = True
        assert PermissionPredicate.can_view_audit(self.user, audit)
        audit.team_members.filter.return_value.exists.return_value = False

        # Client User (same org)
        self.profile.organization = org1
        self.profile.save()
        # Refresh user to ensure profile is up to date (though it should be via related manager)
        self.user.refresh_from_db()
        assert PermissionPredicate.can_view_audit(self.user, audit)

        # Client User (diff org)
        self.profile.organization = org2
        self.profile.save()
        self.user.refresh_from_db()
        assert not PermissionPredicate.can_view_audit(self.user, audit)


@pytest.mark.django_db
class TestPBACPolicy:
    def setup_method(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.profile = self.user.profile
        self.cb_admin_group = Group.objects.create(name="cb_admin")

        self.auditor_group = Group.objects.create(name="auditor")
        self.client_user_group = Group.objects.create(name="client_user")

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_independent_for_decision_cb_admin(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = True
        audit = MagicMock()
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, audit)
        assert allowed
        assert "CB Admin override" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_independent_for_decision_lead_auditor(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        audit = MagicMock()
        audit.lead_auditor = self.user
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, audit)
        assert not allowed
        assert "lead auditor" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_independent_for_decision_team_member(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        audit = MagicMock()
        audit.lead_auditor = MagicMock()
        audit.team_members.filter.return_value.exists.return_value = True
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, audit)
        assert not allowed
        assert "team member" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_independent_for_decision_technical_reviewer(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        audit = MagicMock()
        audit.lead_auditor = MagicMock()
        audit.team_members.filter.return_value.exists.return_value = False
        audit.technical_review.reviewer = self.user
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, audit)
        assert not allowed
        assert "technical reviewer" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_independent_for_decision_success(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        audit = MagicMock()
        audit.lead_auditor = MagicMock()
        audit.team_members.filter.return_value.exists.return_value = False
        # Ensure technical_review doesn't exist or reviewer is different
        del audit.technical_review

        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, audit)
        assert allowed
        assert "Decision maker has independence" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_auditor")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_client_user")
    def test_can_user_access_organization(self, mock_is_client, mock_is_auditor, mock_is_cb_admin):
        audit = MagicMock()
        org1 = Organization.objects.create(name="Org 1", customer_id="ORG1", total_employee_count=10)
        org2 = Organization.objects.create(name="Org 2", customer_id="ORG2", total_employee_count=10)
        audit.organization = org1

        # CB Admin
        mock_is_cb_admin.return_value = True
        allowed, reason = PBACPolicy.can_user_access_organization(self.user, audit)
        assert allowed
        assert "CB Admin" in reason
        mock_is_cb_admin.return_value = False

        # Auditor
        mock_is_auditor.return_value = True
        allowed, reason = PBACPolicy.can_user_access_organization(self.user, audit)
        assert allowed
        assert "Auditors" in reason
        mock_is_auditor.return_value = False

        # Client User (same org)
        mock_is_client.return_value = True
        self.profile.organization = org1
        self.profile.save()
        self.user.refresh_from_db()

        allowed, reason = PBACPolicy.can_user_access_organization(self.user, audit)
        assert allowed
        assert "User belongs to this organization" in reason

        # Client User (diff org)
        self.profile.organization = org2
        self.profile.save()
        self.user.refresh_from_db()

        allowed, reason = PBACPolicy.can_user_access_organization(self.user, audit)
        assert not allowed
        assert "Client users can only access audits for their own organization" in reason

        # No role
        mock_is_client.return_value = False
        allowed, reason = PBACPolicy.can_user_access_organization(self.user, audit)
        assert not allowed
        assert "User does not have permission" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_is_assigned_to_audit(self, mock_is_cb_admin):
        audit = MagicMock()

        # CB Admin
        mock_is_cb_admin.return_value = True
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.user, audit)
        assert allowed
        assert "CB Admin" in reason
        mock_is_cb_admin.return_value = False

        # Lead Auditor
        audit.lead_auditor = self.user
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.user, audit)
        assert allowed
        assert "lead auditor" in reason
        audit.lead_auditor = MagicMock()

        # Team Member
        audit.team_members.filter.return_value.exists.return_value = True
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.user, audit)
        assert allowed
        assert "team member" in reason
        audit.team_members.filter.return_value.exists.return_value = False

        # Not assigned
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.user, audit)
        assert not allowed
        assert "not assigned" in reason


class TestMixins:
    def test_cb_admin_required_mixin(self):
        mixin = CBAdminRequiredMixin()
        mixin.request = MagicMock()
        mixin.request.user = MagicMock()

        with patch("core.permissions.predicates.PermissionPredicate.is_cb_admin", return_value=True):
            assert mixin.test_func() is True

        with patch("core.permissions.predicates.PermissionPredicate.is_cb_admin", return_value=False):
            assert mixin.test_func() is False

    def test_auditor_required_mixin(self):
        mixin = AuditorRequiredMixin()
        mixin.request = MagicMock()
        mixin.request.user = MagicMock()

        with patch("core.permissions.predicates.PermissionPredicate.is_auditor", return_value=True):
            assert mixin.test_func() is True

        with patch("core.permissions.predicates.PermissionPredicate.is_auditor", return_value=False):
            assert mixin.test_func() is False

    def test_client_required_mixin(self):
        mixin = ClientRequiredMixin()
        mixin.request = MagicMock()
        mixin.request.user = MagicMock()

        with patch("core.permissions.predicates.PermissionPredicate.is_client_user", return_value=True):
            assert mixin.test_func() is True

        with patch("core.permissions.predicates.PermissionPredicate.is_client_user", return_value=False):
            assert mixin.test_func() is False


class TestPBACPolicyExtended:
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_technical_reviewer")
    def test_can_conduct_technical_review(self, mock_is_reviewer, mock_is_cb_admin):
        user = MagicMock()
        audit = MagicMock()

        # Not reviewer or admin
        mock_is_reviewer.return_value = False
        mock_is_cb_admin.return_value = False
        allowed, reason = PBACPolicy.can_conduct_technical_review(user, audit)
        assert not allowed
        assert "must be a technical reviewer" in reason

        # Reviewer but Lead Auditor
        mock_is_reviewer.return_value = True
        audit.lead_auditor = user
        allowed, reason = PBACPolicy.can_conduct_technical_review(user, audit)
        assert not allowed
        assert "cannot be the lead auditor" in reason

        # Reviewer but Team Member
        audit.lead_auditor = MagicMock()
        audit.team_members.filter.return_value.exists.return_value = True
        allowed, reason = PBACPolicy.can_conduct_technical_review(user, audit)
        assert not allowed
        assert "cannot be a team member" in reason

        # Reviewer and Independent
        audit.team_members.filter.return_value.exists.return_value = False
        allowed, reason = PBACPolicy.can_conduct_technical_review(user, audit)
        assert allowed

        # CB Admin and Independent
        mock_is_reviewer.return_value = False
        mock_is_cb_admin.return_value = True
        allowed, reason = PBACPolicy.can_conduct_technical_review(user, audit)
        assert allowed

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_decision_maker")
    def test_can_make_certification_decision(self, mock_is_decision_maker, mock_is_cb_admin):
        user = MagicMock()
        audit = MagicMock()

        # Not decision maker or admin
        mock_is_decision_maker.return_value = False
        mock_is_cb_admin.return_value = False
        allowed, reason = PBACPolicy.can_make_certification_decision(user, audit)
        assert not allowed
        assert "must be a decision maker" in reason

        # Decision maker, check independence delegation
        mock_is_decision_maker.return_value = True
        with patch.object(PBACPolicy, "is_independent_for_decision", return_value=(True, "OK")) as mock_indep:
            allowed, reason = PBACPolicy.can_make_certification_decision(user, audit)
            assert allowed
            assert reason == "OK"
            mock_indep.assert_called_once_with(user, audit)

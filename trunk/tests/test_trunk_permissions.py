from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import Group, User

from core.models import Organization
from identity.adapters.models import Profile
from trunk.permissions.mixins import AuditorRequiredMixin, CBAdminRequiredMixin, ClientRequiredMixin
from trunk.permissions.policies import PBACPolicy
from trunk.permissions.predicates import PermissionPredicate


@pytest.mark.django_db
class TestPermissionPredicate:
    def setup_method(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        # Profile is created by signal, but we ensure it exists
        if not hasattr(self.user, 'profile'):
            Profile.objects.create(user=self.user)
        self.profile = self.user.profile

        self.organization = Organization.objects.create(
            name="Test Org",
            total_employee_count=10,
            customer_id="CUST-001"
        )

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
        audit.organization = self.organization

        # No permission
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

        # Organization Member
        self.user.profile.organization = audit.organization
        self.user.profile.save()
        assert PermissionPredicate.can_view_audit(self.user, audit)


@pytest.mark.django_db
class TestPBACPolicy:
    def setup_method(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        if not hasattr(self.user, 'profile'):
            Profile.objects.create(user=self.user)
        self.organization = Organization.objects.create(
            name="Test Org",
            total_employee_count=10,
            customer_id="CUST-001"
        )

        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_user_group = Group.objects.create(name="client_user")
        self.technical_reviewer_group = Group.objects.create(name="technical_reviewer")
        self.decision_maker_group = Group.objects.create(name="decision_maker")

        self.audit = MagicMock()
        self.audit.lead_auditor = None
        self.audit.team_members.filter.return_value.exists.return_value = False
        self.audit.technical_review.reviewer = None
        self.audit.organization = self.organization

    def test_is_independent_for_decision_cb_admin(self):
        self.user.groups.add(self.cb_admin_group)
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, self.audit)
        assert allowed
        assert "CB Admin override" in reason

    def test_is_independent_for_decision_lead_auditor(self):
        self.audit.lead_auditor = self.user
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, self.audit)
        assert not allowed
        assert "lead auditor" in reason

    def test_is_independent_for_decision_team_member(self):
        self.audit.team_members.filter.return_value.exists.return_value = True
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, self.audit)
        assert not allowed
        assert "team member" in reason

    def test_is_independent_for_decision_technical_reviewer(self):
        self.audit.technical_review.reviewer = self.user
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, self.audit)
        assert not allowed
        assert "technical reviewer" in reason

    def test_is_independent_for_decision_success(self):
        allowed, reason = PBACPolicy.is_independent_for_decision(self.user, self.audit)
        assert allowed
        assert "independence" in reason

    def test_can_user_access_organization(self):
        # CB Admin
        self.user.groups.add(self.cb_admin_group)
        allowed, _ = PBACPolicy.can_user_access_organization(self.user, self.audit)
        assert allowed
        self.user.groups.clear()

        # Auditor
        self.user.groups.add(self.auditor_group)
        allowed, _ = PBACPolicy.can_user_access_organization(self.user, self.audit)
        assert allowed
        self.user.groups.clear()

        # Client User - Same Org
        self.user.groups.add(self.client_user_group)
        self.user.profile.organization = self.audit.organization
        self.user.profile.save()
        allowed, _ = PBACPolicy.can_user_access_organization(self.user, self.audit)
        assert allowed

        # Client User - Different Org
        other_org = Organization.objects.create(
            name="Other Org",
            total_employee_count=10,
            customer_id="CUST-002"
        )
        self.user.profile.organization = other_org
        self.user.profile.save()
        allowed, _ = PBACPolicy.can_user_access_organization(self.user, self.audit)
        assert not allowed

        # No Role
        self.user.groups.clear()
        allowed, _ = PBACPolicy.can_user_access_organization(self.user, self.audit)
        assert not allowed

    def test_is_assigned_to_audit(self):
        # CB Admin
        self.user.groups.add(self.cb_admin_group)
        allowed, _ = PBACPolicy.is_assigned_to_audit(self.user, self.audit)
        assert allowed
        self.user.groups.clear()

        # Lead Auditor
        self.audit.lead_auditor = self.user
        allowed, _ = PBACPolicy.is_assigned_to_audit(self.user, self.audit)
        assert allowed
        self.audit.lead_auditor = None

        # Team Member
        self.audit.team_members.filter.return_value.exists.return_value = True
        allowed, _ = PBACPolicy.is_assigned_to_audit(self.user, self.audit)
        assert allowed
        self.audit.team_members.filter.return_value.exists.return_value = False

        # Not Assigned
        allowed, _ = PBACPolicy.is_assigned_to_audit(self.user, self.audit)
        assert not allowed

    def test_can_conduct_technical_review(self):
        # Not Technical Reviewer
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.user, self.audit)
        assert not allowed
        assert "User must be a technical reviewer" in reason

        # Technical Reviewer
        self.user.groups.add(self.technical_reviewer_group)
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.user, self.audit)
        assert allowed

        # Conflict: Lead Auditor
        self.audit.lead_auditor = self.user
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.user, self.audit)
        assert not allowed
        assert "cannot be the lead auditor" in reason
        self.audit.lead_auditor = None

        # Conflict: Team Member
        self.audit.team_members.filter.return_value.exists.return_value = True
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.user, self.audit)
        assert not allowed
        assert "cannot be a team member" in reason
        self.audit.team_members.filter.return_value.exists.return_value = False

        self.user.groups.clear()

    def test_can_make_certification_decision(self):
        # Not Decision Maker
        allowed, reason = PBACPolicy.can_make_certification_decision(self.user, self.audit)
        assert not allowed
        assert "User must be a decision maker" in reason

        # Decision Maker
        self.user.groups.add(self.decision_maker_group)
        allowed, reason = PBACPolicy.can_make_certification_decision(self.user, self.audit)
        assert allowed

        # Conflict (delegated to is_independent_for_decision)
        self.audit.lead_auditor = self.user
        allowed, reason = PBACPolicy.can_make_certification_decision(self.user, self.audit)
        assert not allowed

        self.user.groups.clear()


@pytest.mark.django_db
class TestMixins:
    def setup_method(self):
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_group = Group.objects.create(name="client_user")

        self.org = Organization.objects.create(
            name="Test Org",
            total_employee_count=10,
            customer_id="CUST-MIXIN-001"
        )

        self.user = User.objects.create_user(username="mixin_user", password="password")
        # Profile is created by signal, so we update it
        self.user.profile.organization = self.org
        self.user.profile.save()

    def _check_mixin(self, mixin_cls, user, expected_result):
        view = mixin_cls()
        view.request = MagicMock()
        view.request.user = user
        assert view.test_func() == expected_result

    def test_cb_admin_required_mixin(self):
        # Test with CB Admin
        self.user.groups.add(self.cb_admin_group)
        self._check_mixin(CBAdminRequiredMixin, self.user, True)

        # Test without CB Admin
        self.user.groups.clear()
        self._check_mixin(CBAdminRequiredMixin, self.user, False)

    def test_auditor_required_mixin(self):
        # Test with Auditor
        self.user.groups.add(self.auditor_group)
        self._check_mixin(AuditorRequiredMixin, self.user, True)

        # Test without Auditor
        self.user.groups.clear()
        self._check_mixin(AuditorRequiredMixin, self.user, False)

    def test_client_required_mixin(self):
        # Test with Client
        self.user.groups.add(self.client_group)
        self._check_mixin(ClientRequiredMixin, self.user, True)

        # Test without Client
        self.user.groups.clear()
        self._check_mixin(ClientRequiredMixin, self.user, False)

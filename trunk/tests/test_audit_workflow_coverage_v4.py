from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from audit_management.models import Audit, Nonconformity
from certification.models import TechnicalReview
from core.models import Organization
from trunk.workflows.audit_state_machine import AuditStateMachine
from trunk.workflows.audit_workflow import AuditWorkflow

User = get_user_model()


@pytest.mark.django_db
class TestAuditWorkflowCoverageV4:
    def test_permission_report_draft_to_client_review_lead_auditor_mismatch(self):
        """Test permission when user is a lead auditor but not assigned to this audit."""
        user = User.objects.create_user(username="lead_auditor_other", password="password")
        # Make user a lead auditor globally
        user.profile.is_lead_auditor = True
        user.profile.save()

        audit = Audit(lead_auditor=None, status="report_draft")  # Not assigned to this user
        sm = AuditStateMachine(audit)

        with (
            patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms,
            patch("trunk.permissions.policies.PBACPolicy") as mock_policy,
        ):
            mock_perms.is_lead_auditor.return_value = True
            mock_perms.is_cb_admin.return_value = False
            mock_policy.is_assigned_to_audit.return_value = (True, "Assigned")

            # Should return False because audit.lead_auditor is None (not user)
            # can_transition returns (bool, reason)
            assert sm.can_transition("client_review", user)[0] is False

    def test_permission_client_review_to_submitted_lead_auditor_mismatch(self):
        """Test permission when user is a lead auditor but not assigned to this audit."""
        user = User.objects.create_user(username="lead_auditor_other_2", password="password")
        user.profile.is_lead_auditor = True
        user.profile.save()

        audit = Audit(lead_auditor=None, status="client_review")
        sm = AuditStateMachine(audit)

        with (
            patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms,
            patch("trunk.permissions.policies.PBACPolicy") as mock_policy,
        ):
            mock_perms.is_lead_auditor.return_value = True
            mock_perms.is_cb_admin.return_value = False
            mock_policy.is_assigned_to_audit.return_value = (True, "Assigned")

            assert sm.can_transition("submitted", user)[0] is False

    def test_permission_decision_pending_to_decided_cb_admin_not_decision_maker(self):
        """Test permission for CB Admin who is NOT a decision maker."""
        user = User.objects.create_user(username="cb_admin_only", password="password")

        audit = Audit(status="decision_pending")
        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.is_decision_maker.return_value = False
            mock_perms.is_cb_admin.return_value = True

            # Should return True because is_cb_admin is True
            assert sm.can_transition("decided", user)[0] is True

    def test_guard_draft_to_scheduled_success(self):
        """Test guard success for draft -> scheduled."""
        user = User.objects.create_user(username="lead", password="password")
        audit = Audit(lead_auditor=user, total_audit_date_from="2023-01-01", status="draft")
        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.is_cb_admin.return_value = True  # Bypass permission check

            # Should return True
            assert sm.can_transition("scheduled", user)[0] is True

    def test_guard_technical_review_to_decision_pending_success(self):
        """Test guard success for technical_review -> decision_pending."""
        user = User.objects.create_user(username="reviewer", password="password")
        audit = Audit(status="technical_review")

        # Create approved technical review
        tr = TechnicalReview(audit=audit, status="approved")
        audit.technical_review = tr

        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.can_conduct_technical_review.return_value = True

            assert sm.can_transition("decision_pending", user)[0] is True

    def test_validate_closed_legacy_stage1_success(self):
        """Test validation for Stage 2 closing with legacy Stage 1."""
        org = Organization.objects.create(name="Test Org", total_employee_count=10, customer_id="TEST001")
        audit = Audit(audit_type="stage2", pk=2, organization=org)
        workflow = AuditWorkflow(audit)

        # Mock the audit class objects manager safely
        with patch.object(Audit, "objects") as mock_manager:
            # First filter (status="closed") returns empty
            # Second filter (status="decided") returns True (legacy)

            # Create a mock queryset for the first call (closed)
            mock_qs_closed = MagicMock()
            mock_qs_closed.exclude.return_value.exists.return_value = False

            # Create a mock queryset for the second call (decided)
            mock_qs_decided = MagicMock()
            mock_qs_decided.exclude.return_value.exists.return_value = True

            # Configure filter side effect
            def filter_side_effect(**kwargs):
                if kwargs.get("status") == "closed":
                    return mock_qs_closed
                if kwargs.get("status") == "decided":
                    return mock_qs_decided
                return MagicMock()

            mock_manager.filter.side_effect = filter_side_effect

            # Should not raise ValidationError
            workflow._validate_closed()

    def test_transition_to_decided(self):
        """Test transition_to('decided') calls _validate_decided."""
        user = User.objects.create_user(username="creator", password="password")
        org = Organization.objects.create(name="Test Org 2", total_employee_count=10, customer_id="TEST002")
        audit = Audit(
            status="decision_pending",
            organization=org,
            total_audit_date_from="2023-01-01",
            total_audit_date_to="2023-01-05",
            planned_duration_hours=40,
            created_by=user,
        )
        workflow = AuditWorkflow(audit)

        # Mock _validate_decided to ensure it's called
        with patch.object(workflow, "_validate_decided") as mock_validate:
            # Mock can_transition_to on the CLASS to allow the transition
            with patch("trunk.workflows.audit_workflow.AuditWorkflow.can_transition_to", return_value=True):
                workflow.transition_to("decided")

                mock_validate.assert_called_once()

    def test_permission_report_draft_to_client_review_success(self):
        """Test permission success for report_draft -> client_review."""
        user = User.objects.create_user(username="lead_auditor_assigned", password="password")
        user.profile.is_lead_auditor = True
        user.profile.save()

        audit = Audit(lead_auditor=user, status="report_draft")
        sm = AuditStateMachine(audit)

        with (
            patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms,
            patch("trunk.permissions.policies.PBACPolicy") as mock_policy,
        ):
            mock_perms.is_lead_auditor.return_value = True
            mock_policy.is_assigned_to_audit.return_value = (True, "Assigned")

            assert sm.can_transition("client_review", user)[0] is True

    def test_permission_client_review_to_submitted_success(self):
        """
        Test transition from client_review to submitted (success).
        Requires:
          - User is lead auditor (or CB admin)
          - Guard passes (major NCs have responses)
        """
        user = User.objects.create_user(username="lead_auditor_assigned_2", password="password")

        # Create real objects for ORM relationships
        org = Organization.objects.create(
            name="Test Org 2", customer_id="CUST-002", registered_address="123 Test St", total_employee_count=50
        )
        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
            lead_auditor=user,
            created_by=user,
            status="client_review",
        )

        sm = AuditStateMachine(audit)

        # Mock permissions to return True
        with (
            patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms,
            patch("trunk.permissions.policies.PBACPolicy") as mock_pbac,
        ):
            # Setup permission mocks
            mock_perms.is_cb_admin.return_value = False
            mock_perms.is_lead_auditor.return_value = True
            mock_pbac.is_assigned_to_audit.return_value = (True, "Allowed")

            # We are testing the permission check logic inside can_transition
            # The state machine checks permissions first, then guards.
            # Since we are using a real audit object with no NCs, the guard should pass naturally.

            allowed, reason = sm.can_transition("submitted", user)
            assert allowed is True

    def test_permission_decision_pending_to_closed_cb_admin_not_decision_maker(self):
        """
        Test transition from decision_pending to closed by CB Admin who is NOT decision maker.
        """
        user = User.objects.create_user(username="cb_admin_closer", password="password")

        # Create real objects
        org = Organization.objects.create(
            name="Test Org Closer", customer_id="CUST-CLOSER", registered_address="123 Test St", total_employee_count=50
        )
        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
            created_by=user,
            status="decision_pending",
        )

        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            # User is NOT decision maker
            mock_perms.is_decision_maker.return_value = False
            # User IS CB Admin
            mock_perms.is_cb_admin.return_value = True

            # Guard check: no open major NCs (default state has none)
            allowed, reason = sm.can_transition("closed", user)
            assert allowed is True

    def test_guard_in_progress_to_report_draft_success_state_machine(self):
        """
        Test guard_in_progress_to_report_draft success path.
        Requires at least one finding.
        """
        user = User.objects.create_user(username="lead_auditor_findings", password="password")

        org = Organization.objects.create(
            name="Test Org Findings",
            customer_id="CUST-FINDINGS",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
            lead_auditor=user,
            created_by=user,
        )

        # Create a finding (NonConformity) so the count > 0
        Nonconformity.objects.create(
            audit=audit,
            statement_of_nc="Test NC Statement",
            objective_evidence="Test Evidence",
            clause="4.1",
            category="minor",
            created_by=user,
        )

        sm = AuditStateMachine(audit)

        # We need to bypass the permission check or ensure it passes.
        # Since we are testing the guard specifically, we can invoke the guard directly
        # OR we can mock permissions and call can_transition.
        # Let's call can_transition to be safe, mocking permissions.

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.is_lead_auditor.return_value = True

            # Set state to in_progress
            audit.status = "in_progress"  # Logic doesn't check DB status, but good practice
            # The state machine uses self.audit.status usually, but here we pass from_state/to_state
            # Wait, can_transition uses self.current_state which comes from audit.status
            # But AuditStateMachine wraps StateMachine.
            # Let's just check the guard logic via can_transition

            # We need to ensure the state machine thinks we are in "in_progress"
            # AuditStateMachine initializes with audit.status.
            audit.status = "in_progress"
            sm = AuditStateMachine(audit)

            allowed, reason = sm.can_transition("report_draft", user)
            assert allowed is True

    def test_guard_decision_pending_to_closed_stage2_success_state_machine(self):
        """
        Test guard_decision_pending_to_closed success path for Stage 2.
        Requires completed Stage 1 audit.
        """
        user = User.objects.create_user(username="cb_admin_closer_2", password="password")

        org = Organization.objects.create(
            name="Test Org 3", customer_id="CUST-003", registered_address="123 Test St", total_employee_count=50
        )

        # Create completed Stage 1 audit
        Audit.objects.create(
            organization=org,
            audit_type="stage1",
            total_audit_date_from="2024-01-01",
            total_audit_date_to="2024-01-05",
            created_by=user,
            status="closed",
        )

        # Create Stage 2 audit
        audit = Audit.objects.create(
            organization=org,
            audit_type="stage2",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
            created_by=user,
        )

        sm = AuditStateMachine(audit)
        audit.status = "decision_pending"
        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.is_cb_admin.return_value = True

            allowed, _ = sm.can_transition("closed", user)
            assert allowed is True

    def test_guard_draft_to_scheduled_missing_lead_auditor(self):
        """
        Test guard failure when lead auditor is missing.
        """
        user = User.objects.create_user(username="scheduler_fail", password="password")
        org = Organization.objects.create(
            name="Test Org Sched Fail", customer_id="CUST-SCH-FAIL", total_employee_count=50
        )

        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
            lead_auditor=None,  # Missing
            created_by=user,
            status="draft",
        )

        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms:
            mock_perms.is_cb_admin.return_value = True  # Bypass permissions

            allowed, reason = sm.can_transition("scheduled", user)
            assert allowed is False
            assert "Lead auditor must be assigned" in reason

    def test_permission_report_draft_to_client_review_pbac_fail(self):
        """
        Test permission failure when PBAC check fails.
        """
        user = User.objects.create_user(username="lead_auditor_pbac_fail", password="password")
        org = Organization.objects.create(
            name="Test Org PBAC Fail", customer_id="CUST-PBAC-FAIL", total_employee_count=50
        )

        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            lead_auditor=user,
            created_by=user,
            status="report_draft",
            total_audit_date_from="2025-01-01",
            total_audit_date_to="2025-01-05",
        )

        sm = AuditStateMachine(audit)

        with (
            patch("trunk.permissions.predicates.PermissionPredicate") as mock_perms,
            patch("trunk.permissions.policies.PBACPolicy") as mock_pbac,
        ):
            mock_perms.is_cb_admin.return_value = False
            mock_perms.is_lead_auditor.return_value = True
            # PBAC fails
            mock_pbac.is_assigned_to_audit.return_value = (False, "Not assigned")

            allowed, reason = sm.can_transition("client_review", user)
            assert allowed is False

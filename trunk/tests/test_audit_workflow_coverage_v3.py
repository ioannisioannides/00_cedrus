from unittest.mock import MagicMock, Mock, patch

import pytest

from trunk.workflows.audit_state_machine import AuditStateMachine
from trunk.workflows.audit_workflow import AuditWorkflow


class MockAudit:
    def __init__(self):
        self.pk = 1
        self.status = "draft"
        self.lead_auditor = None
        self.total_audit_date_from = None
        self.organization = Mock()
        self.audit_type = "stage1"
        self.certifications = Mock()
        self.nonconformity_set = Mock()
        self.observation_set = Mock()
        self.opportunityforimprovement_set = Mock()
        self.technical_review = None
        self._state = Mock()
        self._state.db = "default"

    def save(self, *args, **kwargs):
        pass


class TestAuditWorkflowCoverageV3:
    @pytest.mark.django_db
    def test_transition_to_technical_review(self):
        """Test transition to technical_review to hit line 112 in audit_workflow.py."""
        audit = MockAudit()
        audit.status = "submitted"
        workflow = AuditWorkflow(audit)

        # Ensure _validate_submitted passes (called by _validate_technical_review)
        # It checks for major NCs. Let's say there are none.
        audit.nonconformity_set.filter.return_value = []

        # Mock _validate_technical_review to verify it gets called
        with patch.object(workflow, "_validate_technical_review") as mock_validate:
            workflow.transition_to("technical_review", _user=Mock())
            mock_validate.assert_called_once()

    def test_validate_closed_legacy_stage1(self):
        """Test _validate_closed with legacy decided stage 1."""
        audit = MockAudit()
        audit.audit_type = "stage2"
        workflow = AuditWorkflow(audit)

        # Create a mock class for the audit to handle __class__.objects
        mock_manager = MagicMock()
        mock_manager.filter.return_value.exclude.return_value.exists.side_effect = [False, True]

        class MockAuditClass:
            objects = mock_manager

        audit.__class__ = MockAuditClass

        # Mock NCs to avoid subscriptable error
        mock_ncs = MagicMock()
        mock_ncs.filter.return_value.exists.return_value = False
        audit.nonconformity_set = mock_ncs

        # Should NOT raise ValidationError
        workflow._validate_closed()

    def test_validate_closed_no_open_major_ncs(self):
        """Test _validate_closed with no open major NCs."""
        audit = MockAudit()
        audit.audit_type = "surveillance"  # Use surveillance to skip stage 2 check

        # Mock active certs
        mock_certs = MagicMock()
        mock_certs.filter.return_value.exists.return_value = True
        audit.certifications = mock_certs

        workflow = AuditWorkflow(audit)

        # Mock NCs
        mock_ncs = MagicMock()
        mock_ncs.filter.return_value.exists.return_value = False  # No open major NCs
        audit.nonconformity_set = mock_ncs

        # Should NOT raise ValidationError
        workflow._validate_closed()


class TestAuditStateMachineCoverageV3:
    def test_permission_report_draft_to_in_progress(self):
        """Test report_draft -> in_progress permission (Lead Auditor)."""
        audit = MockAudit()
        user = Mock()
        sm = AuditStateMachine(audit)

        # Patch where they are defined/imported from
        with patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit", return_value=(True, None)):
            with patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor", return_value=True):
                audit.lead_auditor = user
                audit.status = "report_draft"
                ok, _ = sm.can_transition("in_progress", user)
                assert ok is True

    def test_permission_client_review_to_report_draft(self):
        """Test client_review -> report_draft permission (Lead Auditor)."""
        audit = MockAudit()
        user = Mock()
        sm = AuditStateMachine(audit)

        with patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit", return_value=(True, None)):
            with patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor", return_value=True):
                audit.lead_auditor = user
                audit.status = "client_review"
                ok, _ = sm.can_transition("report_draft", user)
                assert ok is True

    def test_permission_decision_pending_to_closed_cb_admin(self):
        """Test decision_pending -> closed permission (CB Admin)."""
        audit = MockAudit()
        user = Mock()
        sm = AuditStateMachine(audit)

        # Mock NCs to avoid subscriptable error in guard
        mock_ncs = MagicMock()
        mock_ncs.filter.return_value.exists.return_value = False
        audit.nonconformity_set = mock_ncs

        # Not decision maker, but IS cb admin
        with patch("trunk.permissions.predicates.PermissionPredicate.is_decision_maker", return_value=False):
            with patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin", return_value=True):
                audit.status = "decision_pending"
                ok, _ = sm.can_transition("closed", user)
                assert ok is True

    def test_guard_draft_to_scheduled_missing_date(self):
        """Test guard_draft_to_scheduled with missing date."""
        audit = MockAudit()
        audit.lead_auditor = Mock()  # Has lead auditor
        audit.total_audit_date_from = None  # Missing date
        sm = AuditStateMachine(audit)

        guards = sm._guards()
        guard_func = guards[("draft", "scheduled")][0]

        ok, message = guard_func("draft", "scheduled")
        assert ok is False
        assert "Audit date must be set" in message

    def test_guard_technical_review_to_decision_pending_missing_review(self):
        """Test guard_technical_review_to_decision_pending with missing review."""
        audit = MockAudit()
        # Ensure no technical_review attr
        if hasattr(audit, "technical_review"):
            del audit.technical_review

        sm = AuditStateMachine(audit)

        guards = sm._guards()
        guard_func = guards[("technical_review", "decision_pending")][0]

        ok, message = guard_func("technical_review", "decision_pending")
        assert ok is False
        assert "Technical review is required" in message

    def test_guard_technical_review_to_decision_pending_not_approved(self):
        """Test guard_technical_review_to_decision_pending with review not approved."""
        audit = MockAudit()
        audit.technical_review = Mock()
        audit.technical_review.status = "pending"
        audit.technical_review.get_status_display.return_value = "Pending"

        sm = AuditStateMachine(audit)

        guards = sm._guards()
        guard_func = guards[("technical_review", "decision_pending")][0]

        ok, message = guard_func("technical_review", "decision_pending")
        assert ok is False
        assert "must be 'Approved'" in message

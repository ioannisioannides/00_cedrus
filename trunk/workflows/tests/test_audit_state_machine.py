from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.exceptions import ValidationError

from trunk.workflows.audit_state_machine import AuditStateMachine


class TestAuditStateMachine:
    def setup_method(self):
        self.audit = Mock()
        # Mock the class and objects manager for queries like self.audit.__class__.objects...
        self.audit.__class__ = Mock()
        self.audit.__class__.objects = Mock()

        self.audit.status = "draft"
        self.audit.STATUS_CHOICES = [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("report_draft", "Report Draft"),
            ("client_review", "Client Review"),
            ("submitted", "Submitted"),
            ("technical_review", "Technical Review"),
            ("decision_pending", "Decision Pending"),
            ("decided", "Decided"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ]
        self.audit.save = Mock()
        self.user = Mock()
        self.sm = AuditStateMachine(self.audit)

    def test_initial_state(self):
        assert self.sm._sm.current_state == "draft"

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_transition_cb_admin_override(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.sm.transition("scheduled", self.user)
        assert self.audit.status == "scheduled"
        mock_log.objects.create.assert_called_once()

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_transition_invalid_path(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        with pytest.raises(ValidationError, match="Invalid transition"):
            self.sm.transition("closed", self.user)
        assert self.audit.status == "draft"

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_draft_to_scheduled_success(self, mock_assigned, mock_is_lead, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user

        # Satisfy guard
        self.audit.total_audit_date_from = "2023-01-01"

        self.sm.transition("scheduled", self.user)
        assert self.audit.status == "scheduled"

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    def test_permission_draft_to_scheduled_fail_not_lead(self, mock_is_lead, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = False
        self.audit.lead_auditor = self.user
        self.audit.total_audit_date_from = "2023-01-01"

        with pytest.raises(ValidationError, match="You do not have permission"):
            self.sm.transition("scheduled", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_draft_to_scheduled_missing_date(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.lead_auditor = self.user
        self.audit.total_audit_date_from = None

        with pytest.raises(ValidationError, match="Audit date must be set"):
            self.sm.transition("scheduled", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_in_progress_to_report_draft_no_findings(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "in_progress"

        # Mock findings counts
        self.audit.nonconformity_set.count.return_value = 0
        self.audit.observation_set.count.return_value = 0
        self.audit.opportunityforimprovement_set.count.return_value = 0

        with pytest.raises(ValidationError, match="At least one finding"):
            self.sm.transition("report_draft", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_in_progress_to_report_draft_success(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "in_progress"

        # Mock findings counts
        self.audit.nonconformity_set.count.return_value = 1
        self.audit.observation_set.count.return_value = 0
        self.audit.opportunityforimprovement_set.count.return_value = 0

        self.sm.transition("report_draft", self.user)
        assert self.audit.status == "report_draft"

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_client_review_to_submitted_missing_response(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "client_review"

        nc = Mock()
        nc.category = "major"
        nc.client_root_cause = None
        nc.clause = "4.1"
        self.audit.nonconformity_set.filter.return_value = [nc]

        with pytest.raises(ValidationError, match="missing client response"):
            self.sm.transition("submitted", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_technical_review_to_decision_pending_missing_review(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "technical_review"
        del self.audit.technical_review  # Ensure attribute doesn't exist

        with pytest.raises(ValidationError, match="Technical review is required"):
            self.sm.transition("decision_pending", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_technical_review_to_decision_pending_not_approved(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "technical_review"
        self.audit.technical_review = Mock()
        self.audit.technical_review.status = "pending"
        self.audit.technical_review.get_status_display.return_value = "Pending"

        with pytest.raises(ValidationError, match="must be 'Approved'"):
            self.sm.transition("decision_pending", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_decision_pending_to_closed_stage2_missing_stage1(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "decision_pending"
        self.audit.audit_type = "stage2"

        # Mock query for previous stage 1
        # self.audit.__class__.objects.filter...exists()
        self.audit.__class__.objects.filter.return_value.exclude.return_value.exists.return_value = False

        with pytest.raises(ValidationError, match="requires a completed Stage 1"):
            self.sm.transition("closed", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_decision_pending_to_closed_surveillance_no_cert(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "decision_pending"
        self.audit.audit_type = "surveillance"
        self.audit.certifications.filter.return_value.exists.return_value = False

        with pytest.raises(ValidationError, match="requires active certifications"):
            self.sm.transition("closed", self.user)

    @patch("audit_management.models.AuditStatusLog")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_guard_decision_pending_to_closed_open_major_nc(self, mock_is_cb_admin, mock_log):
        mock_is_cb_admin.return_value = True
        self.audit.status = "decision_pending"
        self.audit.audit_type = "recertification"  # Not stage2 or surveillance

        nc = Mock()
        nc.clause = "9.2"
        qs = MagicMock()
        qs.exists.return_value = True
        qs.count.return_value = 1
        qs.__getitem__.return_value = [nc]  # For slicing [:3]
        qs.__iter__.return_value = iter([nc])
        self.audit.nonconformity_set.filter.return_value = qs

        with pytest.raises(ValidationError, match=r"major NC\(s\) still open"):
            self.sm.transition("closed", self.user)

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.can_conduct_technical_review")
    def test_permission_submitted_to_technical_review(self, mock_can_review, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_can_review.return_value = True
        self.audit.status = "submitted"

        can, _ = self.sm.can_transition("technical_review", self.user)
        assert can is True
        mock_can_review.assert_called_with(self.user)

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_decision_maker")
    @patch("trunk.permissions.policies.PBACPolicy.is_independent_for_decision")
    def test_permission_decision_pending_to_decided_decision_maker(
        self, mock_independent, mock_is_dm, mock_is_cb_admin
    ):
        mock_is_cb_admin.return_value = False
        mock_is_dm.return_value = True
        mock_independent.return_value = (True, "OK")
        self.audit.status = "decision_pending"

        can, _ = self.sm.can_transition("decided", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_decision_maker")
    @patch("trunk.permissions.policies.PBACPolicy.is_independent_for_decision")
    def test_permission_decision_pending_to_decided_conflict(self, mock_independent, mock_is_dm, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_dm.return_value = True
        mock_independent.return_value = (False, "Conflict")
        self.audit.status = "decision_pending"

        can, reason = self.sm.can_transition("decided", self.user)
        assert can is False
        assert "You do not have permission" in reason

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_scheduled_to_in_progress(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "scheduled"

        can, _ = self.sm.can_transition("in_progress", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_in_progress_to_report_draft(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "in_progress"

        # Mock guards to pass
        self.audit.nonconformity_set.count.return_value = 1
        self.audit.observation_set.count.return_value = 0
        self.audit.opportunityforimprovement_set.count.return_value = 0

        can, _ = self.sm.can_transition("report_draft", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_report_draft_to_client_review(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "report_draft"

        can, _ = self.sm.can_transition("client_review", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_report_draft_to_client_review_cb_admin(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = True
        self.audit.status = "report_draft"

        can, _ = self.sm.can_transition("client_review", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_report_draft_to_in_progress(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "report_draft"

        can, _ = self.sm.can_transition("in_progress", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_client_review_to_submitted(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "client_review"

        # Mock guards
        self.audit.nonconformity_set.filter.return_value = []

        can, _ = self.sm.can_transition("submitted", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.is_lead_auditor")
    @patch("trunk.permissions.policies.PBACPolicy.is_assigned_to_audit")
    def test_permission_client_review_to_report_draft(self, mock_assigned, mock_is_lead, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_is_lead.return_value = True
        mock_assigned.return_value = (True, "OK")
        self.audit.lead_auditor = self.user
        self.audit.status = "client_review"

        can, _ = self.sm.can_transition("report_draft", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    @patch("trunk.permissions.predicates.PermissionPredicate.can_conduct_technical_review")
    def test_permission_technical_review_to_decision_pending(self, mock_can_review, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        mock_can_review.return_value = True
        self.audit.status = "technical_review"

        # Mock guards
        self.audit.technical_review.status = "approved"

        can, _ = self.sm.can_transition("decision_pending", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_decision_pending_to_decided_cb_admin(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = True
        self.audit.status = "decision_pending"

        can, _ = self.sm.can_transition("decided", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_decided_to_closed(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        self.audit.status = "decided"

        can, _ = self.sm.can_transition("closed", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_decision_pending_to_closed_cb_admin(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = True
        self.audit.status = "decision_pending"

        # Mock guards
        self.audit.audit_type = "stage1"
        self.audit.nonconformity_set.filter.return_value.exists.return_value = False

        can, _ = self.sm.can_transition("closed", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_to_cancelled_cb_admin(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = True
        self.audit.status = "draft"

        can, _ = self.sm.can_transition("cancelled", self.user)
        assert can is True

    @patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin")
    def test_permission_to_cancelled_fail(self, mock_is_cb_admin):
        mock_is_cb_admin.return_value = False
        self.audit.status = "draft"

        can, _ = self.sm.can_transition("cancelled", self.user)
        assert can is False

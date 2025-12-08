from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from audit_management.models import Audit
from trunk.workflows.audit_state_machine import AuditStateMachine
from trunk.workflows.audit_workflow import AuditWorkflow

User = get_user_model()


class TestAuditWorkflowCoverageV2(TestCase):
    def setUp(self):
        self.audit = MagicMock(spec=Audit)
        self.audit.status = "draft"
        self.workflow = AuditWorkflow(self.audit)
        self.user = User.objects.create(username="testuser")

    def test_state_machine_permissions_cb_admin(self):
        # Test CB Admin permissions for specific transitions
        sm = AuditStateMachine(self.audit)

        # Patch the class where it is imported/used
        with patch("trunk.permissions.predicates.PermissionPredicate.is_cb_admin", return_value=True):
            # report_draft -> client_review
            self.audit.status = "report_draft"
            self.assertTrue(sm.can_transition("client_review", self.user)[0])

            # client_review -> submitted
            self.audit.status = "client_review"
            self.assertTrue(sm.can_transition("submitted", self.user)[0])

    def test_state_machine_permissions_decision_maker(self):
        sm = AuditStateMachine(self.audit)
        self.audit.status = "decision_pending"

        with patch("trunk.permissions.predicates.PermissionPredicate.is_decision_maker", return_value=True):
            with patch("trunk.permissions.policies.PBACPolicy.is_independent_for_decision", return_value=(True, "")):
                # decision_pending -> decided
                self.assertTrue(sm.can_transition("decided", self.user)[0])

    def test_guard_draft_to_scheduled_no_lead_auditor(self):
        sm = AuditStateMachine(self.audit)
        self.audit.status = "draft"
        self.audit.lead_auditor = None
        self.audit.total_audit_date_from = "2023-01-01"

        # Access the internal state machine to run guards directly
        ok, msg = sm._sm._run_guards("scheduled")
        self.assertFalse(ok)
        self.assertIn("Lead auditor must be assigned", msg)

    def test_guard_technical_review_to_decision_pending_no_review(self):
        sm = AuditStateMachine(self.audit)
        self.audit.status = "technical_review"
        # Ensure audit does not have technical_review attribute
        del self.audit.technical_review

        # We need to mock hasattr to return False for technical_review
        class MockAudit:
            status = "technical_review"

        sm.audit = MockAudit()
        sm._sm._obj = sm.audit

        ok, msg = sm._sm._run_guards("decision_pending")
        self.assertFalse(ok)
        self.assertIn("Technical review is required", msg)

    def test_guard_technical_review_to_decision_pending_not_approved(self):
        sm = AuditStateMachine(self.audit)
        self.audit.status = "technical_review"
        review = MagicMock()
        review.status = "pending"
        review.get_status_display.return_value = "Pending"
        self.audit.technical_review = review

        ok, msg = sm._sm._run_guards("decision_pending")
        self.assertFalse(ok)
        self.assertIn("must be 'Approved'", msg)

    def test_validate_transition_submitted(self):
        # Test explicit call to validate_transition for 'submitted'
        # This hits the elif new_status == "submitted" block
        self.audit.status = "client_review"

        # Mock _validate_submitted to avoid complex setup
        with patch.object(AuditWorkflow, "_validate_submitted") as mock_val:
            self.workflow.validate_transition("submitted")
            mock_val.assert_called_once()

    def test_validate_in_progress_no_date(self):
        self.audit.lead_auditor = self.user
        self.audit.total_audit_date_from = None

        with self.assertRaises(ValidationError) as cm:
            self.workflow._validate_in_progress()
        self.assertIn("Cannot start audit without audit dates", str(cm.exception))

    def test_validate_closed_no_previous_stage1(self):
        self.audit.audit_type = "stage2"
        self.audit.organization = MagicMock()

        # Mock objects.filter...exists to return False
        # We need to mock the chain: self.audit.__class__.objects.filter().exclude().exists()

        # Create a mock class for the audit
        MockAuditClass = MagicMock()
        self.audit.__class__ = MockAuditClass

        mock_qs = MagicMock()
        mock_qs.exclude.return_value.exists.return_value = False

        MockAuditClass.objects.filter.return_value = mock_qs

        with self.assertRaises(ValidationError) as cm:
            self.workflow._validate_closed()
        self.assertIn("Stage 2 audit requires a completed Stage 1", str(cm.exception))

    def test_validate_closed_open_major_ncs(self):
        self.audit.audit_type = "recertification"  # Not stage2 or surveillance

        # Mock open major NCs
        mock_nc = MagicMock()
        mock_nc.clause = "9.2"

        mock_qs = MagicMock()
        mock_qs.exists.return_value = True
        mock_qs.count.return_value = 1
        # When sliced, return a list of mocks
        mock_qs.__getitem__.return_value = [mock_nc]
        mock_qs.__iter__.return_value = [mock_nc]

        self.audit.nonconformity_set.filter.return_value = mock_qs

        with self.assertRaises(ValidationError) as cm:
            self.workflow._validate_closed()
        self.assertIn("major NC(s) still open", str(cm.exception))

    def test_get_available_transitions_with_validation_error(self):
        # Mock TRANSITIONS to return a status that fails validation
        with patch.object(AuditWorkflow, "TRANSITIONS", {"draft": ["scheduled"]}):
            self.audit.status = "draft"

            # Mock validate_transition to raise ValidationError
            with patch.object(self.workflow, "validate_transition", side_effect=ValidationError("Fail")):
                transitions = self.workflow.get_available_transitions()

                # Should return the transition but with available=False
                self.assertEqual(len(transitions), 1)
                self.assertEqual(transitions[0]["code"], "scheduled")
                self.assertFalse(transitions[0]["available"])
                self.assertEqual(transitions[0]["reason"], "['Fail']")

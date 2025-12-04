from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from audit_management.models import Audit, Nonconformity
from certification.models import TechnicalReview
from core.models import Certification, Organization, Standard
from trunk.workflows.audit_state_machine import AuditStateMachine


class AuditStateMachineTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Test Org", customer_id="CUST001", total_employee_count=10)
        self.standard = Standard.objects.create(title="ISO 9001", code="9001")
        self.certification = Certification.objects.create(
            organization=self.organization,
            standard=self.standard,
            certificate_status="active",
            expiry_date=timezone.now().date() + timedelta(days=365),
        )
        self.user = User.objects.create_user(username="auditor", password="password")
        self.audit = Audit.objects.create(
            organization=self.organization,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=timezone.now().date(),
            total_audit_date_to=timezone.now().date() + timedelta(days=2),
            created_by=self.user,
            lead_auditor=self.user,
        )
        self.audit.certifications.add(self.certification)
        self.sm = AuditStateMachine(self.audit)

    def test_initial_state(self):
        self.assertEqual(self.sm.audit.status, "draft")

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_draft_to_scheduled_success(self, mock_pbac, mock_predicate):
        # Setup permissions
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)

        # Ensure guard passes (lead_auditor and date are set in setUp)
        self.assertTrue(self.sm.can_transition("scheduled", self.user))
        self.sm.transition("scheduled", self.user)
        self.assertEqual(self.audit.status, "scheduled")

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_draft_to_scheduled_guard_fail(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = True
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)

        # Fail guard: no lead auditor
        self.audit.lead_auditor = None
        self.audit.save()

        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("scheduled", self.user)
        self.assertIn("Lead auditor must be assigned", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_in_progress_to_report_draft_guard_fail(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)

        self.audit.status = "in_progress"
        self.audit.save()

        # Fail guard: no findings
        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("report_draft", self.user)
        self.assertIn("At least one finding", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_in_progress_to_report_draft_success(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)

        self.audit.status = "in_progress"
        self.audit.save()

        # Add finding
        Nonconformity.objects.create(
            audit=self.audit, clause="4.1", statement_of_nc="Test NC", category="minor", created_by=self.user
        )

        self.sm.transition("report_draft", self.user)
        self.assertEqual(self.audit.status, "report_draft")

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_client_review_to_submitted_guard_fail(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)

        self.audit.status = "client_review"
        self.audit.save()

        # Add Major NC without response
        Nonconformity.objects.create(
            audit=self.audit, clause="4.1", statement_of_nc="Major NC", category="major", created_by=self.user
        )

        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("submitted", self.user)
        self.assertIn("Major NC (Clause 4.1) is missing client response", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_technical_review_to_decision_pending_guard_fail(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.can_conduct_technical_review.return_value = True

        self.audit.status = "technical_review"
        self.audit.save()

        # No technical review object
        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("decision_pending", self.user)
        self.assertIn("Technical review is required", str(cm.exception))

        # Technical review not approved
        TechnicalReview.objects.create(audit=self.audit, status="in_progress", reviewer=self.user)
        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("decision_pending", self.user)
        self.assertIn("must be 'Approved'", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_decision_pending_to_closed_guard_fail_stage2(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = True

        self.audit.status = "decision_pending"
        self.audit.audit_type = "stage2"
        self.audit.save()

        # No Stage 1
        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("closed", self.user)
        self.assertIn("Stage 2 audit requires a completed Stage 1 audit", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_permission_denied(self, mock_pbac, mock_predicate):
        mock_predicate.is_lead_auditor.return_value = False
        mock_predicate.is_cb_admin.return_value = False
        mock_pbac.is_assigned_to_audit.return_value = (False, "Not assigned")

        self.assertFalse(self.sm.can_transition("scheduled", self.user)[0])

        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("scheduled", self.user)
        self.assertIn("You do not have permission to perform this transition", str(cm.exception))

    def test_available_transitions(self):
        # Mock permissions to allow everything for simplicity in this test
        with patch("trunk.permissions.predicates.PermissionPredicate") as mock_pred:
            mock_pred.is_cb_admin.return_value = True
            transitions = self.sm.available_transitions(self.user)
            # From draft, can go to scheduled or cancelled
            target_states = [t[0] for t in transitions]
            self.assertIn("scheduled", target_states)
            self.assertIn("cancelled", target_states)

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_other_transitions(self, mock_pbac, mock_predicate):
        # Setup common permissions
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = True
        mock_pbac.is_assigned_to_audit.return_value = (True, None)
        mock_predicate.can_conduct_technical_review.return_value = True
        mock_predicate.is_decision_maker.return_value = True
        mock_pbac.is_independent_for_decision.return_value = (True, None)

        # scheduled -> in_progress
        self.audit.status = "scheduled"
        self.audit.save()
        self.assertTrue(self.sm.can_transition("in_progress", self.user)[0])
        self.sm.transition("in_progress", self.user)
        self.assertEqual(self.audit.status, "in_progress")

        # report_draft -> client_review
        self.audit.status = "report_draft"
        self.audit.save()
        self.assertTrue(self.sm.can_transition("client_review", self.user)[0])
        self.sm.transition("client_review", self.user)
        self.assertEqual(self.audit.status, "client_review")

        # client_review -> report_draft (back)
        self.assertTrue(self.sm.can_transition("report_draft", self.user)[0])
        self.sm.transition("report_draft", self.user)
        self.assertEqual(self.audit.status, "report_draft")

        # report_draft -> in_progress (back)
        self.assertTrue(self.sm.can_transition("in_progress", self.user)[0])
        self.sm.transition("in_progress", self.user)
        self.assertEqual(self.audit.status, "in_progress")

        # submitted -> technical_review
        self.audit.status = "submitted"
        self.audit.save()
        self.assertTrue(self.sm.can_transition("technical_review", self.user)[0])
        self.sm.transition("technical_review", self.user)
        self.assertEqual(self.audit.status, "technical_review")

        # technical_review -> decision_pending
        # Need approved technical review
        TechnicalReview.objects.create(audit=self.audit, status="approved", reviewer=self.user)
        self.assertTrue(self.sm.can_transition("decision_pending", self.user)[0])
        self.sm.transition("decision_pending", self.user)
        self.assertEqual(self.audit.status, "decision_pending")

        # decision_pending -> decided
        self.assertTrue(self.sm.can_transition("decided", self.user)[0])
        self.sm.transition("decided", self.user)
        self.assertEqual(self.audit.status, "decided")

        # decided -> closed
        self.assertTrue(self.sm.can_transition("closed", self.user)[0])
        self.sm.transition("closed", self.user)
        self.assertEqual(self.audit.status, "closed")

        # Cancelled
        mock_predicate.is_cb_admin.return_value = True
        self.audit.status = "draft"
        self.audit.save()
        self.assertTrue(self.sm.can_transition("cancelled", self.user)[0])
        self.sm.transition("cancelled", self.user)
        self.assertEqual(self.audit.status, "cancelled")

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_permissions_failures(self, mock_pbac, mock_predicate):
        # Setup to fail permissions
        mock_predicate.is_cb_admin.return_value = False
        mock_predicate.is_lead_auditor.return_value = False
        mock_pbac.is_assigned_to_audit.return_value = (False, "Not assigned")
        mock_predicate.can_conduct_technical_review.return_value = False
        mock_predicate.is_decision_maker.return_value = False

        # report_draft -> client_review
        self.audit.status = "report_draft"
        self.audit.save()
        self.assertFalse(self.sm.can_transition("client_review", self.user)[0])

        # report_draft -> in_progress
        self.assertFalse(self.sm.can_transition("in_progress", self.user)[0])

        # client_review -> submitted
        self.audit.status = "client_review"
        self.audit.save()
        self.assertFalse(self.sm.can_transition("submitted", self.user)[0])

        # client_review -> report_draft
        self.assertFalse(self.sm.can_transition("report_draft", self.user)[0])

        # submitted -> technical_review
        self.audit.status = "submitted"
        self.audit.save()
        self.assertFalse(self.sm.can_transition("technical_review", self.user)[0])

        # technical_review -> decision_pending
        self.audit.status = "technical_review"
        self.audit.save()
        self.assertFalse(self.sm.can_transition("decision_pending", self.user)[0])

        # decision_pending -> decided
        self.audit.status = "decision_pending"
        self.audit.save()
        self.assertFalse(self.sm.can_transition("decided", self.user)[0])

        # decision_pending -> closed
        self.assertFalse(self.sm.can_transition("closed", self.user)[0])

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_decision_pending_to_closed_guard_fail_surveillance(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = True

        self.audit.status = "decision_pending"
        self.audit.audit_type = "surveillance"
        self.audit.save()

        # No active certifications (setUp creates one, so let's deactivate it)
        self.certification.certificate_status = "suspended"
        self.certification.save()

        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("closed", self.user)
        self.assertIn("Surveillance audit requires active certifications", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_decision_pending_to_closed_guard_fail_open_major_nc(self, mock_pbac, mock_predicate):
        mock_predicate.is_cb_admin.return_value = True

        self.audit.status = "decision_pending"
        self.audit.save()

        # Open Major NC
        Nonconformity.objects.create(
            audit=self.audit,
            clause="4.1",
            statement_of_nc="Major NC",
            category="major",
            verification_status="open",
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as cm:
            self.sm.transition("closed", self.user)
        self.assertIn("major NC(s) still open", str(cm.exception))

    @patch("trunk.permissions.predicates.PermissionPredicate")
    @patch("trunk.permissions.policies.PBACPolicy")
    def test_transition_decision_pending_permissions_branches(self, mock_pbac, mock_predicate):
        self.audit.status = "decision_pending"
        self.audit.save()

        # Case 1: Decision Maker but NOT independent -> False
        mock_predicate.is_decision_maker.return_value = True
        mock_predicate.is_cb_admin.return_value = False  # Ensure this is False
        mock_pbac.is_independent_for_decision.return_value = (False, "Not independent")

        self.assertFalse(self.sm.can_transition("decided", self.user)[0])
        self.assertFalse(self.sm.can_transition("closed", self.user)[0])

        # Case 2: NOT Decision Maker, but IS CB Admin -> True
        mock_predicate.is_decision_maker.return_value = False
        mock_predicate.is_cb_admin.return_value = True

        self.assertTrue(self.sm.can_transition("decided", self.user)[0])
        self.assertTrue(self.sm.can_transition("closed", self.user)[0])

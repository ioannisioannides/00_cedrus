"""
Test audit workflow state machine.

Sprint 8, Task 8.4: Workflow validation tests
"""

# pylint: disable=redefined-outer-name,unused-argument

import pytest
from django.core.exceptions import ValidationError

from audits.models import Audit, Nonconformity
from core.models import Organization, Standard
from core.test_utils import TEST_PASSWORD
from trunk.workflows.audit_state_machine import AuditStateMachine


@pytest.fixture
def organization(db):
    """Create test organization."""
    return Organization.objects.create(
        name="Test Org",
        customer_id="TEST001",
        registered_address="123 Test St",
        total_employee_count=50,
    )


@pytest.fixture
def standard(db):
    """Create test standard."""
    return Standard.objects.create(code="ISO 9001", title="Quality Management")


@pytest.fixture
def audit_draft(db, organization):
    """Create draft audit."""
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    creator = user_model.objects.create_user(username="creator", password=TEST_PASSWORD)  # nosec B106

    return Audit.objects.create(
        organization=organization,
        audit_type="stage1",
        status="draft",
        created_by=creator,
        lead_auditor=creator,
        total_audit_date_from="2025-12-01",
        total_audit_date_to="2025-12-03",
    )


@pytest.mark.django_db
class TestAuditWorkflowTransitions:
    """Test valid and invalid workflow transitions."""

    def test_draft_to_scheduled_valid(self, audit_draft):
        """Test valid transition from draft to scheduled."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        lead_group = Group.objects.create(name="lead_auditor")
        auditor.groups.add(lead_group)

        audit_draft.lead_auditor = auditor
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        audit = workflow.transition("scheduled", user=auditor)

        assert audit.status == "scheduled"

    def test_draft_to_scheduled_no_auditor_fails(self, audit_draft):
        """Test transition fails if user is not the assigned lead auditor."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        # Create a user who is a lead auditor but NOT assigned to this audit
        other_auditor = user_model.objects.create_user(username="other", password=TEST_PASSWORD)  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        other_auditor.groups.add(lead_group)

        # Assign a different auditor
        assigned_auditor = user_model.objects.create_user(username="assigned", password=TEST_PASSWORD)  # nosec B106
        assigned_auditor.groups.add(lead_group)

        audit_draft.lead_auditor = assigned_auditor
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        # Should fail because user is not the assigned lead auditor
        ok, _ = workflow.can_transition("scheduled", other_auditor)
        assert not ok
        # The reason comes from permission checker returning False, which usually results in a generic message
        # or we can check that it returned False.

    def test_invalid_transition_fails(self, audit_draft):
        """Test invalid transition is rejected."""
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = user_model.objects.create_user(username="checker", password=TEST_PASSWORD)  # nosec B106

        workflow = AuditStateMachine(audit_draft)
        with pytest.raises(ValidationError):
            workflow.transition("closed", user=user)

    def test_report_draft_requires_findings(self, audit_draft):
        """Test cannot move to report_draft without findings."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        auditor.groups.add(lead_group)

        # Assign auditor to audit so they have permission
        audit_draft.lead_auditor = auditor
        audit_draft.scheduled_date = "2025-12-01"
        audit_draft.status = "in_progress"
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        with pytest.raises(ValidationError, match="At least one finding"):
            workflow.transition("report_draft", user=auditor)

    def test_submitted_requires_nc_responses(self, audit_draft, standard):
        """Test cannot submit without client responses to major NCs."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        auditor.groups.add(lead_group)

        audit_draft.lead_auditor = auditor

        # Create major NC without response
        Nonconformity.objects.create(
            audit=audit_draft,
            standard=standard,
            clause="7.1",
            category="major",
            objective_evidence="Test",
            statement_of_nc="Test NC",
            auditor_explanation="Test",
            created_by=auditor,
        )

        audit_draft.status = "client_review"
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        with pytest.raises(ValidationError, match="missing client response"):
            workflow.transition("submitted", user=auditor)

    def test_closed_requires_verified_ncs(self, audit_draft, standard):
        """Test cannot close with open NCs."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        # Make auditor a CB admin to allow closing
        cb_group = Group.objects.create(name="cb_admin")
        auditor.groups.add(cb_group)

        # Create NC that's still open
        Nonconformity.objects.create(
            audit=audit_draft,
            standard=standard,
            clause="7.1",
            category="major",
            objective_evidence="Test",
            statement_of_nc="Test NC",
            auditor_explanation="Test",
            created_by=auditor,
            verification_status="open",
        )

        audit_draft.status = "decision_pending"
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        with pytest.raises(ValidationError, match="still open"):
            workflow.transition("closed", user=auditor)

    def test_get_available_transitions(self, audit_draft):
        """Test getting available transitions."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        # Need a user with permissions (e.g. Lead Auditor)
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        auditor.groups.add(lead_group)

        audit_draft.lead_auditor = auditor
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)
        transitions = workflow.available_transitions(auditor)

        # transitions is a list of tuples (code, label)

        assert len(transitions) >= 1
        codes = [t[0] for t in transitions]
        assert "scheduled" in codes

    def test_can_transition_to(self, audit_draft):
        """Test checking if transition is allowed."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        user_model = get_user_model()
        auditor = user_model.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        auditor.groups.add(lead_group)

        audit_draft.lead_auditor = auditor
        audit_draft.save()

        workflow = AuditStateMachine(audit_draft)

        ok, _ = workflow.can_transition("scheduled", auditor)
        assert ok is True

        ok, _ = workflow.can_transition("closed", auditor)
        assert ok is False

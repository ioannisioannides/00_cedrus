"""
Comprehensive tests for trunk module: permissions, events, services.

Tests for:
- trunk/permissions/policies.py
- trunk/events/handlers.py
- trunk/events/dispatcher.py
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.test import TestCase

from accounts.models import Profile
from core.models import Certification, Organization, Site, Standard

from trunk.events import EventType, event_dispatcher
from trunk.events.dispatcher import EventDispatcher
from trunk.events.handlers import (
    on_appeal_received,
    on_audit_status_changed,
    on_certificate_history_created,
    on_complaint_received,
    on_nc_verified,
    register_event_handlers,
)
from trunk.permissions.policies import PBACPolicy
from trunk.permissions.predicates import PermissionPredicate


# ==============================================================================
# PERMISSION POLICIES TESTS
# ==============================================================================


class PBACPolicyTest(TestCase):
    """Test Policy-Based Access Control policies."""

    def setUp(self):
        """Set up test users and audit."""
        # Create groups
        self.cb_group = Group.objects.create(name="cb_admin")
        self.lead_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_user_group = Group.objects.create(name="client_user")
        self.tech_reviewer_group = Group.objects.create(name="technical_reviewer")
        self.decision_maker_group = Group.objects.create(name="decision_maker")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")  # nosec B106
        self.cb_admin.groups.add(self.cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")  # nosec B106
        self.lead_auditor.groups.add(self.lead_group)

        self.auditor = User.objects.create_user(username="auditor", password="pass")  # nosec B106
        self.auditor.groups.add(self.auditor_group)

        self.client_user = User.objects.create_user(username="client", password="pass")  # nosec B106
        self.client_user.groups.add(self.client_user_group)

        self.tech_reviewer = User.objects.create_user(username="tech", password="pass")  # nosec B106
        self.tech_reviewer.groups.add(self.tech_reviewer_group)

        self.decision_maker = User.objects.create_user(username="decision", password="pass")  # nosec B106
        self.decision_maker.groups.add(self.decision_maker_group)

        # Create organization
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Test",
            certificate_status="active",
        )

        self.site = Site.objects.create(organization=self.org, site_name="Site 1", site_address="123 St")

        # Create profile for client user
        # Profile is created by signal, so we just need to update it
        self.client_user.refresh_from_db()
        if hasattr(self.client_user, "profile"):
            self.client_user.profile.organization = self.org
            self.client_user.profile.save()
        else:
            Profile.objects.create(user=self.client_user, organization=self.org)

        # Import and create audit
        from audits.models import Audit

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="draft",
            lead_auditor=self.lead_auditor,
            created_by=self.cb_admin,
        )
        self.audit.certifications.add(self.cert)
        self.audit.sites.add(self.site)

    def test_is_independent_for_decision_cb_admin_bypass(self):
        """Test CB Admin can always make decisions."""
        allowed, reason = PBACPolicy.is_independent_for_decision(self.cb_admin, self.audit)
        self.assertTrue(allowed)
        self.assertIn("CB Admin", reason)

    def test_is_independent_for_decision_lead_auditor_not_allowed(self):
        """Test lead auditor cannot make decision on their own audit."""
        allowed, reason = PBACPolicy.is_independent_for_decision(self.lead_auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("lead auditor", reason)

    def test_is_independent_for_decision_team_member_not_allowed(self):
        """Test team member cannot make decision on their audit."""
        from audits.models import AuditTeamMember

        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            date_from=date.today(),
            date_to=date.today() + timedelta(days=1),
        )
        allowed, reason = PBACPolicy.is_independent_for_decision(self.auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("team member", reason)

    def test_is_independent_for_decision_independent_user_allowed(self):
        """Test independent user can make decision."""
        allowed, reason = PBACPolicy.is_independent_for_decision(self.decision_maker, self.audit)
        self.assertTrue(allowed)
        self.assertIn("independence", reason)

    def test_can_user_access_organization_cb_admin(self):
        """Test CB Admin can access all organizations."""
        allowed, reason = PBACPolicy.can_user_access_organization(self.cb_admin, self.audit)
        self.assertTrue(allowed)
        self.assertIn("all organizations", reason)

    def test_can_user_access_organization_auditor(self):
        """Test auditors can access all organizations."""
        allowed, reason = PBACPolicy.can_user_access_organization(self.auditor, self.audit)
        self.assertTrue(allowed)
        self.assertIn("all organizations", reason)

    def test_can_user_access_organization_client_user_own_org(self):
        """Test client user can access their own organization."""
        allowed, reason = PBACPolicy.can_user_access_organization(self.client_user, self.audit)
        self.assertTrue(allowed)
        self.assertIn("belongs to this organization", reason)

    def test_can_user_access_organization_client_user_other_org(self):
        """Test client user cannot access other organization."""
        other_org = Organization.objects.create(
            name="Other Org",
            registered_address="456 St",
            customer_id="ORG002",
            total_employee_count=5,
        )
        from audits.models import Audit

        other_audit = Audit.objects.create(
            organization=other_org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="draft",
            lead_auditor=self.lead_auditor,
            created_by=self.cb_admin,
        )
        allowed, reason = PBACPolicy.can_user_access_organization(self.client_user, other_audit)
        self.assertFalse(allowed)
        self.assertIn("only access audits for their own organization", reason)

    def test_can_user_access_organization_unknown_role(self):
        """Test unknown role cannot access organization."""
        other_user = User.objects.create_user(username="other", password="pass")  # nosec B106
        allowed, reason = PBACPolicy.can_user_access_organization(other_user, self.audit)
        self.assertFalse(allowed)
        self.assertIn("does not have permission", reason)

    def test_is_assigned_to_audit_cb_admin(self):
        """Test CB Admin is always considered assigned."""
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.cb_admin, self.audit)
        self.assertTrue(allowed)
        self.assertIn("CB Admin", reason)

    def test_is_assigned_to_audit_lead_auditor(self):
        """Test lead auditor is assigned."""
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.lead_auditor, self.audit)
        self.assertTrue(allowed)
        self.assertIn("lead auditor", reason)

    def test_is_assigned_to_audit_team_member(self):
        """Test team member is assigned."""
        from audits.models import AuditTeamMember

        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            date_from=date.today(),
            date_to=date.today() + timedelta(days=1),
        )
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.auditor, self.audit)
        self.assertTrue(allowed)
        self.assertIn("team member", reason)

    def test_is_assigned_to_audit_not_assigned(self):
        """Test non-assigned user is not assigned."""
        allowed, reason = PBACPolicy.is_assigned_to_audit(self.decision_maker, self.audit)
        self.assertFalse(allowed)
        self.assertIn("not assigned", reason)

    def test_can_conduct_technical_review_tech_reviewer(self):
        """Test technical reviewer can conduct review."""
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.tech_reviewer, self.audit)
        self.assertTrue(allowed)
        self.assertIn("can conduct technical review", reason)

    def test_can_conduct_technical_review_cb_admin(self):
        """Test CB Admin can conduct review."""
        allowed, _ = PBACPolicy.can_conduct_technical_review(self.cb_admin, self.audit)
        self.assertTrue(allowed)

    def test_can_conduct_technical_review_not_allowed(self):
        """Test regular user cannot conduct review."""
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("must be a technical reviewer", reason)

    def test_can_conduct_technical_review_lead_auditor_not_allowed(self):
        """Test lead auditor cannot review their own audit."""
        self.lead_auditor.groups.add(self.tech_reviewer_group)
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.lead_auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("cannot be the lead auditor", reason)

    def test_can_conduct_technical_review_team_member_not_allowed(self):
        """Test team member cannot review their own audit."""
        from audits.models import AuditTeamMember

        self.auditor.groups.add(self.tech_reviewer_group)
        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            date_from=date.today(),
            date_to=date.today() + timedelta(days=1),
        )
        allowed, reason = PBACPolicy.can_conduct_technical_review(self.auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("cannot be a team member", reason)

    def test_can_make_certification_decision_decision_maker(self):
        """Test decision maker can make certification decision."""
        allowed, _ = PBACPolicy.can_make_certification_decision(self.decision_maker, self.audit)
        self.assertTrue(allowed)

    def test_can_make_certification_decision_cb_admin(self):
        """Test CB Admin can make certification decision."""
        allowed, _ = PBACPolicy.can_make_certification_decision(self.cb_admin, self.audit)
        self.assertTrue(allowed)

    def test_can_make_certification_decision_not_allowed(self):
        """Test regular user cannot make certification decision."""
        allowed, reason = PBACPolicy.can_make_certification_decision(self.auditor, self.audit)
        self.assertFalse(allowed)
        self.assertIn("must be a decision maker", reason)


# ==============================================================================
# EVENT HANDLERS TESTS
# ==============================================================================


class EventHandlersTest(TestCase):
    """Test event handlers for audit lifecycle."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certification_scope="Test",
            certificate_status="active",
        )

        from audits.models import Audit

        self.user = User.objects.create_user(username="test", password="pass")  # nosec B106
        self.lead_auditor = User.objects.create_user(username="lead_auditor", password="pass")  # nosec B106
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="draft",
            lead_auditor=self.lead_auditor,
            created_by=self.user,
        )

    def test_on_audit_status_changed_to_client_review(self):
        """Test handler for status change to client_review."""
        events = []
        event_dispatcher.register(EventType.AUDIT_SUBMITTED_TO_CLIENT, lambda p: events.append(p))

        on_audit_status_changed(
            {"audit": self.audit, "new_status": "client_review", "changed_by": self.user}
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["audit"], self.audit)

    def test_on_audit_status_changed_to_submitted(self):
        """Test handler for status change to submitted."""
        events = []
        event_dispatcher.register(EventType.AUDIT_SUBMITTED_TO_CB, lambda p: events.append(p))

        on_audit_status_changed(
            {"audit": self.audit, "new_status": "submitted", "changed_by": self.user}
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["audit"], self.audit)

    def test_on_audit_status_changed_to_decided(self):
        """Test handler for status change to decided."""
        events = []
        event_dispatcher.register(EventType.AUDIT_DECIDED, lambda p: events.append(p))

        on_audit_status_changed(
            {"audit": self.audit, "new_status": "decided", "changed_by": self.user}
        )

        self.assertEqual(len(events), 1)

    def test_on_audit_status_changed_missing_audit(self):
        """Test handler with missing audit returns early."""
        events = []
        event_dispatcher.register(EventType.AUDIT_SUBMITTED_TO_CLIENT, lambda p: events.append(p))

        on_audit_status_changed({"new_status": "client_review", "changed_by": self.user})

        self.assertEqual(len(events), 0)

    def test_on_audit_status_changed_missing_status(self):
        """Test handler with missing status returns early."""
        events = []
        event_dispatcher.register(EventType.AUDIT_SUBMITTED_TO_CLIENT, lambda p: events.append(p))

        on_audit_status_changed({"audit": self.audit, "changed_by": self.user})

        self.assertEqual(len(events), 0)

    def test_on_nc_verified_accepted(self):
        """Test handler for NC verification accepted."""
        events = []
        event_dispatcher.register(EventType.NC_VERIFIED_ACCEPTED, lambda p: events.append(p))

        from audits.models import Nonconformity

        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            created_by=self.user,
        )

        on_nc_verified({"nc": nc, "verification_status": "accepted"})

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["nc"], nc)

    def test_on_nc_verified_rejected(self):
        """Test handler for NC verification rejected."""
        events = []
        event_dispatcher.register(EventType.NC_VERIFIED_REJECTED, lambda p: events.append(p))

        from audits.models import Nonconformity

        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            created_by=self.user,
        )

        on_nc_verified({"nc": nc, "verification_status": "rejected"})

        self.assertEqual(len(events), 1)

    def test_on_nc_verified_closed(self):
        """Test handler for NC closed."""
        events = []
        event_dispatcher.register(EventType.NC_CLOSED, lambda p: events.append(p))

        from audits.models import Nonconformity

        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            created_by=self.user,
        )

        on_nc_verified({"nc": nc, "verification_status": "closed"})

        self.assertEqual(len(events), 1)

    def test_on_nc_verified_missing_nc(self):
        """Test handler with missing NC returns early."""
        events = []
        event_dispatcher.register(EventType.NC_VERIFIED_ACCEPTED, lambda p: events.append(p))

        on_nc_verified({"verification_status": "accepted"})

        self.assertEqual(len(events), 0)

    def test_on_nc_verified_missing_status(self):
        """Test handler with missing status returns early."""
        events = []
        event_dispatcher.register(EventType.NC_VERIFIED_ACCEPTED, lambda p: events.append(p))

        from audits.models import Nonconformity

        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            created_by=self.user,
        )

        on_nc_verified({"nc": nc})

        self.assertEqual(len(events), 0)

    def test_on_complaint_received(self):
        """Test handler for complaint received."""
        mock_complaint = MagicMock()
        mock_complaint.complaint_number = "C001"
        mock_complaint.complainant_name = "Test Complainant"

        # Should not raise
        on_complaint_received({"complaint": mock_complaint})

    def test_on_appeal_received(self):
        """Test handler for appeal received."""
        mock_appeal = MagicMock()
        mock_appeal.appeal_number = "A001"
        mock_appeal.appellant_name = "Test Appellant"

        # Should not raise
        on_appeal_received({"appeal": mock_appeal})

    def test_on_certificate_history_created(self):
        """Test handler for certificate history created."""
        mock_history = MagicMock()
        mock_history.action = "issued"
        mock_history.certification.certificate_id = "CERT001"

        # Should not raise
        on_certificate_history_created({"history": mock_history})

    def test_register_event_handlers(self):
        """Test that register_event_handlers registers all handlers."""
        # Clear existing handlers
        event_dispatcher.clear()

        # Register handlers
        register_event_handlers()

        # Verify handlers are registered
        self.assertTrue(len(event_dispatcher._handlers) > 0)


# ==============================================================================
# EVENT DISPATCHER TESTS
# ==============================================================================


class EventDispatcherTest(TestCase):
    """Test event dispatcher functionality."""

    def setUp(self):
        """Set up fresh dispatcher."""
        self.dispatcher = EventDispatcher()
        self.events_received = []

    def test_register_and_emit(self):
        """Test basic register and emit."""

        def handler(payload):
            self.events_received.append(payload)

        self.dispatcher.register(EventType.AUDIT_CREATED, handler)
        self.dispatcher.emit(EventType.AUDIT_CREATED, {"test": "data"})

        self.assertEqual(len(self.events_received), 1)
        self.assertEqual(self.events_received[0]["test"], "data")

    def test_multiple_handlers(self):
        """Test multiple handlers for same event."""

        def handler1(payload):
            self.events_received.append(("h1", payload))

        def handler2(payload):
            self.events_received.append(("h2", payload))

        self.dispatcher.register(EventType.AUDIT_CREATED, handler1)
        self.dispatcher.register(EventType.AUDIT_CREATED, handler2)
        self.dispatcher.emit(EventType.AUDIT_CREATED, {"test": "data"})

        self.assertEqual(len(self.events_received), 2)

    def test_clear(self):
        """Test clearing handlers."""

        def handler(payload):
            self.events_received.append(payload)

        self.dispatcher.register(EventType.AUDIT_CREATED, handler)
        self.dispatcher.clear()
        self.dispatcher.emit(EventType.AUDIT_CREATED, {"test": "data"})

        self.assertEqual(len(self.events_received), 0)

    def test_emit_no_handlers(self):
        """Test emit with no handlers doesn't error."""
        # Should not raise
        self.dispatcher.emit(EventType.AUDIT_CREATED, {"test": "data"})

    def test_handler_exception_logged(self):
        """Test handler exceptions are logged but don't stop other handlers."""

        def bad_handler(payload):
            raise ValueError("Test error")

        def good_handler(payload):
            self.events_received.append(payload)

        self.dispatcher.register(EventType.AUDIT_CREATED, bad_handler)
        self.dispatcher.register(EventType.AUDIT_CREATED, good_handler)

        # Should not raise, and good handler should still be called
        self.dispatcher.emit(EventType.AUDIT_CREATED, {"test": "data"})

        self.assertEqual(len(self.events_received), 1)

    def tearDown(self):
        """Clean up."""
        self.dispatcher.clear()

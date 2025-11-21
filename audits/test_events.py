"""
Event system testing.

Tests that events are properly emitted during audit and finding lifecycle operations.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase

from audits.models import Audit, Nonconformity
from core.models import Certification, Organization, Site, Standard
from trunk.events import EventType, event_dispatcher
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService


class EventSystemTest(TestCase):
    """Test event dispatcher and event emissions."""

    def setUp(self):
        """Set up test data and event listeners."""
        self.events_received = []

        # Register event handlers
        def event_handler(payload):
            self.events_received.append(payload)

        event_dispatcher.register(EventType.AUDIT_CREATED, event_handler)
        event_dispatcher.register(EventType.AUDIT_UPDATED, event_handler)
        event_dispatcher.register(EventType.AUDIT_STATUS_CHANGED, event_handler)
        event_dispatcher.register(EventType.FINDING_CREATED, event_handler)
        event_dispatcher.register(EventType.NC_CLIENT_RESPONDED, event_handler)
        event_dispatcher.register(EventType.NC_VERIFIED_ACCEPTED, event_handler)
        event_dispatcher.register(EventType.NC_VERIFIED_REJECTED, event_handler)
        event_dispatcher.register(EventType.NC_CLOSED, event_handler)

        # Create users
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")
        self.lead_auditor.groups.add(lead_group)

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

        self.site = Site.objects.create(
            organization=self.org, site_name="Site 1", site_address="123 St"
        )

    def tearDown(self):
        """Clean up event handlers."""
        event_dispatcher.clear()

    def test_audit_created_event(self):
        """Test AUDIT_CREATED event is emitted."""
        self.events_received.clear()

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["audit"], audit)
        self.assertEqual(event_payload["created_by"], self.cb_admin)

    def test_audit_updated_event(self):
        """Test AUDIT_UPDATED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.events_received.clear()

        AuditService.update_audit(audit=audit, data={"planned_duration_hours": 16.0})

        # Should emit AUDIT_UPDATED
        self.assertGreaterEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["audit"], audit)

    def test_audit_status_changed_event(self):
        """Test AUDIT_STATUS_CHANGED event is emitted when status changes."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.events_received.clear()

        AuditService.update_audit(audit=audit, data={"status": "scheduled"})

        # Should emit both AUDIT_UPDATED and AUDIT_STATUS_CHANGED
        self.assertEqual(len(self.events_received), 2)

        # Check for status change event
        status_change_events = [
            e for e in self.events_received if "old_status" in e and e["old_status"] == "draft"
        ]
        self.assertEqual(
            len(status_change_events), 2
        )  # One in AUDIT_UPDATED, one in STATUS_CHANGED

    def test_finding_created_event(self):
        """Test FINDING_CREATED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.events_received.clear()

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["finding"], nc)
        self.assertEqual(event_payload["finding_type"], "nonconformity")
        self.assertEqual(event_payload["audit"], audit)

    def test_nc_client_responded_event(self):
        """Test NC_CLIENT_RESPONDED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        self.events_received.clear()

        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Corrective action",
            },
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["nonconformity"], nc)
        self.assertEqual(event_payload["audit"], audit)

    def test_nc_verified_accepted_event(self):
        """Test NC_VERIFIED_ACCEPTED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Corrective action",
            },
        )

        self.events_received.clear()

        FindingService.verify_nonconformity(
            nc=nc, user=self.lead_auditor, action="accept", notes="Accepted"
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["nonconformity"], nc)
        self.assertEqual(event_payload["verified_by"], self.lead_auditor)

    def test_nc_verified_rejected_event(self):
        """Test NC_VERIFIED_REJECTED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Corrective action",
            },
        )

        self.events_received.clear()

        FindingService.verify_nonconformity(
            nc=nc, user=self.lead_auditor, action="request_changes", notes="Need more details"
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["nonconformity"], nc)
        self.assertEqual(event_payload["verified_by"], self.lead_auditor)

    def test_nc_closed_event(self):
        """Test NC_CLOSED event is emitted."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        nc = FindingService.create_nonconformity(
            audit=audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Test NC",
                "auditor_explanation": "Test explanation",
            },
        )

        FindingService.respond_to_nonconformity(
            nc=nc,
            response_data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Corrective action",
            },
        )

        FindingService.verify_nonconformity(
            nc=nc, user=self.lead_auditor, action="accept", notes="Accepted"
        )

        self.events_received.clear()

        FindingService.verify_nonconformity(
            nc=nc, user=self.lead_auditor, action="close", notes="Verified effective"
        )

        self.assertEqual(len(self.events_received), 1)
        event_payload = self.events_received[0]
        self.assertEqual(event_payload["nonconformity"], nc)
        self.assertEqual(event_payload["closed_by"], self.lead_auditor)

"""
Service layer unit tests.

Direct unit tests for AuditService and FindingService methods.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase

from core.models import Certification, Organization, Site, Standard
from trunk.events import EventType, event_dispatcher
from trunk.services.audit_service import AuditService
from trunk.services.finding_service import FindingService


class AuditServiceTest(TestCase):
    """Test AuditService methods."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

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

    def test_create_audit_basic(self):
        """Test basic audit creation."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.assertIsNotNone(audit)
        self.assertEqual(audit.organization, self.org)
        self.assertEqual(audit.audit_type, "stage2")
        self.assertEqual(audit.status, "draft")
        self.assertEqual(audit.created_by, self.cb_admin)

    def test_create_audit_with_multiple_certifications(self):
        """Test audit creation with multiple certifications."""
        cert2 = Certification.objects.create(
            organization=self.org,
            standard=Standard.objects.create(code="ISO 14001", title="EMS"),
            certification_scope="Test 2",
            certificate_status="active",
        )

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert, cert2],
            sites=[self.site],
            audit_data={
                "audit_type": "integrated",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 16.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.assertEqual(audit.certifications.count(), 2)
        self.assertIn(self.cert, audit.certifications.all())
        self.assertIn(cert2, audit.certifications.all())

    def test_create_audit_with_multiple_sites(self):
        """Test audit creation with multiple sites."""
        site2 = Site.objects.create(organization=self.org, site_name="Site 2", site_address="456 St")

        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site, site2],
            audit_data={
                "audit_type": "surveillance",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today() + timedelta(days=1),
                "planned_duration_hours": 16.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        self.assertEqual(audit.sites.count(), 2)
        self.assertIn(self.site, audit.sites.all())
        self.assertIn(site2, audit.sites.all())

    def test_update_audit_basic_fields(self):
        """Test updating audit basic fields."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        AuditService.update_audit(audit=audit, data={"planned_duration_hours": 16.0})

        audit.refresh_from_db()
        self.assertEqual(audit.planned_duration_hours, 16.0)

    def test_update_audit_status(self):
        """Test updating audit status."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        AuditService.update_audit(audit=audit, data={"status": "scheduled"})

        audit.refresh_from_db()
        self.assertEqual(audit.status, "scheduled")

    def test_create_audit_emits_event(self):
        """Test that audit creation emits AUDIT_CREATED event."""
        events_received = []

        def handler(payload):
            events_received.append(payload)

        event_dispatcher.register(EventType.AUDIT_CREATED, handler)

        try:
            audit = AuditService.create_audit(
                organization=self.org,
                certifications=[self.cert],
                sites=[self.site],
                audit_data={
                    "audit_type": "stage2",
                    "total_audit_date_from": date.today(),
                    "total_audit_date_to": date.today(),
                    "planned_duration_hours": 8.0,
                    "status": "draft",
                },
                created_by=self.cb_admin,
            )

            self.assertEqual(len(events_received), 1)
            self.assertEqual(events_received[0]["audit"], audit)
        finally:
            event_dispatcher.clear()

    def test_update_audit_emits_event(self):
        """Test that audit update emits AUDIT_UPDATED event."""
        audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

        events_received = []

        def handler(payload):
            events_received.append(payload)

        event_dispatcher.register(EventType.AUDIT_UPDATED, handler)

        try:
            AuditService.update_audit(audit=audit, data={"planned_duration_hours": 16.0})

            self.assertGreaterEqual(len(events_received), 1)
            self.assertEqual(events_received[0]["audit"], audit)
        finally:
            event_dispatcher.clear()


class FindingServiceTest(TestCase):
    """Test FindingService methods."""

    def setUp(self):
        """Set up test data."""
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin.groups.add(cb_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")
        self.lead_auditor.groups.add(lead_group)

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

        self.audit = AuditService.create_audit(
            organization=self.org,
            certifications=[self.cert],
            sites=[self.site],
            audit_data={
                "audit_type": "stage2",
                "total_audit_date_from": date.today(),
                "total_audit_date_to": date.today(),
                "planned_duration_hours": 8.0,
                "status": "draft",
            },
            created_by=self.cb_admin,
        )

    def test_create_major_nonconformity(self):
        """Test creating a major NC."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "major",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Major NC",
                "auditor_explanation": "Test explanation",
            },
        )

        self.assertIsNotNone(nc)
        self.assertEqual(nc.category, "major")
        self.assertEqual(nc.audit, self.audit)
        self.assertEqual(nc.verification_status, "open")

    def test_create_minor_nonconformity(self):
        """Test creating a minor NC."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "category": "minor",
                "objective_evidence": "Test evidence",
                "statement_of_nc": "Minor NC",
                "auditor_explanation": "Test explanation",
            },
        )

        self.assertEqual(nc.category, "minor")

    def test_create_observation(self):
        """Test creating an observation."""
        obs = FindingService.create_observation(
            audit=self.audit,
            user=self.lead_auditor,
            data={
                "standard": self.standard,
                "clause": "7.5.1",
                "statement": "Test observation",
                "explanation": "Additional details",
            },
        )

        self.assertIsNotNone(obs)
        self.assertEqual(obs.audit, self.audit)

    def test_create_ofi(self):
        """Test creating an OFI."""
        ofi = FindingService.create_ofi(
            audit=self.audit,
            user=self.lead_auditor,
            data={"standard": self.standard, "clause": "7.5.1", "description": "Test OFI"},
        )

        self.assertIsNotNone(ofi)
        self.assertEqual(ofi.audit, self.audit)

    def test_respond_to_nonconformity(self):
        """Test client response to NC."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
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

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "client_responded")
        self.assertEqual(nc.client_root_cause, "Root cause")
        self.assertEqual(nc.client_correction, "Correction")
        self.assertEqual(nc.client_corrective_action, "Corrective action")

    def test_verify_nonconformity_accept(self):
        """Test auditor accepts NC response."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
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

        FindingService.verify_nonconformity(nc=nc, user=self.lead_auditor, action="accept", notes="Looks good")

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "accepted")
        self.assertEqual(nc.verification_notes, "Looks good")

    def test_verify_nonconformity_reject(self):
        """Test auditor requests changes to NC response."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
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
            nc=nc, user=self.lead_auditor, action="request_changes", notes="Need more detail"
        )

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "open")
        self.assertEqual(nc.verification_notes, "Need more detail")

    def test_verify_nonconformity_close(self):
        """Test auditor closes NC after verification."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
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

        FindingService.verify_nonconformity(nc=nc, user=self.lead_auditor, action="accept", notes="Accepted")

        FindingService.verify_nonconformity(nc=nc, user=self.lead_auditor, action="close", notes="Verified effective")

        nc.refresh_from_db()
        self.assertEqual(nc.verification_status, "closed")

    def test_create_nonconformity_emits_event(self):
        """Test that NC creation emits FINDING_CREATED event."""
        events_received = []

        def handler(payload):
            events_received.append(payload)

        event_dispatcher.register(EventType.FINDING_CREATED, handler)

        try:
            nc = FindingService.create_nonconformity(
                audit=self.audit,
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

            self.assertEqual(len(events_received), 1)
            self.assertEqual(events_received[0]["finding"], nc)
            self.assertEqual(events_received[0]["finding_type"], "nonconformity")
        finally:
            event_dispatcher.clear()

    def test_respond_to_nc_emits_event(self):
        """Test that NC response emits NC_CLIENT_RESPONDED event."""
        nc = FindingService.create_nonconformity(
            audit=self.audit,
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

        events_received = []

        def handler(payload):
            events_received.append(payload)

        event_dispatcher.register(EventType.NC_CLIENT_RESPONDED, handler)

        try:
            FindingService.respond_to_nonconformity(
                nc=nc,
                response_data={
                    "client_root_cause": "Root cause",
                    "client_correction": "Correction",
                    "client_corrective_action": "Corrective action",
                },
            )

            self.assertEqual(len(events_received), 1)
            self.assertEqual(events_received[0]["nonconformity"], nc)
        finally:
            event_dispatcher.clear()

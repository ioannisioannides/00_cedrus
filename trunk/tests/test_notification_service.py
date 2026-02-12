"""
Tests for the NotificationService.

Covers all 7 notification methods with both happy-path and edge-case scenarios.
Uses Django's console email backend to capture outgoing messages.
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.core import mail
from django.test import TestCase, override_settings

from audit_management.models import Audit, AuditProgram, Nonconformity
from certification.models import CertificationDecision, Complaint
from core.models import Certification, Organization, Standard
from trunk.services.notification_service import NotificationService, _send_notification


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@cedrus.local",
    SITE_URL="http://localhost:8000",
)
class TestNotificationService(TestCase):
    """Test NotificationService methods."""

    def setUp(self):
        # Groups
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.client_admin_group = Group.objects.create(name="client_admin")
        self.client_user_group = Group.objects.create(name="client_user")
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")

        # Users
        self.admin_user = User.objects.create_user(
            username="admin",
            password="pass",
            email="admin@cb.com",
            first_name="Admin",
            last_name="User",
        )
        self.admin_user.groups.add(self.cb_admin_group)

        self.lead_auditor = User.objects.create_user(
            username="lead",
            password="pass",
            email="lead@cb.com",
            first_name="Lead",
            last_name="Auditor",
        )
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.client_user = User.objects.create_user(
            username="client1",
            password="pass",
            email="client@acme.com",
            first_name="Client",
            last_name="Contact",
        )
        self.client_user.groups.add(self.client_admin_group)

        # Core data
        self.org = Organization.objects.create(
            name="Acme Corp",
            customer_id="ACME01",
            total_employee_count=50,
            registered_address="addr",
        )
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.certification = Certification.objects.create(
            organization=self.org,
            standard=self.standard,
            certificate_id="CERT-001",
            issue_date=date(2025, 1, 1),
            expiry_date=date(2025, 12, 31),
            certificate_status="active",
        )

        # Link client profile to organization (profile auto-created by signal)
        self.client_user.profile.organization = self.org
        self.client_user.profile.save()

        # Audit data
        self.program = AuditProgram.objects.create(
            organization=self.org,
            title="2025",
            year=2025,
            objectives="obj",
            risks_opportunities="risk",
            created_by=self.admin_user,
        )
        self.audit = Audit.objects.create(
            program=self.program,
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date(2025, 3, 1),
            total_audit_date_to=date(2025, 3, 5),
            created_by=self.admin_user,
            lead_auditor=self.lead_auditor,
        )

    # ------------------------------------------------------------------
    # notify_audit_assigned
    # ------------------------------------------------------------------

    def test_notify_audit_assigned_sends_email(self):
        NotificationService.notify_audit_assigned({"audit_id": self.audit.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Audit assigned", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["lead@cb.com"])

    def test_notify_audit_assigned_empty_payload(self):
        NotificationService.notify_audit_assigned({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_assigned_missing_audit(self):
        NotificationService.notify_audit_assigned({"audit_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_assigned_no_lead_auditor(self):
        self.audit.lead_auditor = None
        self.audit.save()
        NotificationService.notify_audit_assigned({"audit_id": self.audit.pk})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_assigned_lead_auditor_no_email(self):
        self.lead_auditor.email = ""
        self.lead_auditor.save()
        NotificationService.notify_audit_assigned({"audit_id": self.audit.pk})
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_audit_status_changed
    # ------------------------------------------------------------------

    def test_notify_audit_status_changed_sends_email(self):
        NotificationService.notify_audit_status_changed(
            {
                "audit_id": self.audit.pk,
                "new_status": "scheduled",
            }
        )
        # Should send to lead auditor + created_by (2 unique emails)
        self.assertEqual(len(mail.outbox), 2)

    def test_notify_audit_status_changed_deduplicates(self):
        # When lead_auditor == created_by, only one email
        self.audit.lead_auditor = self.admin_user
        self.audit.save()
        NotificationService.notify_audit_status_changed(
            {
                "audit_id": self.audit.pk,
                "new_status": "scheduled",
            }
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_notify_audit_status_changed_empty_payload(self):
        NotificationService.notify_audit_status_changed({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_status_changed_missing_new_status(self):
        NotificationService.notify_audit_status_changed({"audit_id": self.audit.pk})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_status_changed_missing_audit(self):
        NotificationService.notify_audit_status_changed({"audit_id": 999999, "new_status": "draft"})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_audit_status_changed_no_recipients(self):
        self.lead_auditor.email = ""
        self.lead_auditor.save()
        self.admin_user.email = ""
        self.admin_user.save()
        NotificationService.notify_audit_status_changed(
            {
                "audit_id": self.audit.pk,
                "new_status": "scheduled",
            }
        )
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_nc_raised
    # ------------------------------------------------------------------

    def test_notify_nc_raised_sends_email(self):
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
        )
        NotificationService.notify_nc_raised({"nc_id": nc.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Nonconformity raised", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["client@acme.com"])

    def test_notify_nc_raised_uses_finding_id_fallback(self):
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="minor",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
        )
        NotificationService.notify_nc_raised({"finding_id": nc.pk})
        self.assertEqual(len(mail.outbox), 1)

    def test_notify_nc_raised_empty_payload(self):
        NotificationService.notify_nc_raised({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_nc_raised_missing_nc(self):
        NotificationService.notify_nc_raised({"nc_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_nc_raised_no_client_contacts(self):
        # Remove client group membership so no client contacts are found
        self.client_user.groups.clear()
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
        )
        NotificationService.notify_nc_raised({"nc_id": nc.pk})
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_nc_response_required
    # ------------------------------------------------------------------

    def test_notify_nc_response_required_sends_email(self):
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
        )
        NotificationService.notify_nc_response_required({"nc_id": nc.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Response required", mail.outbox[0].subject)

    def test_notify_nc_response_required_empty_payload(self):
        NotificationService.notify_nc_response_required({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_nc_response_required_missing_nc(self):
        NotificationService.notify_nc_response_required({"nc_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_nc_response_required_no_client_contacts(self):
        self.client_user.groups.clear()
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="5.1",
            category="minor",
            objective_evidence="ev",
            statement_of_nc="st",
            auditor_explanation="exp",
            created_by=self.admin_user,
        )
        NotificationService.notify_nc_response_required({"nc_id": nc.pk})
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_certification_expiring
    # ------------------------------------------------------------------

    def test_notify_certification_expiring_sends_email(self):
        NotificationService.notify_certification_expiring({"certification_id": self.certification.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Certification expiring", mail.outbox[0].subject)

    def test_notify_certification_expiring_empty_payload(self):
        NotificationService.notify_certification_expiring({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_certification_expiring_missing_cert(self):
        NotificationService.notify_certification_expiring({"certification_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_certification_expiring_no_client_contacts(self):
        self.client_user.groups.clear()
        NotificationService.notify_certification_expiring({"certification_id": self.certification.pk})
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_complaint_received
    # ------------------------------------------------------------------

    def test_notify_complaint_received_sends_email(self):
        complaint = Complaint.objects.create(
            complaint_number="COMP-001",
            organization=self.org,
            complainant_name="John",
            complaint_type="audit_conduct",
            description="desc",
            submitted_by=self.admin_user,
        )
        NotificationService.notify_complaint_received({"complaint_id": complaint.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New complaint received", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["admin@cb.com"])

    def test_notify_complaint_received_empty_payload(self):
        NotificationService.notify_complaint_received({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_complaint_received_missing_complaint(self):
        NotificationService.notify_complaint_received({"complaint_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_complaint_received_no_cb_admins(self):
        self.admin_user.groups.clear()
        complaint = Complaint.objects.create(
            complaint_number="COMP-002",
            organization=self.org,
            complainant_name="Jane",
            complaint_type="other",
            description="desc",
            submitted_by=self.admin_user,
        )
        NotificationService.notify_complaint_received({"complaint_id": complaint.pk})
        self.assertEqual(len(mail.outbox), 0)

    # ------------------------------------------------------------------
    # notify_decision_made
    # ------------------------------------------------------------------

    def test_notify_decision_made_sends_email(self):
        CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.admin_user,
            decision="grant",
            decision_notes="Approved",
        )
        NotificationService.notify_decision_made({"audit_id": self.audit.pk})
        # Should send to lead_auditor + client_admin
        self.assertEqual(len(mail.outbox), 2)
        recipients = {m.to[0] for m in mail.outbox}
        self.assertIn("lead@cb.com", recipients)
        self.assertIn("client@acme.com", recipients)

    def test_notify_decision_made_empty_payload(self):
        NotificationService.notify_decision_made({})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_decision_made_missing_decision(self):
        NotificationService.notify_decision_made({"audit_id": 999999})
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_decision_made_no_recipients(self):
        self.lead_auditor.email = ""
        self.lead_auditor.save()
        self.client_user.groups.clear()
        CertificationDecision.objects.create(
            audit=self.audit,
            decision_maker=self.admin_user,
            decision="grant",
            decision_notes="Approved",
        )
        NotificationService.notify_decision_made({"audit_id": self.audit.pk})
        self.assertEqual(len(mail.outbox), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@cedrus.local",
)
class TestSendNotificationHelper(TestCase):
    """Test the _send_notification helper function."""

    def test_successful_email_send(self):
        _send_notification(
            recipient_email="user@example.com",
            subject="Test Subject",
            template="notifications/base_email.html",
            context={},
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
        self.assertEqual(mail.outbox[0].to, ["user@example.com"])
        self.assertEqual(mail.outbox[0].from_email, "test@cedrus.local")

    def test_email_failure_does_not_raise(self):
        """Send failure should be logged, not raised."""
        # Use a template that doesn't exist to trigger a failure
        _send_notification(
            recipient_email="user@example.com",
            subject="Test",
            template="notifications/nonexistent.html",
            context={},
        )
        # Should not raise, just log the error
        self.assertEqual(len(mail.outbox), 0)

    def test_html_message_is_set(self):
        _send_notification(
            recipient_email="user@example.com",
            subject="HTML Test",
            template="notifications/base_email.html",
            context={},
        )
        # Django's mail.outbox stores alternatives for HTML
        msg = mail.outbox[0]
        self.assertTrue(len(msg.alternatives) > 0)
        html_content = msg.alternatives[0][0]
        self.assertIn("Cedrus", html_content)

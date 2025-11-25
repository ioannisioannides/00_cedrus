from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from audits.models import Appeal, Audit, Complaint
from core.models import Organization


class ComplaintViewTest(TestCase):
    """Test complaint views."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="user", password="password")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="closed",
            created_by=self.user,
            lead_auditor=self.user,
        )

    def test_complaint_list(self):
        """Test complaint list view."""
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("audits:complaint_list"))
        self.assertEqual(response.status_code, 200)

    def test_complaint_create(self):
        """Test creating a complaint."""
        self.client.login(username="user", password="password")
        data = {
            "complainant_name": "John Doe",
            "complainant_email": "john@example.com",
            "organization": self.org.pk,
            "complaint_type": "other",
            "description": "Bad service",
            "related_audit": self.audit.pk,
        }
        response = self.client.post(reverse("audits:complaint_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Complaint.objects.filter(description="Bad service").exists())

    def test_complaint_detail(self):
        """Test complaint detail view."""
        complaint = Complaint.objects.create(
            complainant_name="John Doe",
            complainant_email="john@example.com",
            organization=self.org,
            complaint_type="other",
            description="Bad service",
            related_audit=self.audit,
            submitted_by=self.user,
        )
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("audits:complaint_detail", kwargs={"pk": complaint.pk}))
        self.assertEqual(response.status_code, 200)


class AppealViewTest(TestCase):
    """Test appeal views."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="user", password="password")
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="closed",
            created_by=self.user,
            lead_auditor=self.user,
        )
        # Create a certification decision (mocked or real if needed)
        # For now, we just need a related_decision string or object?
        # Appeal model: related_decision = models.OneToOneField('CertificationDecision', ...)
        # Let's check Appeal model.

    def test_appeal_list(self):
        """Test appeal list view."""
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("audits:appeal_list"))
        self.assertEqual(response.status_code, 200)

    def test_appeal_create(self):
        """Test creating an appeal."""
        # Need a CertificationDecision first
        from audits.models import CertificationDecision

        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision="grant",
            decision_maker=self.user,
        )

        self.client.login(username="user", password="password")
        data = {
            "appellant_name": "Jane Doe",
            "appellant_email": "jane@example.com",
            "related_decision": decision.pk,
            "grounds": "Unfair decision",
        }
        response = self.client.post(reverse("audits:appeal_create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appeal.objects.filter(grounds="Unfair decision").exists())

    def test_appeal_detail(self):
        """Test appeal detail view."""
        from audits.models import CertificationDecision

        decision = CertificationDecision.objects.create(
            audit=self.audit,
            decision="grant",
            decision_maker=self.user,
        )
        appeal = Appeal.objects.create(
            appellant_name="Jane Doe",
            appellant_email="jane@example.com",
            related_decision=decision,
            grounds="Unfair decision",
            submitted_by=self.user,
        )
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("audits:appeal_detail", kwargs={"pk": appeal.pk}))
        self.assertEqual(response.status_code, 200)

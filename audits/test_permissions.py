"""
Permission testing for role-based access control.

Tests that each user role has appropriate access to features:
- CB Admin: Full access
- Lead Auditor: Assigned audits, findings
- Auditor: View assigned audits
- Client Admin/User: Own organization's audits, respond to NCs
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import Audit
from core.models import Certification, Organization, Site, Standard
from trunk.permissions.predicates import PermissionPredicate


class PermissionPredicateTest(TestCase):
    """Test PermissionPredicate static methods."""

    def setUp(self):
        """Set up test users with different roles."""
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.auditor_group = Group.objects.create(name="auditor")
        self.client_admin_group = Group.objects.create(name="client_admin")
        self.client_user_group = Group.objects.create(name="client_user")

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")  # nosec B106
        self.cb_admin.groups.add(self.cb_admin_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass")  # nosec B106
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.auditor = User.objects.create_user(username="auditor", password="pass")  # nosec B106
        self.auditor.groups.add(self.auditor_group)

        self.client_admin = User.objects.create_user(username="clientadmin", password="pass")  # nosec B106
        self.client_admin.groups.add(self.client_admin_group)

        self.client_user = User.objects.create_user(username="clientuser", password="pass")  # nosec B106
        self.client_user.groups.add(self.client_user_group)

        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )

        self.client_admin.profile.organization = self.org
        self.client_admin.profile.save()

    def test_is_cb_admin(self):
        """Test CB Admin role detection."""
        self.assertTrue(PermissionPredicate.is_cb_admin(self.cb_admin))
        self.assertFalse(PermissionPredicate.is_cb_admin(self.lead_auditor))
        self.assertFalse(PermissionPredicate.is_cb_admin(self.client_admin))

    def test_is_lead_auditor(self):
        """Test Lead Auditor role detection."""
        self.assertTrue(PermissionPredicate.is_lead_auditor(self.lead_auditor))
        self.assertFalse(PermissionPredicate.is_lead_auditor(self.auditor))
        self.assertFalse(PermissionPredicate.is_lead_auditor(self.cb_admin))

    def test_is_auditor(self):
        """Test Auditor role detection (includes lead auditor)."""
        self.assertTrue(PermissionPredicate.is_auditor(self.lead_auditor))
        self.assertTrue(PermissionPredicate.is_auditor(self.auditor))
        self.assertFalse(PermissionPredicate.is_auditor(self.client_admin))

    def test_is_client_user(self):
        """Test Client User role detection."""
        self.assertTrue(PermissionPredicate.is_client_user(self.client_admin))
        self.assertTrue(PermissionPredicate.is_client_user(self.client_user))
        self.assertFalse(PermissionPredicate.is_client_user(self.lead_auditor))

    def test_can_view_audit(self):
        """Test audit viewing permissions."""
        std = Standard.objects.create(code="ISO 9001", title="QMS")
        cert = Certification.objects.create(
            organization=self.org,
            standard=std,
            certification_scope="Test",
            certificate_status="active",
        )
        site = Site.objects.create(organization=self.org, site_name="Site 1", site_address="123 St")

        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        audit.certifications.add(cert)
        audit.sites.add(site)

        # CB Admin can view any audit
        self.assertTrue(PermissionPredicate.can_view_audit(self.cb_admin, audit))

        # Lead Auditor can view their own audit
        self.assertTrue(PermissionPredicate.can_view_audit(self.lead_auditor, audit))

        # Client can view their org's audit
        self.assertTrue(PermissionPredicate.can_view_audit(self.client_admin, audit))

        # Other auditor cannot view
        other_auditor = User.objects.create_user(username="other", password="pass")  # nosec B106
        other_auditor.groups.add(self.auditor_group)
        self.assertFalse(PermissionPredicate.can_view_audit(other_auditor, audit))


class RoleBasedAccessTest(TestCase):
    """Test role-based access control through views."""

    def setUp(self):
        """Set up test data."""
        # Create groups
        cb_admin_group = Group.objects.create(name="cb_admin")
        lead_auditor_group = Group.objects.create(name="lead_auditor")
        auditor_group = Group.objects.create(name="auditor")
        client_admin_group = Group.objects.create(name="client_admin")

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")  # nosec B106
        self.cb_admin.groups.add(cb_admin_group)

        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")  # nosec B106
        self.lead_auditor.groups.add(lead_auditor_group)

        self.auditor = User.objects.create_user(username="auditor", password="pass123")  # nosec B106
        self.auditor.groups.add(auditor_group)

        self.client_admin = User.objects.create_user(username="clientadmin", password="pass123")  # nosec B106
        self.client_admin.groups.add(client_admin_group)

        self.other_client = User.objects.create_user(username="otherclient", password="pass123")  # nosec B106
        self.other_client.groups.add(client_admin_group)

        # Create organizations
        self.org1 = Organization.objects.create(
            name="Org 1", registered_address="123 St", customer_id="ORG001", total_employee_count=10
        )

        org2 = Organization.objects.create(
            name="Org 2", registered_address="456 St", customer_id="ORG002", total_employee_count=20
        )

        # Create standard and certifications
        self.standard = Standard.objects.create(code="ISO 9001", title="QMS")

        cert1 = Certification.objects.create(
            organization=self.org1,
            standard=self.standard,
            certification_scope="Manufacturing",
            certificate_status="active",
        )

        Certification.objects.create(
            organization=org2,
            standard=self.standard,
            certification_scope="Services",
            certificate_status="active",
        )

        # Create sites
        site1 = Site.objects.create(organization=self.org1, site_name="Site 1", site_address="123 St")

        Site.objects.create(organization=org2, site_name="Site 2", site_address="456 St")

        # Link clients to organizations
        self.client_admin.profile.organization = self.org1
        self.client_admin.profile.save()

        self.other_client.profile.organization = org2
        self.other_client.profile.save()

        # Create audit for org1
        self.audit1 = Audit.objects.create(
            organization=self.org1,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=2),
            planned_duration_hours=16.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.audit1.certifications.add(cert1)
        self.audit1.sites.add(site1)

        self.client = Client()

    def test_cb_admin_can_create_audit(self):
        """CB Admin can create audits."""
        self.client.login(username="cbadmin", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 200)

    def test_lead_auditor_cannot_create_audit(self):
        """Lead Auditor cannot create audits."""
        self.client.login(username="lead", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 403)

    def test_client_cannot_create_audit(self):
        """Client cannot create audits."""
        self.client.login(username="clientadmin", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 403)

    def test_lead_auditor_can_view_own_audit(self):
        """Lead Auditor can view their assigned audits."""
        self.client.login(username="lead", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_client_can_view_own_org_audit(self):
        """Client can view their organization's audits."""
        self.client.login(username="clientadmin", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_view_other_org_audit(self):
        """Client cannot view other organization's audits."""
        self.client.login(username="otherclient", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 404)

    def test_auditor_cannot_view_unassigned_audit(self):
        """Auditor cannot view audits they're not assigned to."""
        self.client.login(username="auditor", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 404)

    def test_lead_auditor_can_edit_draft_audit(self):
        """Lead Auditor can edit their draft audits."""
        self.client.login(username="lead", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_update", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_lead_auditor_cannot_edit_decided_audit(self):
        """Lead Auditor cannot edit decided audits."""
        self.audit1.status = "decided"
        self.audit1.save()

        self.client.login(username="lead", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_update", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 403)

    def test_client_cannot_edit_audit(self):
        """Client cannot edit audits."""
        self.client.login(username="clientadmin", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_update", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 403)

    def test_cb_admin_can_make_decision(self):
        """CB Admin can make certification decisions."""
        # Audit must be in "submitted" status to make decision (after technical review)
        self.audit1.status = "submitted"
        self.audit1.save()

        self.client.login(username="cbadmin", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_make_decision", args=[self.audit1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_lead_auditor_cannot_make_decision(self):
        """Lead Auditor cannot make certification decisions."""
        self.audit1.status = "client_review"
        self.audit1.save()

        self.client.login(username="lead", password="pass123")  # nosec B106
        response = self.client.get(reverse("audits:audit_make_decision", args=[self.audit1.pk]))
        self.assertRedirects(response, reverse("audits:audit_detail", args=[self.audit1.pk]))

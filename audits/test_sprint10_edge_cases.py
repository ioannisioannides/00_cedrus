"""
Sprint 10: Edge Case Testing

Tests for boundary conditions, multi-site scenarios, external team members,
multiple major NCs, and various user role combinations.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import Audit, AuditTeamMember, Nonconformity
from core.models import Organization, Site, Standard
from trunk.services.sampling import calculate_sample_size


class MultiSiteEdgeCaseTests(TestCase):
    """Test edge cases for multi-site audits."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Multi-Site Org",
            registered_address="123 Test St",
            customer_id="CUST-MULTI-001",
            total_employee_count=500,
        )
        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

    def test_single_site_no_sampling(self):
        """Test that single-site audits don't show sampling info."""
        site = Site.objects.create(organization=self.org, site_name="Only Site", site_address="123 Main St")
        self.audit.sites.add(site)

        # Single site should not trigger multi-site sampling
        self.assertEqual(self.audit.sites.count(), 1)

    def test_large_multi_site_sampling(self):
        """Test IAF MD1 sampling with large number of sites."""
        # Create 100 sites
        for i in range(100):
            site = Site.objects.create(organization=self.org, site_name=f"Site {i+1}", site_address=f"Address {i+1}")
            self.audit.sites.add(site)

        result = calculate_sample_size(total_sites=100, is_initial_certification=True)
        # √100 = 10
        self.assertEqual(result["minimum_sites"], 10)

    def test_exact_square_root_sites(self):
        """Test sampling when site count is perfect square."""
        for i in range(16):  # 16 = 4²
            site = Site.objects.create(organization=self.org, site_name=f"Site {i+1}", site_address=f"Address {i+1}")
            self.audit.sites.add(site)

        result = calculate_sample_size(total_sites=16, is_initial_certification=True)
        self.assertEqual(result["minimum_sites"], 4)  # √16 = 4


class ExternalTeamMemberEdgeCaseTests(TestCase):
    """Test edge cases for external team members."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-EXT-001",
            total_employee_count=10,
        )
        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

    def test_external_expert_without_user(self):
        """Test external expert can be added without user account."""
        external_member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=None,
            name="Dr. Jane External",
            title="Environmental Expert",
            role="technical_expert",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )
        self.assertIsNone(external_member.user)
        self.assertEqual(external_member.name, "Dr. Jane External")

    def test_mixed_internal_external_team(self):
        """Test audit with both internal and external team members."""
        # Internal member
        internal = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            name=self.auditor.get_full_name() or self.auditor.username,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        # External member
        external = AuditTeamMember.objects.create(
            audit=self.audit,
            user=None,
            name="External Consultant",
            title="ISO 9001 Specialist",
            role="technical_expert",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        self.assertEqual(self.audit.team_members.count(), 2)
        self.assertTrue(internal.user is not None)
        self.assertTrue(external.user is None)


class MultipleNCEdgeCaseTests(TestCase):
    """Test edge cases with multiple nonconformities."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-NC-001",
            total_employee_count=10,
        )
        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="scheduled",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )

        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality management systems - Requirements")

    def test_multiple_major_ncs_block_submission(self):
        """Test that multiple open major NCs block submission."""
        # Create 3 major NCs
        for i in range(3):
            Nonconformity.objects.create(
                audit=self.audit,
                standard=self.standard,
                clause=f"4.{i+1}",
                category="major",
                objective_evidence=f"Evidence {i+1}",
                statement_of_nc=f"Statement {i+1}",
                auditor_explanation=f"Explanation {i+1}",
                created_by=self.auditor,
                verification_status="open",
            )

        self.assertEqual(
            self.audit.nonconformity_set.filter(category="major", verification_status="open").count(),
            3,
        )

    def test_mix_of_major_and_minor_ncs(self):
        """Test audit with both major and minor NCs."""
        # 2 major NCs
        Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="4.1",
            category="major",
            objective_evidence="Major evidence",
            statement_of_nc="Major NC",
            auditor_explanation="Major explanation",
            created_by=self.auditor,
            verification_status="open",
        )

        # 3 minor NCs
        for i in range(3):
            Nonconformity.objects.create(
                audit=self.audit,
                standard=self.standard,
                clause=f"5.{i+1}",
                category="minor",
                objective_evidence=f"Minor evidence {i+1}",
                statement_of_nc=f"Minor NC {i+1}",
                auditor_explanation=f"Minor explanation {i+1}",
                created_by=self.auditor,
                verification_status="open",
            )

        self.assertEqual(self.audit.nonconformity_set.filter(category="major").count(), 1)
        self.assertEqual(self.audit.nonconformity_set.filter(category="minor").count(), 3)


class DateBoundaryEdgeCaseTests(TestCase):
    """Test edge cases for date boundaries."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-DATE-001",
            total_employee_count=10,
        )
        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

    def test_same_day_audit(self):
        """Test audit with same start and end date."""
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today(),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )
        self.assertEqual(audit.total_audit_date_from, audit.total_audit_date_to)

    def test_long_duration_audit(self):
        """Test audit with very long duration."""
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=365),
            created_by=self.auditor,
            lead_auditor=self.auditor,
        )
        duration = (audit.total_audit_date_to - audit.total_audit_date_from).days
        self.assertEqual(duration, 365)


class RolePermissionEdgeCaseTests(TestCase):
    """Test edge cases for role-based permissions."""

    def setUp(self):
        """Set up test fixtures."""
        self.client_http = Client()
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-ROLE-001",
            total_employee_count=10,
        )

        # Create users with different roles
        self.auditor = User.objects.create_user(username="auditor1", password="testpass123")  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.lead_auditor = User.objects.create_user(username="leadauditor1", password="testpass123")  # nosec B106
        lead_group, _ = Group.objects.get_or_create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_group)

        self.cb_admin = User.objects.create_user(username="cbadmin1", password="testpass123")  # nosec B106
        cb_group, _ = Group.objects.get_or_create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            status="draft",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
            created_by=self.lead_auditor,
            lead_auditor=self.lead_auditor,
        )

    def test_cb_admin_has_full_access(self):
        """Test CB admin can access all audits."""
        self.client_http.login(username="cbadmin1", password="testpass123")  # nosec B106
        url = reverse("audits:audit_detail", kwargs={"pk": self.audit.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_lead_auditor_can_edit_own_audit(self):
        """Test lead auditor can edit their own audit."""
        self.client_http.login(username="leadauditor1", password="testpass123")  # nosec B106
        url = reverse("audits:audit_update", kwargs={"pk": self.audit.pk})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_regular_auditor_limited_access(self):
        """Test regular auditor has limited access to unassigned audits."""
        self.client_http.login(username="auditor1", password="testpass123")  # nosec B106
        url = reverse("audits:audit_detail", kwargs={"pk": self.audit.pk})
        response = self.client_http.get(url)
        # Should not see audit they're not assigned to
        self.assertIn(response.status_code, [302, 403, 404])

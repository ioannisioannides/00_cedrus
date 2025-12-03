"""
Test Suite for Sprint 8: Audit Team & Multi-Site Management

Tests cover:
- US-010: Assign Team Members to Audit
- Team member CRUD operations
- Form validation (dates, user/external experts)
- Permission checks (cb_admin, lead_auditor)
- Competence warnings integration
- IAF MD1 multi-site sampling display
- Documentation forms (US-018, US-019, US-020)
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import Audit, AuditChanges, AuditorCompetenceWarning, AuditTeamMember
from audits.team_forms import AuditTeamMemberForm
from core.models import Organization
from core.test_utils import TEST_PASSWORD
from trunk.services.sampling import calculate_sample_size

User = get_user_model()


class AuditTeamMemberFormTests(TestCase):
    """Test AuditTeamMemberForm validation and behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-FORM-001",
            total_employee_count=10,
        )
        self.user = User.objects.create_user(
            username="auditor1", password=TEST_PASSWORD, first_name="John", last_name="Auditor"  # nosec B106
        )

        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.user.groups.add(auditor_group)
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            created_by=self.user,
            lead_auditor=self.user,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

    def test_form_with_internal_auditor(self):
        """Test form with user selected (internal auditor)."""
        form_data = {
            "user": self.user.id,
            "role": "auditor",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        form = AuditTeamMemberForm(data=form_data, audit=self.audit)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())

    def test_form_with_external_expert(self):
        """Test form with external expert (no user, name required)."""
        form_data = {
            "name": "Jane External",
            "title": "Senior Consultant",
            "role": "technical_expert",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        form = AuditTeamMemberForm(data=form_data, audit=self.audit)
        self.assertTrue(form.is_valid())

    def test_form_external_expert_missing_name(self):
        """Test form validation fails when external expert has no name."""
        form_data = {
            "role": "technical_expert",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        form = AuditTeamMemberForm(data=form_data, audit=self.audit)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_date_validation_outside_audit_range(self):
        """Test form validation fails when dates are outside audit range."""
        form_data = {
            "user": self.user.id,
            "role": "auditor",
            "date_from": self.audit.total_audit_date_from - timedelta(days=1),
            "date_to": self.audit.total_audit_date_to,
        }
        form = AuditTeamMemberForm(data=form_data, audit=self.audit)
        self.assertFalse(form.is_valid())

    def test_form_date_validation_date_to_before_date_from(self):
        """Test form validation fails when date_to < date_from."""
        form_data = {
            "user": self.user.id,
            "role": "auditor",
            "date_from": self.audit.total_audit_date_to,
            "date_to": self.audit.total_audit_date_from,
        }
        form = AuditTeamMemberForm(data=form_data, audit=self.audit)
        self.assertFalse(form.is_valid())


class TeamMemberViewTests(TestCase):
    """Test team member CRUD views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-VIEW-001",
            total_employee_count=10,
        )

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(self.cb_admin_group)

        self.lead_auditor = User.objects.create_user(
            username="leadauditor", password=TEST_PASSWORD, first_name="Lead", last_name="Auditor"  # nosec B106
        )
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.regular_user = User.objects.create_user(username="regularuser", password=TEST_PASSWORD)  # nosec B106

        self.auditor_user = User.objects.create_user(
            username="auditor1", password=TEST_PASSWORD, first_name="John", last_name="Auditor"  # nosec B106
        )
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor_user.groups.add(auditor_group)

        # Create audit
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            created_by=self.lead_auditor,
            lead_auditor=self.lead_auditor,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

    def test_team_member_add_as_cb_admin(self):
        """Test cb_admin can add team members."""
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_team_member_add_as_lead_auditor(self):
        """Test lead_auditor can add team members to their audit."""
        self.client.login(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_team_member_add_permission_denied(self):
        """Test regular user cannot add team members."""
        self.client.login(username="regularuser", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_team_member_add_post_internal_auditor(self):
        """Test adding internal auditor via POST."""
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})
        data = {
            "user": self.auditor_user.id,
            "role": "auditor",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(AuditTeamMember.objects.filter(audit=self.audit, user=self.auditor_user).exists())

    def test_team_member_add_post_external_expert(self):
        """Test adding external expert via POST."""
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})
        data = {
            "name": "Jane External",
            "title": "Senior Consultant",
            "role": "technical_expert",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AuditTeamMember.objects.filter(audit=self.audit, name="Jane External").exists())

    def test_team_member_edit_as_cb_admin(self):
        """Test cb_admin can edit team members."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor_user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_edit", kwargs={"pk": member.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_team_member_edit_permission_denied(self):
        """Test regular user cannot edit team members."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor_user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )
        self.client.login(username="regularuser", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_edit", kwargs={"pk": member.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_team_member_delete_as_cb_admin(self):
        """Test cb_admin can delete team members."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor_user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )
        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_delete", kwargs={"pk": member.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AuditTeamMember.objects.filter(pk=member.pk).exists())

    def test_team_member_delete_permission_denied(self):
        """Test regular user cannot delete team members."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor_user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )
        self.client.login(username="regularuser", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_delete", kwargs={"pk": member.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AuditTeamMember.objects.filter(pk=member.pk).exists())


class CompetenceWarningTests(TestCase):
    """Test competence warning detection in team member views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-001",
            total_employee_count=10,
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(self.cb_admin_group)

        self.auditor = User.objects.create_user(
            username="auditor1", password=TEST_PASSWORD, first_name="John", last_name="Auditor"  # nosec B106
        )
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            created_by=self.auditor,
            lead_auditor=self.auditor,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

    def test_competence_warning_displayed(self):
        """Test that competence warnings are displayed in the add form."""
        # Create a competence warning
        AuditorCompetenceWarning.objects.create(
            audit=self.audit,
            auditor=self.auditor,
            warning_type="scope_mismatch",
            description="Missing required training",
            issued_by=self.cb_admin,
        )

        self.client.login(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:team_member_add", kwargs={"audit_pk": self.audit.pk})

        # Add team member with warning
        data = {
            "user": self.auditor.id,
            "role": "auditor",
            "date_from": self.audit.total_audit_date_from,
            "date_to": self.audit.total_audit_date_to,
        }
        response = self.client.post(url, data, follow=True)

        # Should still succeed but show warning in messages
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("competence warning" in str(m).lower() for m in messages))


class MultiSiteSamplingTests(TestCase):
    """Test IAF MD1 multi-site sampling calculations."""

    def test_calculate_sample_size_initial_certification(self):
        """Test IAF MD1 calculation for initial certification."""
        result = calculate_sample_size(total_sites=9, is_initial_certification=True)
        self.assertEqual(result["minimum_sites"], 3)  # √9 = 3
        self.assertEqual(result["base_calculation"], 3)

    def test_calculate_sample_size_surveillance(self):
        """Test IAF MD1 calculation for surveillance audits."""
        result = calculate_sample_size(total_sites=9, is_initial_certification=False)
        # √9 - 0.5 = 3.0 - 0.5 = 2.5 → ceil(2.5) = 3 → max(1, 3) = 3
        self.assertEqual(result["minimum_sites"], 3)
        self.assertEqual(result["base_calculation"], 3)

    def test_calculate_sample_size_with_high_risk(self):
        """Test IAF MD1 with high-risk sites adjustment."""
        result = calculate_sample_size(total_sites=10, high_risk_sites=5, is_initial_certification=True)
        # Base: √10 ≈ 3.16 → 4
        # Risk adjustment: 5 high-risk sites → +1 (per 5 sites)
        self.assertEqual(result["minimum_sites"], 5)
        self.assertGreater(result["risk_adjustment"], 0)

    def test_multi_site_display_in_view(self):
        """Test that multi-site sampling info appears in audit detail view."""
        from core.models import Site

        self.client = Client()
        org = Organization.objects.create(
            name="Multi-Site Org",
            registered_address="123 Test St",
            customer_id="CUST-002",
            total_employee_count=100,
        )

        user = User.objects.create_user(username="testuser", password=TEST_PASSWORD)  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        user.groups.add(auditor_group)
        self.client.login(username="testuser", password=TEST_PASSWORD)  # nosec B106

        audit = Audit.objects.create(
            organization=org,
            audit_type="stage1",
            created_by=user,
            lead_auditor=user,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

        # Add multiple sites
        for i in range(5):
            site = Site.objects.create(organization=org, site_name=f"Site {i+1}", site_address=f"Address {i+1}")
            audit.sites.add(site)

        url = reverse("audits:audit_detail", kwargs={"pk": audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get("is_multi_site", False))
        self.assertIn("sampling_info", response.context)


class DocumentationFormTests(TestCase):
    """Test documentation forms (US-018, US-019, US-020)."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-DOC-001",
            total_employee_count=10,
        )

        self.lead_auditor = User.objects.create_user(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        self.lead_auditor_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(self.lead_auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            created_by=self.lead_auditor,
            lead_auditor=self.lead_auditor,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

    def test_audit_changes_form_access(self):
        """Test access to organization changes form."""
        self.client.login(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_changes_edit", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_audit_plan_review_form_access(self):
        """Test access to audit plan review form."""
        self.client.login(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_plan_review_edit", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_audit_summary_form_access(self):
        """Test access to audit summary form."""
        self.client.login(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_summary_edit", kwargs={"audit_pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_audit_changes_form_save(self):
        """Test saving organization changes."""
        self.client.login(username="leadauditor", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_changes_edit", kwargs={"audit_pk": self.audit.pk})
        data = {
            "changes_identified": True,
            "change_description": "Added new location",
            "impact_assessment": "Low impact, no scope change required",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(AuditChanges.objects.filter(audit=self.audit).exists())


class AuditDetailContextTests(TestCase):
    """Test audit detail view context for Sprint 8 features."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.org = Organization.objects.create(
            name="Test Organization",
            registered_address="123 Test St",
            customer_id="CUST-DETAIL-001",
            total_employee_count=10,
        )
        self.user = User.objects.create_user(username="testuser", password=TEST_PASSWORD)  # nosec B106
        auditor_group, _ = Group.objects.get_or_create(name="auditor")
        self.user.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            created_by=self.user,
            lead_auditor=self.user,
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=7),
        )

    def test_audit_detail_shows_team_members(self):
        """Test that audit detail shows team members."""
        # Add team member
        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        self.client.login(username="testuser", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_detail", kwargs={"pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.get_full_name() or self.user.username)

    def test_audit_detail_shows_internal_external_badges(self):
        """Test that internal/external badges are displayed."""
        # Add internal member
        AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.user,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        # Add external member
        AuditTeamMember.objects.create(
            audit=self.audit,
            name="Jane External",
            role="technical_expert",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        self.client.login(username="testuser", password=TEST_PASSWORD)  # nosec B106
        url = reverse("audits:audit_detail", kwargs={"pk": self.audit.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internal")
        self.assertContains(response, "External")

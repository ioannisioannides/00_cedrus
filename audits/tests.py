"""
Comprehensive tests for audits app: audits, findings, workflows, permissions.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from audits.models import (
    Audit,
    AuditChanges,
    AuditPlanReview,
    AuditRecommendation,
    AuditSummary,
    AuditTeamMember,
    Nonconformity,
    Observation,
    OpportunityForImprovement,
)
from core.models import Certification, Organization, Site, Standard


class AuditModelTest(TestCase):
    """Test Audit model validation and relationships."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Test scope",
            certificate_status="active",
        )
        self.site = Site.objects.create(
            organization=self.org, site_name="Test Site", site_address="456 St"
        )
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        lead_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_group)
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

    def test_create_audit(self):
        """Test creating a basic audit."""
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        audit.certifications.add(self.cert)
        audit.sites.add(self.site)

        self.assertEqual(audit.organization, self.org)
        self.assertEqual(audit.audit_type, "stage2")
        self.assertEqual(audit.status, "draft")
        self.assertIn(self.cert, audit.certifications.all())
        self.assertIn(self.site, audit.sites.all())

    def test_audit_cascade_organization(self):
        """Test that audits are deleted when organization is deleted."""
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        audit_id = audit.id
        self.org.delete()
        self.assertFalse(Audit.objects.filter(id=audit_id).exists())

    def test_audit_protect_created_by(self):
        """Test that created_by user cannot be deleted if audits exist."""
        Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        with self.assertRaises(Exception):  # ProtectedError
            self.cb_admin.delete()

    def test_audit_protect_lead_auditor(self):
        """Test that lead_auditor cannot be deleted if audits exist."""
        Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        with self.assertRaises(Exception):  # ProtectedError
            self.lead_auditor.delete()

    def test_audit_duration_validation(self):
        """Test that planned_duration_hours must be >= 0."""
        # Note: MinValueValidator is at model level
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=0.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.assertEqual(audit.planned_duration_hours, 0.0)

    def test_audit_str(self):
        """Test audit string representation."""
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.assertIn("Test Org", str(audit))
        self.assertIn("Stage 2", str(audit))
        self.assertIn("Draft", str(audit))


class AuditViewPermissionTest(TestCase):
    """Test audit view permissions."""

    def setUp(self):
        self.client = Client()

        # Create users
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        self.auditor = User.objects.create_user(username="auditor", password="pass123")
        self.client_admin = User.objects.create_user(username="clientadmin", password="pass123")
        self.other_lead = User.objects.create_user(username="otherlead", password="pass123")

        # Create groups
        cb_group = Group.objects.create(name="cb_admin")
        lead_group = Group.objects.create(name="lead_auditor")
        auditor_group = Group.objects.create(name="auditor")
        client_admin_group = Group.objects.create(name="client_admin")

        self.cb_admin.groups.add(cb_group)
        self.lead_auditor.groups.add(lead_group)
        self.auditor.groups.add(auditor_group)
        self.client_admin.groups.add(client_admin_group)
        self.other_lead.groups.add(lead_group)

        # Create organization
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.org2 = Organization.objects.create(
            name="Other Org",
            registered_address="456 St",
            customer_id="ORG002",
            total_employee_count=5,
        )

        # Create audit
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

        # Assign client to organization
        self.client_admin.profile.organization = self.org
        self.client_admin.profile.save()

    def test_audit_list_cb_admin(self):
        """Test CB Admin can see all audits."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.audit, response.context["audits"])

    def test_audit_list_lead_auditor(self):
        """Test Lead Auditor sees only assigned audits."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.audit, response.context["audits"])

        # Other lead should not see this audit
        self.client.login(username="otherlead", password="pass123")
        response = self.client.get(reverse("audits:audit_list"))
        self.assertNotIn(self.audit, response.context["audits"])

    def test_audit_list_client_admin(self):
        """Test Client Admin sees only their organization's audits."""
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.audit, response.context["audits"])

        # Create audit for other org
        audit2 = Audit.objects.create(
            organization=self.org2,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        response = self.client.get(reverse("audits:audit_list"))
        self.assertNotIn(audit2, response.context["audits"])

    def test_audit_create_cb_admin(self):
        """Test CB Admin can create audit."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 200)

    def test_audit_create_lead_auditor(self):
        """Test Lead Auditor cannot create audit."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 403)

    def test_audit_create_client_admin(self):
        """Test Client Admin cannot create audit."""
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_create"))
        self.assertEqual(response.status_code, 403)

    def test_audit_detail_cb_admin(self):
        """Test CB Admin can view any audit."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["audit"], self.audit)

    def test_audit_detail_lead_auditor_own(self):
        """Test Lead Auditor can view own audit."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_audit_detail_lead_auditor_other(self):
        """Test Lead Auditor cannot view other's audit."""
        self.client.login(username="otherlead", password="pass123")
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 404)  # Queryset filtered

    def test_audit_detail_client_admin_own_org(self):
        """Test Client Admin can view their org's audit."""
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_detail", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_audit_detail_client_admin_other_org(self):
        """Test Client Admin cannot view other org's audit."""
        audit2 = Audit.objects.create(
            organization=self.org2,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_detail", args=[audit2.pk]))
        self.assertEqual(response.status_code, 404)

    def test_audit_update_cb_admin(self):
        """Test CB Admin can update any audit."""
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_update", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_audit_update_lead_auditor_own(self):
        """Test Lead Auditor can update own audit."""
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_update", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

    def test_audit_update_lead_auditor_other(self):
        """Test Lead Auditor cannot update other's audit."""
        self.client.login(username="otherlead", password="pass123")
        response = self.client.get(reverse("audits:audit_update", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 403)

    def test_audit_update_auditor(self):
        """Test Auditor cannot update audit."""
        self.client.login(username="auditor", password="pass123")
        response = self.client.get(reverse("audits:audit_update", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 403)

    def test_audit_update_client_admin(self):
        """Test Client Admin cannot update audit."""
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_update", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 403)

    def test_audit_print_permission(self):
        """Test audit print view permissions."""
        # CB Admin
        self.client.login(username="cbadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_print", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

        # Lead Auditor (own audit)
        self.client.login(username="lead", password="pass123")
        response = self.client.get(reverse("audits:audit_print", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

        # Client Admin (own org)
        self.client.login(username="clientadmin", password="pass123")
        response = self.client.get(reverse("audits:audit_print", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 200)

        # Other Lead Auditor
        self.client.login(username="otherlead", password="pass123")
        response = self.client.get(reverse("audits:audit_print", args=[self.audit.pk]))
        self.assertRedirects(response, reverse("audits:audit_list"))


class FindingModelTest(TestCase):
    """Test Finding models (Nonconformity, Observation, OFI)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management Systems")
        self.auditor = User.objects.create_user(username="auditor", password="pass123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        lead_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_group)
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_create_nonconformity(self):
        """Test creating a nonconformity."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence here",
            statement_of_nc="NC statement",
            auditor_explanation="Explanation",
            created_by=self.auditor,
        )
        self.assertEqual(nc.audit, self.audit)
        self.assertEqual(nc.clause, "7.5.1")
        self.assertEqual(nc.category, "major")
        self.assertEqual(nc.verification_status, "open")

    def test_nonconformity_cascade_audit(self):
        """Test that nonconformities are deleted when audit is deleted."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            auditor_explanation="Explanation",
            created_by=self.auditor,
        )
        nc_id = nc.id
        self.audit.delete()
        self.assertFalse(Nonconformity.objects.filter(id=nc_id).exists())

    def test_nonconformity_verification_workflow(self):
        """Test nonconformity verification status workflow."""
        nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="7.5.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            auditor_explanation="Explanation",
            created_by=self.auditor,
        )
        self.assertEqual(nc.verification_status, "open")

        # Client responds
        nc.verification_status = "client_responded"
        nc.client_root_cause = "Root cause"
        nc.client_correction = "Correction"
        nc.client_corrective_action = "Corrective action"
        nc.save()
        self.assertEqual(nc.verification_status, "client_responded")

        # Auditor verifies
        nc.verification_status = "accepted"
        nc.verified_by = self.lead_auditor
        nc.verified_at = date.today()
        nc.save()
        self.assertEqual(nc.verification_status, "accepted")
        self.assertEqual(nc.verified_by, self.lead_auditor)

    def test_create_observation(self):
        """Test creating an observation."""
        obs = Observation.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="8.2.1",
            statement="Observation statement",
            explanation="Additional explanation",
            created_by=self.auditor,
        )
        self.assertEqual(obs.audit, self.audit)
        self.assertEqual(obs.clause, "8.2.1")
        self.assertEqual(obs.statement, "Observation statement")

    def test_create_opportunity_for_improvement(self):
        """Test creating an OFI."""
        ofi = OpportunityForImprovement.objects.create(
            audit=self.audit,
            standard=self.std,
            clause="9.1.1",
            description="Opportunity description",
            created_by=self.auditor,
        )
        self.assertEqual(ofi.audit, self.audit)
        self.assertEqual(ofi.clause, "9.1.1")
        self.assertEqual(ofi.description, "Opportunity description")


class AuditTeamMemberTest(TestCase):
    """Test AuditTeamMember model."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        lead_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_group)
        self.auditor = User.objects.create_user(username="auditor", password="pass123")
        auditor_group = Group.objects.create(name="auditor")
        self.auditor.groups.add(auditor_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_create_team_member_with_user(self):
        """Test creating team member with user account."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            name=self.auditor.get_full_name() or self.auditor.username,
            role="auditor",
            date_from=date.today(),
            date_to=date.today() + timedelta(days=2),
        )
        self.assertEqual(member.audit, self.audit)
        self.assertEqual(member.user, self.auditor)
        self.assertEqual(member.role, "auditor")

    def test_create_team_member_external(self):
        """Test creating team member without user (external expert)."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=None,
            name="External Expert",
            title="Technical Expert",
            role="technical_expert",
            date_from=date.today(),
            date_to=date.today() + timedelta(days=2),
        )
        self.assertIsNone(member.user)
        self.assertEqual(member.name, "External Expert")
        self.assertEqual(member.role, "technical_expert")

    def test_team_member_validation(self):
        """Test that team member must have either user or name."""
        # This validation is in clean() method, but needs to be called explicitly
        member = AuditTeamMember(
            audit=self.audit,
            user=None,
            name="",  # Empty name
            role="auditor",
            date_from=date.today(),
            date_to=date.today() + timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            member.full_clean()

    def test_team_member_cascade_audit(self):
        """Test that team members are deleted when audit is deleted."""
        member = AuditTeamMember.objects.create(
            audit=self.audit,
            user=self.auditor,
            name="Test Member",
            role="auditor",
            date_from=date.today(),
            date_to=date.today() + timedelta(days=2),
        )
        member_id = member.id
        self.audit.delete()
        self.assertFalse(AuditTeamMember.objects.filter(id=member_id).exists())


class AuditMetadataTest(TestCase):
    """Test audit metadata models (Changes, PlanReview, Summary, Recommendation)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass123")
        cb_group = Group.objects.create(name="cb_admin")
        self.cb_admin.groups.add(cb_group)
        self.lead_auditor = User.objects.create_user(username="lead", password="pass123")
        lead_group = Group.objects.create(name="lead_auditor")
        self.lead_auditor.groups.add(lead_group)

        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=3),
            planned_duration_hours=24.0,
            status="draft",
            created_by=self.cb_admin,
            lead_auditor=self.lead_auditor,
        )

    def test_audit_changes_one_to_one(self):
        """Test AuditChanges one-to-one relationship."""
        changes = AuditChanges.objects.create(audit=self.audit)
        self.assertEqual(changes.audit, self.audit)
        self.assertEqual(self.audit.changes, changes)

        # Should not be able to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            AuditChanges.objects.create(audit=self.audit)

    def test_audit_plan_review_one_to_one(self):
        """Test AuditPlanReview one-to-one relationship."""
        plan_review = AuditPlanReview.objects.create(audit=self.audit)
        self.assertEqual(plan_review.audit, self.audit)
        self.assertEqual(self.audit.plan_review, plan_review)

    def test_audit_summary_one_to_one(self):
        """Test AuditSummary one-to-one relationship."""
        summary = AuditSummary.objects.create(audit=self.audit)
        self.assertEqual(summary.audit, self.audit)
        self.assertEqual(self.audit.summary, summary)

    def test_audit_recommendation_one_to_one(self):
        """Test AuditRecommendation one-to-one relationship."""
        recommendation = AuditRecommendation.objects.create(audit=self.audit)
        self.assertEqual(recommendation.audit, self.audit)
        self.assertEqual(self.audit.recommendation, recommendation)

    def test_audit_metadata_auto_create(self):
        """Test that metadata records can be auto-created with get_or_create."""
        changes, created = AuditChanges.objects.get_or_create(audit=self.audit)
        self.assertTrue(created)

        changes2, created2 = AuditChanges.objects.get_or_create(audit=self.audit)
        self.assertFalse(created2)
        self.assertEqual(changes, changes2)

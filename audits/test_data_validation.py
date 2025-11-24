"""
Test suite for Sprint 7 Task 7.3: Data Validation Implementation

Tests all new validation rules:
1. Future date validation
2. Audit sequence validation (Stage 2 requires Stage 1)
3. Surveillance audit validation (requires active certification)
4. Finding-standard validation (standard must be in audit's certifications)
5. Team member role validation
6. Site organization validation
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from audits.models import Audit, AuditTeamMember, Nonconformity, Observation
from audits.workflows import AuditWorkflow
from core.models import Certification, Organization, Site, Standard


class FutureDateValidationTests(TestCase):
    """Test future date validation for audits."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="active",
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )
        self.user = User.objects.create_user(username="leadauditor", password="pass")
        self.auditor_group = Group.objects.get_or_create(name="lead_auditor")[0]
        self.user.groups.add(self.auditor_group)

    def test_audit_cannot_be_more_than_one_year_in_future(self):
        """Audit start date cannot be more than 1 year in the future."""
        two_years_ahead = timezone.now().date() + timedelta(days=730)

        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=two_years_ahead,
            total_audit_date_to=two_years_ahead + timedelta(days=3),
            lead_auditor=self.user,
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as cm:
            audit.full_clean()  # full_clean() includes clean()

        self.assertIn("cannot be more than 1 year in the future", str(cm.exception))

    def test_audit_within_one_year_is_valid(self):
        """Audit within 1 year in future is valid."""
        six_months_ahead = timezone.now().date() + timedelta(days=180)

        audit = Audit(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=six_months_ahead,
            total_audit_date_to=six_months_ahead + timedelta(days=3),
            lead_auditor=self.user,
            created_by=self.user,
        )

        # Should not raise
        audit.clean()


class AuditSequenceValidationTests(TestCase):
    """Test audit sequence validation (Stage 2 requires Stage 1)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="active",
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )
        self.user = User.objects.create_user(username="leadauditor", password="pass")
        self.auditor_group = Group.objects.get_or_create(name="lead_auditor")[0]
        self.user.groups.add(self.auditor_group)

    def test_stage2_cannot_proceed_to_technical_review_without_stage1(self):
        """Stage 2 cannot proceed to closure without completed Stage 1."""
        # Create CB Admin for transition check
        cb_admin = User.objects.create_user(username="cbadmin_val", password="pass")
        cb_admin.groups.add(Group.objects.get_or_create(name="cb_admin")[0])

        today = timezone.now().date()

        # Create Stage 2 without Stage 1
        stage2 = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=3),
            lead_auditor=self.user,
            created_by=self.user,
            status="decision_pending",
        )
        stage2.certifications.add(self.cert)
        stage2.sites.add(self.site)

        workflow = AuditWorkflow(stage2)
        can_transition, reason = workflow.can_transition("closed", cb_admin)

        self.assertFalse(can_transition)
        self.assertIn("Stage 2 audit requires a completed Stage 1", reason)

    def test_surveillance_cannot_proceed_without_active_certification(self):
        """Surveillance cannot proceed to closure without active certification."""
        # Create CB Admin for transition check
        if not User.objects.filter(username="cbadmin_val").exists():
            cb_admin = User.objects.create_user(username="cbadmin_val", password="pass")
            cb_admin.groups.add(Group.objects.get_or_create(name="cb_admin")[0])
        else:
            cb_admin = User.objects.get(username="cbadmin_val")

        today = timezone.now().date()

        # Update existing certification to draft status instead of creating new one
        self.cert.certificate_status = "draft"
        self.cert.save()

        surveillance = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=2),
            lead_auditor=self.user,
            created_by=self.user,
            status="decision_pending",
        )
        surveillance.certifications.add(self.cert)
        surveillance.sites.add(self.site)

        workflow = AuditWorkflow(surveillance)
        can_transition, reason = workflow.can_transition("closed", cb_admin)

        self.assertFalse(can_transition)
        self.assertIn("requires active certifications", reason)

    def test_stage2_valid_after_stage1_closed(self):
        """Stage 2 is valid after Stage 1 is closed."""
        today = timezone.now().date()

        # Create and close Stage 1
        stage1 = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=today - timedelta(days=30),
            total_audit_date_to=today - timedelta(days=27),
            lead_auditor=self.user,
            created_by=self.user,
            status="closed",  # Changed from "decided" to "closed"
        )
        stage1.certifications.add(self.cert)
        stage1.sites.add(self.site)

        # Now Stage 2 should be valid
        stage2 = Audit(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=3),
            lead_auditor=self.user,
            created_by=self.user,
        )

        # Should not raise
        stage2.clean()


class SurveillanceAuditValidationTests(TestCase):
    """Test surveillance audit validation (requires active certification)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )
        self.user = User.objects.create_user(username="leadauditor", password="pass")
        self.auditor_group = Group.objects.get_or_create(name="lead_auditor")[0]
        self.user.groups.add(self.auditor_group)

    def test_surveillance_requires_active_certification(self):
        """Surveillance audit requires at least one active certification."""
        today = timezone.now().date()

        # Create draft certification (not active)
        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="draft",
        )

        audit = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=2),
            lead_auditor=self.user,
            created_by=self.user,
        )
        audit.certifications.add(cert)
        audit.sites.add(self.site)

        with self.assertRaises(ValidationError) as cm:
            audit.full_clean()  # full_clean() includes clean()

        self.assertIn("requires at least one active certification", str(cm.exception))

    def test_surveillance_valid_with_active_certification(self):
        """Surveillance audit is valid with active certification."""
        today = timezone.now().date()

        cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="active",
        )

        audit = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=2),
            lead_auditor=self.user,
            created_by=self.user,
        )
        audit.certifications.add(cert)
        audit.sites.add(self.site)

        # Should not raise
        audit.clean()


class FindingStandardValidationTests(TestCase):
    """Test finding-standard validation (standard must be in audit's certifications)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std_iso9001 = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.std_iso27001 = Standard.objects.create(
            code="ISO 27001:2013", title="Information Security"
        )

        self.cert_iso9001 = Certification.objects.create(
            organization=self.org,
            standard=self.std_iso9001,
            certification_scope="Software",
            certificate_status="active",
        )

        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )

        self.user = User.objects.create_user(username="auditor", password="pass")
        self.auditor_group = Group.objects.get_or_create(name="auditor")[0]
        self.user.groups.add(self.auditor_group)

        today = timezone.now().date()
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=3),
            lead_auditor=self.user,
            created_by=self.user,
        )
        self.audit.certifications.add(self.cert_iso9001)
        self.audit.sites.add(self.site)

    def test_finding_standard_must_be_in_audit_certifications(self):
        """Finding standard must be part of audit's certifications."""
        nc = Nonconformity(
            audit=self.audit,
            standard=self.std_iso27001,  # NOT in audit's certifications
            clause="7.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            auditor_explanation="Explanation",
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as cm:
            nc.clean()

        self.assertIn("is not part of this audit's certifications", str(cm.exception))
        self.assertIn("ISO 27001:2013", str(cm.exception))

    def test_finding_valid_with_correct_standard(self):
        """Finding is valid when standard is in audit's certifications."""
        nc = Nonconformity(
            audit=self.audit,
            standard=self.std_iso9001,  # IS in audit's certifications
            clause="7.1",
            category="major",
            objective_evidence="Evidence",
            statement_of_nc="Statement",
            auditor_explanation="Explanation",
            created_by=self.user,
        )

        # Should not raise
        nc.clean()

    def test_observation_standard_validation(self):
        """Observation also validates standard belongs to audit."""
        obs = Observation(
            audit=self.audit,
            standard=self.std_iso27001,  # NOT in audit's certifications
            clause="5.1",
            statement="Observation statement",
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as cm:
            obs.clean()

        self.assertIn("is not part of this audit's certifications", str(cm.exception))


class TeamMemberRoleValidationTests(TestCase):
    """Test team member role validation."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="active",
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )

        self.auditor_user = User.objects.create_user(username="auditor", password="pass")
        self.auditor_group = Group.objects.get_or_create(name="auditor")[0]
        self.auditor_user.groups.add(self.auditor_group)

        self.client_user = User.objects.create_user(username="client", password="pass")
        self.client_group = Group.objects.get_or_create(name="client_user")[0]
        self.client_user.groups.add(self.client_group)

        today = timezone.now().date()
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage1",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=3),
            lead_auditor=self.auditor_user,
            created_by=self.auditor_user,
        )
        self.audit.certifications.add(self.cert)
        self.audit.sites.add(self.site)

    def test_non_auditor_cannot_be_assigned_as_auditor(self):
        """User without auditor role cannot be assigned as auditor."""
        team_member = AuditTeamMember(
            audit=self.audit,
            user=self.client_user,  # Client user, not auditor
            name=self.client_user.username,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        with self.assertRaises(ValidationError) as cm:
            team_member.clean()

        self.assertIn("does not have an auditor role", str(cm.exception))

    def test_auditor_can_be_assigned_as_auditor(self):
        """User with auditor role can be assigned as auditor."""
        team_member = AuditTeamMember(
            audit=self.audit,
            user=self.auditor_user,
            name=self.auditor_user.username,
            role="auditor",
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        # Should not raise
        team_member.clean()

    def test_non_auditor_can_be_observer(self):
        """Non-auditor can be assigned as observer."""
        team_member = AuditTeamMember(
            audit=self.audit,
            user=self.client_user,
            name=self.client_user.username,
            role="observer",  # Observer doesn't require auditor role
            date_from=self.audit.total_audit_date_from,
            date_to=self.audit.total_audit_date_to,
        )

        # Should not raise
        team_member.clean()


class WorkflowAuditSequenceValidationTests(TestCase):
    """Test workflow validation for audit sequences."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            customer_id="TEST001",
            registered_address="123 Test St",
            total_employee_count=50,
        )
        self.std = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std,
            certification_scope="Software",
            certificate_status="active",
        )
        self.site = Site.objects.create(
            organization=self.org,
            site_name="HQ",
            site_address="123 Test St",
            site_employee_count=50,
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.cb_admin_group = Group.objects.get_or_create(name="cb_admin")[0]
        self.cb_admin.groups.add(self.cb_admin_group)

    def test_stage2_cannot_close_without_stage1(self):
        """Stage 2 cannot close without completed Stage 1."""
        today = timezone.now().date()

        # Create Stage 2 without Stage 1
        stage2 = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=3),
            lead_auditor=self.cb_admin,
            created_by=self.cb_admin,
            status="decision_pending",
        )
        stage2.certifications.add(self.cert)
        stage2.sites.add(self.site)

        workflow = AuditWorkflow(stage2)
        can_transition, reason = workflow.can_transition("closed", self.cb_admin)

        self.assertFalse(can_transition)
        self.assertIn("Stage 2 audit requires a completed Stage 1", reason)

    def test_surveillance_cannot_close_without_active_certification(self):
        """Surveillance cannot close without active certification."""
        today = timezone.now().date()

        # Update existing certification to draft status instead of creating new one
        self.cert.certificate_status = "draft"
        self.cert.save()

        surveillance = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=today,
            total_audit_date_to=today + timedelta(days=2),
            lead_auditor=self.cb_admin,
            created_by=self.cb_admin,
            status="decision_pending",
        )
        surveillance.certifications.add(self.cert)
        surveillance.sites.add(self.site)

        workflow = AuditWorkflow(surveillance)
        can_transition, reason = workflow.can_transition("closed", self.cb_admin)

        self.assertFalse(can_transition)
        self.assertIn("requires active certifications", reason)

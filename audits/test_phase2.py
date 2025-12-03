"""
Phase 2 Unit Tests

Tests for:
- Root cause analysis models (RootCauseCategory, FindingRecurrence)
- Auditor competence tracking (AuditorCompetenceWarning)
- IAF MD1 sampling algorithm
- IAF MD5 duration validation
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from audits.models import (
    Audit,
    AuditorCompetenceWarning,
    FindingRecurrence,
    Nonconformity,
    RootCauseCategory,
)
from core.models import Certification, Organization, Site, Standard
from core.test_utils import TEST_PASSWORD
from trunk.services.duration_validator import (
    calculate_complexity_factor,
    get_base_duration,
    validate_audit_duration,
)
from trunk.services.sampling import calculate_sample_size, validate_site_selection


class RootCauseCategoryTests(TestCase):
    """Test RootCauseCategory model and hierarchy."""

    def setUp(self):
        """Create test categories."""
        self.parent = RootCauseCategory.objects.create(
            name="Resource Issues", code="RC-100", description="Issues related to resource adequacy"
        )

        self.child = RootCauseCategory.objects.create(
            name="Training Deficiency",
            code="RC-101",
            description="Insufficient or inadequate training",
            parent=self.parent,
        )

    def test_category_creation(self):
        """Test basic category creation."""
        self.assertEqual(self.parent.name, "Resource Issues")
        self.assertEqual(self.parent.code, "RC-100")
        self.assertTrue(self.parent.is_active)

    def test_hierarchical_structure(self):
        """Test parent-child relationship."""
        self.assertEqual(self.child.parent, self.parent)
        self.assertIn(self.child, self.parent.subcategories.all())

    def test_category_str_representation(self):
        """Test __str__ method."""
        self.assertEqual(str(self.parent), "RC-100: Resource Issues")
        self.assertIn("RC-100 > RC-101", str(self.child))

    def test_category_activation(self):
        """Test deactivating a category."""
        self.parent.is_active = False
        self.parent.save()

        self.assertFalse(self.parent.is_active)
        # Child remains active independently
        self.assertTrue(self.child.is_active)


class FindingRecurrenceTests(TestCase):
    """Test FindingRecurrence model for tracking repeat findings."""

    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        self.org = Organization.objects.create(name="Test Org", customer_id="C001", total_employee_count=50)
        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")
        self.cert = Certification.objects.create(
            organization=self.org, standard=self.standard, certification_scope="Manufacturing"
        )
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            created_by=self.user,
            lead_auditor=self.user,
        )
        self.nc = Nonconformity.objects.create(
            audit=self.audit,
            standard=self.standard,
            clause="7.5.1",
            category="minor",
            objective_evidence="Test evidence",
            statement_of_nc="Test NC",
            auditor_explanation="Test explanation",
            created_by=self.user,
        )

    def test_recurrence_creation(self):
        """Test creating recurrence data for a finding."""
        recurrence = FindingRecurrence.objects.create(
            finding=self.nc,
            recurrence_count=2,
            first_occurrence=date.today() - timedelta(days=365),
            last_occurrence=date.today(),
            previous_audits="Audit A001, Audit A002",
            corrective_actions_effective=False,
            resolution_notes="Still recurring after corrective action",
        )

        self.assertEqual(recurrence.finding, self.nc)
        self.assertEqual(recurrence.recurrence_count, 2)
        self.assertFalse(recurrence.corrective_actions_effective)

    def test_escalation_flag(self):
        """Test escalation flag for high-recurrence findings."""
        recurrence = FindingRecurrence.objects.create(
            finding=self.nc,
            recurrence_count=4,
            first_occurrence=date.today() - timedelta(days=730),
            last_occurrence=date.today(),
            escalation_required=True,
        )

        self.assertTrue(recurrence.escalation_required)

    def test_one_to_one_relationship(self):
        """Test that one finding can only have one recurrence record."""
        FindingRecurrence.objects.create(
            finding=self.nc,
            recurrence_count=1,
            first_occurrence=date.today(),
            last_occurrence=date.today(),
        )

        # Attempting to create another should raise an error
        with self.assertRaises(IntegrityError):
            FindingRecurrence.objects.create(
                finding=self.nc,
                recurrence_count=2,
                first_occurrence=date.today(),
                last_occurrence=date.today(),
            )


class AuditorCompetenceWarningTests(TestCase):
    """Test AuditorCompetenceWarning model."""

    def setUp(self):
        """Create test data."""
        self.auditor = User.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106
        self.org = Organization.objects.create(name="Test Org", customer_id="C001", total_employee_count=50)
        self.audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=8.0,
            created_by=self.cb_admin,
            lead_auditor=self.auditor,
        )

    def test_warning_creation(self):
        """Test creating a competence warning."""
        warning = AuditorCompetenceWarning.objects.create(
            audit=self.audit,
            auditor=self.auditor,
            warning_type="scope_mismatch",
            severity="high",
            description="Auditor lacks experience in aerospace sector",
            issued_by=self.cb_admin,
        )

        self.assertEqual(warning.auditor, self.auditor)
        self.assertEqual(warning.warning_type, "scope_mismatch")
        self.assertEqual(warning.severity, "high")
        self.assertIsNone(warning.resolved_at)
        self.assertFalse(warning.is_resolved())

    def test_warning_resolution(self):
        """Test resolving a competence warning."""
        warning = AuditorCompetenceWarning.objects.create(
            audit=self.audit,
            auditor=self.auditor,
            warning_type="expired_qualification",
            severity="critical",
            description="ISO 9001 qualification expired",
            issued_by=self.cb_admin,
        )

        # Resolve the warning
        from django.utils import timezone

        warning.resolved_at = timezone.now()
        warning.resolution_notes = "Auditor renewed qualification"
        warning.save()

        self.assertTrue(warning.is_resolved())
        self.assertEqual(warning.resolution_notes, "Auditor renewed qualification")

    def test_acknowledgement_tracking(self):
        """Test auditor acknowledgement of warning."""
        warning = AuditorCompetenceWarning.objects.create(
            audit=self.audit,
            auditor=self.auditor,
            warning_type="insufficient_experience",
            severity="medium",
            description="Only 2 years of auditing experience",
            issued_by=self.cb_admin,
        )

        self.assertFalse(warning.acknowledged_by_auditor)

        warning.acknowledged_by_auditor = True
        warning.save()

        self.assertTrue(warning.acknowledged_by_auditor)


class IAFmd1SamplingTests(TestCase):
    """Test IAF MD1 sampling algorithm."""

    def test_small_org_initial_cert(self):
        """Test sampling for small org (5 sites) - initial certification."""
        result = calculate_sample_size(total_sites=5, is_initial_certification=True)

        # √5 = 2.24, round up to 3
        self.assertEqual(result["minimum_sites"], 3)
        self.assertEqual(result["base_calculation"], 3)
        self.assertEqual(result["risk_adjustment"], 0)
        self.assertEqual(result["audit_type"], "initial certification")

    def test_medium_org_surveillance(self):
        """Test sampling for medium org (25 sites) - surveillance."""
        result = calculate_sample_size(total_sites=25, is_initial_certification=False)

        # √25 - 0.5 = 4.5, round up to 5
        self.assertEqual(result["minimum_sites"], 5)
        self.assertEqual(result["base_calculation"], 5)
        self.assertEqual(result["audit_type"], "surveillance")

    def test_large_org_with_high_risk(self):
        """Test sampling for large org (100 sites) with high-risk sites."""
        result = calculate_sample_size(total_sites=100, high_risk_sites=10, is_initial_certification=False)

        # √100 - 0.5 = 9.5 → 10, + 2 for 10 high-risk sites
        self.assertEqual(result["minimum_sites"], 12)
        self.assertEqual(result["base_calculation"], 10)
        self.assertEqual(result["risk_adjustment"], 2)
        self.assertIn("High-risk sites", result["risk_factors"][0])

    def test_previous_ncs_adjustment(self):
        """Test sampling adjustment for previous major NCs."""
        result = calculate_sample_size(total_sites=36, previous_findings_count=5, is_initial_certification=True)

        # √36 = 6, + 20% = 1.2 → 2 additional
        self.assertEqual(result["minimum_sites"], 8)
        self.assertEqual(result["base_calculation"], 6)
        self.assertEqual(result["risk_adjustment"], 2)

    def test_high_scope_variation(self):
        """Test sampling with high scope variation."""
        result = calculate_sample_size(total_sites=16, scope_variation="high", is_initial_certification=True)

        # √16 = 4, + 2 for high variation
        self.assertEqual(result["minimum_sites"], 6)
        self.assertEqual(result["base_calculation"], 4)
        self.assertEqual(result["risk_adjustment"], 2)

    def test_single_site_organization(self):
        """Test edge case: single-site organization."""
        result = calculate_sample_size(total_sites=1, is_initial_certification=True)

        self.assertEqual(result["minimum_sites"], 1)
        self.assertEqual(result["base_calculation"], 1)

    def test_very_large_organization(self):
        """Test sampling for very large org (1000 sites)."""
        result = calculate_sample_size(total_sites=1000, is_initial_certification=False)

        # √1000 - 0.5 ≈ 31.12, round up to 32
        self.assertEqual(result["minimum_sites"], 32)

    def test_site_selection_validation_valid(self):
        """Test valid site selection."""
        validation = validate_site_selection(selected_sites=5, required_minimum=5, total_sites=10)

        self.assertTrue(validation["is_valid"])
        self.assertEqual(validation["shortfall"], 0)

    def test_site_selection_validation_insufficient(self):
        """Test insufficient site selection."""
        validation = validate_site_selection(selected_sites=3, required_minimum=5, total_sites=10)

        self.assertFalse(validation["is_valid"])
        self.assertEqual(validation["shortfall"], 2)
        self.assertIn("Need 2 more site(s)", validation["message"])

    def test_invalid_total_sites(self):
        """Test error handling for invalid input."""
        with self.assertRaises(ValueError):
            calculate_sample_size(total_sites=0, is_initial_certification=True)


class IAFmd5DurationTests(TestCase):
    """Test IAF MD5 duration validation."""

    def test_base_duration_small_org(self):
        """Test base duration lookup for small organization."""
        duration = get_base_duration(employee_count=15, standard_code="ISO 9001")

        self.assertEqual(duration, 8.0)  # 11-15 employees = 8 hours

    def test_base_duration_medium_org(self):
        """Test base duration for medium organization."""
        duration = get_base_duration(employee_count=100, standard_code="ISO 9001")

        self.assertEqual(duration, 21.0)  # 86-125 employees = 21 hours

    def test_base_duration_large_org(self):
        """Test base duration for large organization (>10,500 employees)."""
        duration = get_base_duration(employee_count=12500, standard_code="ISO 9001")

        # 10,500 base = 133 hours + 1 increment of 14 hours = 147
        self.assertEqual(duration, 147.0)

    def test_complexity_factor_multisite(self):
        """Test complexity factor for multi-site organization."""
        factor, reasons = calculate_complexity_factor(number_of_sites=3)

        self.assertGreater(factor, 1.0)  # Should increase duration
        self.assertIn("Multi-site", reasons[0])

    def test_complexity_factor_complex_processes(self):
        """Test complexity factor for complex processes."""
        factor, _ = calculate_complexity_factor(process_complexity="complex")

        self.assertEqual(factor, 1.15)  # +15% for complex processes

    def test_complexity_factor_high_regulatory(self):
        """Test complexity factor for high regulatory environment."""
        factor, _ = calculate_complexity_factor(regulatory_environment="high")

        self.assertEqual(factor, 1.10)  # +10% for high regulatory

    def test_complexity_factor_limits(self):
        """Test complexity factor is capped at 1.3."""
        factor, _ = calculate_complexity_factor(
            number_of_sites=10,
            scope_variation="high",
            process_complexity="complex",
            regulatory_environment="high",
            has_outsourced_processes=True,
            previous_major_ncs=5,
        )

        self.assertLessEqual(factor, 1.3)  # Should be capped at 1.3

    def test_duration_validation_compliant(self):
        """Test duration validation for compliant audit."""
        result = validate_audit_duration(planned_hours=21.0, employee_count=100, is_initial_certification=True)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["severity"], "compliant")
        self.assertEqual(result["shortfall_hours"], 0)

    def test_duration_validation_insufficient(self):
        """Test duration validation for insufficient audit."""
        result = validate_audit_duration(planned_hours=15.0, employee_count=100, is_initial_certification=True)

        self.assertFalse(result["is_valid"])
        self.assertIn("critical", result["severity"].lower())
        self.assertGreater(result["shortfall_hours"], 0)

    def test_surveillance_duration_reduction(self):
        """Test that surveillance audits have reduced duration."""
        initial_result = validate_audit_duration(planned_hours=21.0, employee_count=100, is_initial_certification=True)

        surveillance_result = validate_audit_duration(
            planned_hours=14.0, employee_count=100, is_initial_certification=False
        )

        self.assertLess(surveillance_result["required_minimum"], initial_result["required_minimum"])

    def test_warning_severity_for_minor_shortfall(self):
        """Test warning (not critical) for minor shortfall."""
        result = validate_audit_duration(
            planned_hours=19.5,
            employee_count=100,
            is_initial_certification=True,  # Just 1.5 hours short
        )

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["severity"], "warning")
        self.assertLessEqual(result["shortfall_hours"], 2)

    def test_invalid_employee_count(self):
        """Test error handling for invalid employee count."""
        with self.assertRaises(ValueError):
            get_base_duration(employee_count=0)


class Phase2IntegrationTests(TestCase):
    """Integration tests combining Phase 2 features."""

    def setUp(self):
        """
        Prepare a multi-site audit test fixture by creating users, an organization with ten sites, a standard, and a certification.
        
        Creates the following attributes on self:
        - auditor: test user with username "auditor"
        - cb_admin: test user with username "cbadmin"
        - org: Organization named "Multi-Site Manufacturing Corp" with customer_id "C001" and total_employee_count 500
        - sites: list of 10 Site instances (site_name "Site 1" through "Site 10", site_address "Address 1" through "Address 10", each with site_employee_count 50) linked to org
        - standard: Standard with code "ISO 9001:2015" and title "Quality Management"
        - cert: Certification linking org and standard with certification_scope "Manufacturing"
        """
        self.auditor = User.objects.create_user(username="auditor", password=TEST_PASSWORD)  # nosec B106
        self.cb_admin = User.objects.create_user(username="cbadmin", password=TEST_PASSWORD)  # nosec B106

        self.org = Organization.objects.create(
            name="Multi-Site Manufacturing Corp", customer_id="C001", total_employee_count=500
        )

        # Create 10 sites
        self.sites = []
        for i in range(10):
            site = Site.objects.create(
                organization=self.org,
                site_name=f"Site {i + 1}",
                site_address=f"Address {i + 1}",
                site_employee_count=50,
            )
            self.sites.append(site)

        self.standard = Standard.objects.create(code="ISO 9001:2015", title="Quality Management")

        self.cert = Certification.objects.create(
            organization=self.org, standard=self.standard, certification_scope="Manufacturing"
        )

    def test_complete_multi_site_audit_planning(self):
        """Test complete audit planning with sampling and duration validation."""
        # Step 1: Calculate required site sample
        sampling_result = calculate_sample_size(
            total_sites=10,
            high_risk_sites=2,
            is_initial_certification=True,
            scope_variation="moderate",
        )

        # √10 = 3.16 → 4 (base) + 1 (moderate variation) + 1 (2 high-risk sites) = 6
        self.assertEqual(sampling_result["minimum_sites"], 6)

        # Step 2: Validate duration for selected sites
        # 500 employees = 42 base hours (IAF MD5)
        # Complexity: 6 sites (+25%), moderate variation (+5%) = 1.30x factor
        # Required: 42 * 1.30 = 54.6 → 54.5 hours
        duration_result = validate_audit_duration(
            planned_hours=55.0,  # Meets IAF MD5 requirements with complexity factors
            employee_count=500,
            is_initial_certification=True,
            number_of_sites=6,  # Use actual sampled sites count
            scope_variation="moderate",
        )

        self.assertTrue(duration_result["is_valid"])

        # Step 3: Create audit with validated parameters
        audit = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=2),
            planned_duration_hours=duration_result["planned_hours"],
            created_by=self.cb_admin,
            lead_auditor=self.auditor,
        )

        # Add sampled sites to audit
        for i in range(sampling_result["minimum_sites"]):
            audit.sites.add(self.sites[i])

        self.assertEqual(audit.sites.count(), 6)
        self.assertEqual(audit.planned_duration_hours, 55.0)

    def test_root_cause_tracking_across_audits(self):
        """Test root cause categorization and recurrence tracking."""
        # Create root cause categories
        training_cat = RootCauseCategory.objects.create(
            name="Training Deficiency", code="RC-002", description="Inadequate training"
        )

        # Create first audit with NC
        audit1 = Audit.objects.create(
            organization=self.org,
            audit_type="stage2",
            total_audit_date_from=date.today() - timedelta(days=365),
            total_audit_date_to=date.today() - timedelta(days=364),
            planned_duration_hours=35.0,
            created_by=self.cb_admin,
            lead_auditor=self.auditor,
        )

        nc1 = Nonconformity.objects.create(
            audit=audit1,
            standard=self.standard,
            clause="7.2",
            category="minor",
            objective_evidence="Inadequate training records",
            statement_of_nc="Training requirements not met",
            auditor_explanation="Missing competence evidence",
            created_by=self.auditor,
        )
        nc1.root_cause_categories.add(training_cat)

        # Create second audit with recurring NC
        audit2 = Audit.objects.create(
            organization=self.org,
            audit_type="surveillance",
            total_audit_date_from=date.today(),
            total_audit_date_to=date.today() + timedelta(days=1),
            planned_duration_hours=23.0,
            created_by=self.cb_admin,
            lead_auditor=self.auditor,
        )

        nc2 = Nonconformity.objects.create(
            audit=audit2,
            standard=self.standard,
            clause="7.2",
            category="major",  # Escalated due to recurrence
            objective_evidence="Still no training records",
            statement_of_nc="Training requirements still not met",
            auditor_explanation="Recurring issue from previous audit",
            created_by=self.auditor,
        )
        nc2.root_cause_categories.add(training_cat)

        # Track recurrence
        recurrence = FindingRecurrence.objects.create(
            finding=nc2,
            recurrence_count=2,
            first_occurrence=audit1.total_audit_date_from,
            last_occurrence=audit2.total_audit_date_from,
            previous_audits=f"Audit {audit1.id}",
            corrective_actions_effective=False,
            escalation_required=True,
            resolution_notes="Escalated to major NC due to ineffective corrective action",
        )

        self.assertEqual(recurrence.recurrence_count, 2)
        self.assertTrue(recurrence.escalation_required)
        self.assertIn(training_cat, nc2.root_cause_categories.all())
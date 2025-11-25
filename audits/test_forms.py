"""
Tests for audits forms.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase

from audits.forms import (
    NonconformityForm,
    NonconformityResponseForm,
    NonconformityVerificationForm,
    ObservationForm,
    OpportunityForImprovementForm,
)
from audits.models import Audit, Nonconformity
from core.models import Certification, Organization, Standard


class AuditFormsTest(TestCase):
    """Test forms in audits app."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name="Test Org",
            registered_address="123 St",
            customer_id="ORG001",
            total_employee_count=10,
        )
        self.std1 = Standard.objects.create(code="ISO 9001", title="QMS")
        self.std2 = Standard.objects.create(code="ISO 14001", title="EMS")

        self.cert = Certification.objects.create(
            organization=self.org,
            standard=self.std1,
            certification_scope="Test scope",
            certificate_status="active",
        )

        self.cb_admin = User.objects.create_user(username="cbadmin", password="pass")
        self.lead_auditor = User.objects.create_user(username="lead", password="pass")

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
        self.audit.certifications.add(self.cert)

    def test_nonconformity_form_valid(self):
        """Test NonconformityForm with valid data."""
        form = NonconformityForm(
            data={
                "standard": self.std1.id,
                "clause": "4.1",
                "category": "minor",
                "objective_evidence": "Evidence",
                "statement_of_nc": "Statement",
                "auditor_explanation": "Explanation",
                "due_date": date.today(),
            },
            audit=self.audit,
        )
        self.assertTrue(form.is_valid())

    def test_nonconformity_form_invalid_standard(self):
        """Test NonconformityForm with standard not in audit."""
        form = NonconformityForm(
            data={
                "standard": self.std2.id,  # Not in audit
                "clause": "4.1",
                "category": "minor",
                "objective_evidence": "Evidence",
                "statement_of_nc": "Statement",
                "auditor_explanation": "Explanation",
                "due_date": date.today(),
            },
            audit=self.audit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("standard", form.errors)
        self.assertEqual(
            form.errors["standard"],
            ["Select a valid choice. That choice is not one of the available choices."],
        )

    def test_observation_form_valid(self):
        """Test ObservationForm with valid data."""
        form = ObservationForm(
            data={
                "standard": self.std1.id,
                "clause": "4.1",
                "statement": "Statement",
                "explanation": "Explanation",
            },
            audit=self.audit,
        )
        self.assertTrue(form.is_valid())

    def test_observation_form_invalid_standard(self):
        """Test ObservationForm with invalid standard."""
        form = ObservationForm(
            data={
                "standard": self.std2.id,
                "clause": "4.1",
                "statement": "Statement",
                "explanation": "Explanation",
            },
            audit=self.audit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("standard", form.errors)
        self.assertEqual(
            form.errors["standard"],
            ["Select a valid choice. That choice is not one of the available choices."],
        )

    def test_ofi_form_valid(self):
        """Test OpportunityForImprovementForm with valid data."""
        form = OpportunityForImprovementForm(
            data={
                "standard": self.std1.id,
                "clause": "4.1",
                "description": "Description",
            },
            audit=self.audit,
        )
        self.assertTrue(form.is_valid())

    def test_ofi_form_invalid_standard(self):
        """Test OpportunityForImprovementForm with invalid standard."""
        form = OpportunityForImprovementForm(
            data={
                "standard": self.std2.id,
                "clause": "4.1",
                "description": "Description",
            },
            audit=self.audit,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("standard", form.errors)
        self.assertEqual(
            form.errors["standard"],
            ["Select a valid choice. That choice is not one of the available choices."],
        )

    def test_nc_response_form_valid(self):
        """Test NonconformityResponseForm with valid data."""
        form = NonconformityResponseForm(
            data={
                "client_root_cause": "Root cause",
                "client_correction": "Correction",
                "client_corrective_action": "Action",
                "due_date": date.today(),
            }
        )
        self.assertTrue(form.is_valid())

    def test_nc_response_form_missing_fields(self):
        """Test NonconformityResponseForm with missing fields."""
        form = NonconformityResponseForm(
            data={
                "client_root_cause": "",
                "client_correction": "",
                "client_corrective_action": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("client_root_cause", form.errors)
        self.assertIn("client_correction", form.errors)
        self.assertIn("client_corrective_action", form.errors)

    def test_nc_verification_form_valid(self):
        """Test NonconformityVerificationForm with valid data."""
        form = NonconformityVerificationForm(
            data={
                "verification_action": "accept",
                "verification_notes": "Notes",
            }
        )
        self.assertTrue(form.is_valid())

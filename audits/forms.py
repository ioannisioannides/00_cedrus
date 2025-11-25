"""
Forms for audit findings: Nonconformity, Observation, OpportunityForImprovement.

These forms handle creation and editing of findings, with validation to ensure
standards belong to the audit's certifications.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Nonconformity, Observation, OpportunityForImprovement


class NonconformityForm(forms.ModelForm):
    """Form for creating/editing nonconformities."""

    class Meta:
        model = Nonconformity
        fields = [
            "standard",
            "clause",
            "category",
            "objective_evidence",
            "statement_of_nc",
            "auditor_explanation",
            "due_date",
        ]
        widgets = {
            "standard": forms.Select(attrs={"class": "form-select"}),
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "objective_evidence": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "statement_of_nc": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "auditor_explanation": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Filter standards to only those covered by the audit
        if audit:
            # Get standards from audit's certifications
            standards = audit.certifications.values_list("standard", flat=True).distinct()
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.filter(id__in=standards)
            self.fields["standard"].required = True
        else:
            # If no audit provided, allow all standards (shouldn't happen in practice)
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        standard = cleaned_data.get("standard")

        # Validate that standard is from audit's certifications
        if self.audit and standard:
            audit_standards = self.audit.certifications.values_list("standard", flat=True).distinct()
            if standard.id not in audit_standards:
                raise ValidationError("The selected standard must be one of the standards covered by this audit.")

        return cleaned_data


class ObservationForm(forms.ModelForm):
    """Form for creating/editing observations."""

    class Meta:
        model = Observation
        fields = ["standard", "clause", "statement", "explanation"]
        widgets = {
            "standard": forms.Select(attrs={"class": "form-select"}),
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "statement": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "explanation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Filter standards to only those covered by the audit
        if audit:
            standards = audit.certifications.values_list("standard", flat=True).distinct()
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.filter(id__in=standards)
            self.fields["standard"].required = True
        else:
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        standard = cleaned_data.get("standard")

        if self.audit and standard:
            audit_standards = self.audit.certifications.values_list("standard", flat=True).distinct()
            if standard.id not in audit_standards:
                raise ValidationError("The selected standard must be one of the standards covered by this audit.")

        return cleaned_data


class OpportunityForImprovementForm(forms.ModelForm):
    """Form for creating/editing opportunities for improvement."""

    class Meta:
        model = OpportunityForImprovement
        fields = ["standard", "clause", "description"]
        widgets = {
            "standard": forms.Select(attrs={"class": "form-select"}),
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Filter standards to only those covered by the audit
        if audit:
            standards = audit.certifications.values_list("standard", flat=True).distinct()
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.filter(id__in=standards)
            self.fields["standard"].required = True
        else:
            from core.models import Standard

            self.fields["standard"].queryset = Standard.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        standard = cleaned_data.get("standard")

        if self.audit and standard:
            audit_standards = self.audit.certifications.values_list("standard", flat=True).distinct()
            if standard.id not in audit_standards:
                raise ValidationError("The selected standard must be one of the standards covered by this audit.")

        return cleaned_data


class NonconformityResponseForm(forms.ModelForm):
    """Form for clients to respond to nonconformities."""

    class Meta:
        model = Nonconformity
        fields = ["client_root_cause", "client_correction", "client_corrective_action", "due_date"]
        widgets = {
            "client_root_cause": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "client_correction": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "client_corrective_action": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        root_cause = cleaned_data.get("client_root_cause", "").strip()
        correction = cleaned_data.get("client_correction", "").strip()
        corrective_action = cleaned_data.get("client_corrective_action", "").strip()

        # All three fields are required for a complete response
        if not root_cause:
            raise ValidationError({"client_root_cause": "Root cause analysis is required."})
        if not correction:
            raise ValidationError({"client_correction": "Immediate correction is required."})
        if not corrective_action:
            raise ValidationError({"client_corrective_action": "Corrective action plan is required."})

        return cleaned_data


class NonconformityVerificationForm(forms.ModelForm):
    """Form for auditors to verify nonconformity responses."""

    verification_action: forms.ChoiceField = forms.ChoiceField(
        choices=[
            ("accept", "Accept Response"),
            ("request_changes", "Request Changes"),
            ("close", "Close Nonconformity"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        required=True,
        help_text="Choose the verification action",
    )

    verification_notes: forms.CharField = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=False,
        help_text="Optional notes about the verification",
    )

    class Meta:
        model = Nonconformity
        fields = []  # We handle status update in the view

    def clean(self):
        cleaned_data = super().clean()
        # No additional validation needed - auditors can accept or close directly
        return cleaned_data

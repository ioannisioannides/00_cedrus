"""
Forms for managing audit findings (Nonconformities, Observations, OFIs).

These forms handle creation and editing of findings with appropriate
validation and field requirements for each finding type.
"""

from django import forms
from django.core.exceptions import ValidationError

from audit_management.models import Nonconformity, Observation, OpportunityForImprovement
from core.models import Site


class NonconformityForm(forms.ModelForm):
    """
    Form for creating/editing nonconformities.

    Includes validation for required fields and category-specific rules.
    """

    class Meta:
        model = Nonconformity
        fields = [
            "standard",
            "clause",
            "site",
            "category",
            "objective_evidence",
            "statement_of_nc",
            "auditor_explanation",
        ]
        widgets = {
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "objective_evidence": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the evidence that supports this nonconformity...",
                }
            ),
            "statement_of_nc": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Clear statement of the nonconformity...",
                }
            ),
            "auditor_explanation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Detailed explanation of why this is a nonconformity...",
                }
            ),
            "standard": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "clause": "Standard clause reference (e.g., 4.1, 7.5.1)",
            "category": "Major: affects ability to meet requirements. Minor: isolated incident.",
            "objective_evidence": "Factual information that supports the nonconformity",
            "statement_of_nc": "Clear statement of what requirement was not met",
            "auditor_explanation": "Why this constitutes a nonconformity",
            "site": "Select the specific site where this finding was observed (for multi-site audits)",
        }

    def __init__(self, *args, audit=None, **kwargs):
        """
        Initialize form with audit context.

        Args:
            audit: The audit this nonconformity belongs to
        """
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Set audit on instance for validation (needed for model.clean())
        if audit and not self.instance.pk:  # Only for create forms
            self.instance.audit = audit

        # Filter sites to only those belonging to the audit's organization
        if audit:
            self.fields["site"].queryset = Site.objects.filter(organization=audit.organization)
            # Filter to sites assigned to this audit if any
            if audit.sites.exists():
                self.fields["site"].queryset = audit.sites.all()
            self.fields["site"].required = False

        # Make fields required
        self.fields["clause"].required = True
        self.fields["category"].required = True
        self.fields["objective_evidence"].required = True
        self.fields["statement_of_nc"].required = True
        self.fields["auditor_explanation"].required = True

    def clean_clause(self):
        """Validate clause format."""
        clause = self.cleaned_data.get("clause", "").strip()
        if not clause:
            raise ValidationError("Clause reference is required.")
        return clause

    def clean(self):
        """Additional validation."""
        cleaned_data = super().clean()

        # Validate that all required text fields have content
        required_fields = ["objective_evidence", "statement_of_nc", "auditor_explanation"]
        for field in required_fields:
            value = cleaned_data.get(field, "").strip()
            if not value:
                self.add_error(field, f"{field.replace('_', ' ').title()} cannot be empty.")

        return cleaned_data

    def save(self, commit=True):
        """Save the nonconformity with audit and creator."""
        nc = super().save(commit=False)
        if self.audit:
            nc.audit = self.audit
        if commit:
            nc.save()
            self.save_m2m()
        return nc


class NonconformityResponseForm(forms.ModelForm):
    """
    Form for client response to nonconformity.

    Used by clients to provide root cause analysis, correction,
    and corrective action plan.
    """

    class Meta:
        model = Nonconformity
        fields = ["client_root_cause", "client_correction", "client_corrective_action", "due_date"]
        widgets = {
            "client_root_cause": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Analyze the root cause of this nonconformity...",
                }
            ),
            "client_correction": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the immediate correction taken...",
                }
            ),
            "client_corrective_action": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the corrective action to prevent recurrence...",
                }
            ),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
        help_texts = {
            "client_root_cause": "Identify the underlying cause of the nonconformity",
            "client_correction": "What was done immediately to address the issue?",
            "client_corrective_action": "What will be done to prevent it from happening again?",
            "due_date": "Target date for completion of corrective action",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required for response
        for field in self.fields:
            self.fields[field].required = True

    def clean(self):
        """Validate that all response fields have content."""
        cleaned_data = super().clean()

        # Validate that text fields are not just whitespace
        text_fields = ["client_root_cause", "client_correction", "client_corrective_action"]
        for field in text_fields:
            value = cleaned_data.get(field, "").strip()
            if not value:
                self.add_error(field, f"{field.replace('_', ' ').title()} cannot be empty.")

        return cleaned_data


class NonconformityVerificationForm(forms.ModelForm):
    """
    Form for auditor verification of client response.

    Used by auditors to accept or reject the client's response
    with verification notes.
    """

    verification_action = forms.ChoiceField(
        choices=[
            ("accept", "Accept Response"),
            ("request_changes", "Request Changes"),
            ("close", "Close Nonconformity"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Select the action to take on this nonconformity response.",
    )

    class Meta:
        model = Nonconformity
        fields = ["verification_notes"]
        widgets = {
            "verification_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Provide notes on the verification of the client response...",
                }
            ),
        }
        help_texts = {
            "verification_notes": "Document your assessment of the client response",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["verification_notes"].required = True


class ObservationForm(forms.ModelForm):
    """
    Form for creating/editing observations.

    Observations are informational findings that don't require
    formal client response.
    """

    class Meta:
        model = Observation
        fields = ["standard", "clause", "site", "statement", "explanation"]
        widgets = {
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "statement": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Observation statement...",
                }
            ),
            "explanation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional explanation (optional)...",
                }
            ),
            "standard": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "clause": "Standard clause reference",
            "statement": "Clear statement of the observation",
            "explanation": "Additional context or explanation",
            "site": "Select the specific site where this observation was made",
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Set audit on instance for validation (needed for model.clean())
        if audit and not self.instance.pk:  # Only for create forms
            self.instance.audit = audit

        # Filter sites to only those in the audit
        if audit:
            self.fields["site"].queryset = Site.objects.filter(organization=audit.organization)
            if audit.sites.exists():
                self.fields["site"].queryset = audit.sites.all()
            self.fields["site"].required = False

        # Make core fields required
        self.fields["clause"].required = True
        self.fields["statement"].required = True
        self.fields["explanation"].required = False

    def save(self, commit=True):
        """Save the observation with audit and creator."""
        obs = super().save(commit=False)
        if self.audit:
            obs.audit = self.audit
        if commit:
            obs.save()
            self.save_m2m()
        return obs


class OpportunityForImprovementForm(forms.ModelForm):
    """
    Form for creating/editing opportunities for improvement.

    OFIs are suggestions for enhancement that don't require
    formal response.
    """

    class Meta:
        model = OpportunityForImprovement
        fields = ["standard", "clause", "site", "description"]
        widgets = {
            "clause": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 4.1, 7.5.1"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Describe the opportunity for improvement...",
                }
            ),
            "standard": forms.Select(attrs={"class": "form-select"}),
            "site": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "clause": "Standard clause reference",
            "description": "Description of the improvement opportunity",
            "site": "Select the specific site where this opportunity applies",
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Set audit on instance for validation (needed for model.clean())
        if audit and not self.instance.pk:  # Only for create forms
            self.instance.audit = audit

        # Filter sites to only those in the audit
        if audit:
            self.fields["site"].queryset = Site.objects.filter(organization=audit.organization)
            if audit.sites.exists():
                self.fields["site"].queryset = audit.sites.all()
            self.fields["site"].required = False

        # Make core fields required
        self.fields["clause"].required = True
        self.fields["description"].required = True

    def save(self, commit=True):
        """Save the OFI with audit and creator."""
        ofi = super().save(commit=False)
        if self.audit:
            ofi.audit = self.audit
        if commit:
            ofi.save()
            self.save_m2m()
        return ofi

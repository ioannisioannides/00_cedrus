"""
Forms for audit team member management.
Sprint 8: US-010 - Assign Team Members to Audit
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from audits.models import Audit, AuditorCompetenceWarning, AuditTeamMember
from trunk.services.competence_service import CompetenceService


class AuditTeamMemberForm(forms.ModelForm):
    """
    Form for adding/editing audit team members.

    Supports both internal auditors (user selected) and external experts (name only).
    Auto-fills name from user when user is selected.
    Validates date ranges within audit dates.
    """

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(
            groups__name__in=["lead_auditor", "auditor", "technical_expert", "cb_admin"]
        ).distinct(),
        required=False,
        empty_label="--- External Expert (No User Account) ---",
        help_text="Select a user for internal team members, or leave blank for external experts",
    )

    name = forms.CharField(
        max_length=255,
        required=False,
        help_text="Auto-filled from user if selected, or enter manually for external experts",
        widget=forms.TextInput(
            attrs={"placeholder": "Will auto-fill from user selection", "class": "form-control"}
        ),
    )

    title = forms.CharField(
        max_length=255,
        required=False,
        help_text="Job title or professional designation",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g., Senior Auditor, Technical Expert - Environmental",
                "class": "form-control",
            }
        ),
    )

    role = forms.ChoiceField(
        choices=AuditTeamMember.ROLE_CHOICES,
        help_text="Role in this audit",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    date_from = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        help_text="Team member participation start date (must be within audit dates)",
    )

    date_to = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        help_text="Team member participation end date (must be within audit dates)",
    )

    class Meta:
        model = AuditTeamMember
        fields = ["user", "name", "title", "role", "date_from", "date_to"]

    def __init__(self, *args, **kwargs):
        self.audit = kwargs.pop("audit", None)
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # If editing existing member, populate name from instance
        if self.instance and self.instance.pk:
            self.initial["name"] = self.instance.name
            if self.instance.user:
                self.initial["user"] = self.instance.user

        # Set date field initial values based on audit dates
        if self.audit and not self.instance.pk:
            self.fields["date_from"].initial = self.audit.total_audit_date_from
            self.fields["date_to"].initial = self.audit.total_audit_date_to

    def clean_name(self):
        """
        Ensure name is provided.
        If user is selected, auto-fill from user.
        If user is not selected (external expert), name is required.
        """
        user = self.cleaned_data.get("user")
        name = self.cleaned_data.get("name")

        if user:
            # Auto-fill from user
            return user.get_full_name() or user.username
        elif not name:
            raise ValidationError(
                "Name is required for external experts (when no user is selected)."
            )

        return name

    def clean(self):
        """
        Validate the entire form.
        - Ensure dates are within audit date range
        - Ensure date_to >= date_from
        - Call model's clean() method for additional validation
        """
        cleaned_data = super().clean()

        if not self.audit:
            raise ValidationError("Audit is required")

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        # Basic date validation
        if date_from and date_to:
            if date_to < date_from:
                raise ValidationError({"date_to": "End date must be on or after start date."})

        # Validate against audit dates
        if date_from and self.audit.total_audit_date_from:
            if date_from < self.audit.total_audit_date_from:
                raise ValidationError(
                    {
                        "date_from": f"Team member start date cannot be before audit start date ({self.audit.total_audit_date_from})."
                    }
                )

        if date_to and self.audit.total_audit_date_to:
            if date_to > self.audit.total_audit_date_to:
                raise ValidationError(
                    {
                        "date_to": f"Team member end date cannot be after audit end date ({self.audit.total_audit_date_to})."
                    }
                )

        # Competence Validation (Sprint 8 / Phase 2A)
        user = cleaned_data.get("user")
        if user and self.audit and self.request_user:
            try:
                CompetenceService.ensure_auditor_has_active_qualification(user, self.audit)
                CompetenceService.check_recent_competence_evaluation(user)
            except ValidationError as e:
                # Create warning record instead of blocking assignment
                # This allows the assignment but flags it for review
                AuditorCompetenceWarning.objects.create(
                    audit=self.audit,
                    auditor=user,
                    warning_type="scope_mismatch", # Defaulting to scope mismatch or we could parse exception
                    description=str(e.message) if hasattr(e, 'message') else str(e),
                    issued_by=self.request_user
                )

        return cleaned_data

    def _post_clean(self):
        """Override to set audit before model validation."""
        # Ensure audit is set on the instance before Django calls model.full_clean()
        if self.audit:
            self.instance.audit = self.audit
        super()._post_clean()

    def save(self, commit=True):
        """Save the team member, ensuring audit is set."""
        instance = super().save(commit=False)
        instance.audit = self.audit

        # Ensure name is set (from user or manual entry)
        if instance.user and not instance.name:
            instance.name = instance.user.get_full_name() or instance.user.username

        if commit:
            instance.save()
        return instance

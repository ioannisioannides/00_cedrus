"""
Forms for audit documentation sections: Organization Changes, Audit Plan Review, Audit Summary.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import AuditChanges, AuditPlanReview, AuditSummary


class AuditChangesForm(forms.ModelForm):
    """Form for tracking organization changes during audit."""

    class Meta:
        model = AuditChanges
        fields = [
            "change_of_name",
            "change_of_scope",
            "change_of_sites",
            "change_of_ms_rep",
            "change_of_signatory",
            "change_of_employee_count",
            "change_of_contact_info",
            "other_has_change",
            "other_description",
        ]
        widgets = {
            "change_of_name": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_scope": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_sites": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_ms_rep": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_signatory": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_employee_count": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "change_of_contact_info": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "other_has_change": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "other_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        other_has_change = cleaned_data.get("other_has_change", False)
        other_description = cleaned_data.get("other_description", "").strip()

        if other_has_change and not other_description:
            raise ValidationError({"other_description": 'Description is required when "Other changes" is selected.'})

        return cleaned_data


class AuditPlanReviewForm(forms.ModelForm):
    """Form for audit plan review and deviations."""

    class Meta:
        model = AuditPlanReview
        fields = [
            "deviations_yes_no",
            "deviations_details",
            "issues_affecting_yes_no",
            "issues_affecting_details",
            "next_audit_date_from",
            "next_audit_date_to",
        ]
        widgets = {
            "deviations_yes_no": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "deviations_details": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "issues_affecting_yes_no": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "issues_affecting_details": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "next_audit_date_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "next_audit_date_to": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        deviations_yes_no = cleaned_data.get("deviations_yes_no", False)
        deviations_details = cleaned_data.get("deviations_details", "").strip()
        issues_affecting_yes_no = cleaned_data.get("issues_affecting_yes_no", False)
        issues_affecting_details = cleaned_data.get("issues_affecting_details", "").strip()
        next_audit_date_from = cleaned_data.get("next_audit_date_from")
        next_audit_date_to = cleaned_data.get("next_audit_date_to")

        if deviations_yes_no and not deviations_details:
            raise ValidationError({"deviations_details": "Details are required when deviations occurred."})

        if issues_affecting_yes_no and not issues_affecting_details:
            raise ValidationError({"issues_affecting_details": "Details are required when issues affected the audit."})

        if next_audit_date_from and next_audit_date_to:
            if next_audit_date_to < next_audit_date_from:
                raise ValidationError({"next_audit_date_to": "End date must be after start date."})

        return cleaned_data


class AuditSummaryForm(forms.ModelForm):
    """Form for audit summary and evaluation."""

    class Meta:
        model = AuditSummary
        fields = [
            "objectives_met",
            "objectives_comments",
            "scope_appropriate",
            "scope_comments",
            "ms_meets_requirements",
            "ms_comments",
            "management_review_effective",
            "management_review_comments",
            "internal_audit_effective",
            "internal_audit_comments",
            "ms_effective",
            "ms_effective_comments",
            "correct_use_of_logos",
            "logos_comments",
            "promoted_to_committee",
            "committee_comments",
            "general_commentary",
        ]
        widgets = {
            "objectives_met": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "objectives_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "scope_appropriate": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "scope_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "ms_meets_requirements": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ms_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "management_review_effective": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "management_review_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "internal_audit_effective": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "internal_audit_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "ms_effective": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ms_effective_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "correct_use_of_logos": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "logos_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "promoted_to_committee": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "committee_comments": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "general_commentary": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

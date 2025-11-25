"""
Forms for audit recommendations and certification decisions.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import AuditRecommendation


class AuditRecommendationForm(forms.ModelForm):
    """Form for creating/editing audit recommendations."""

    class Meta:
        model = AuditRecommendation
        fields = [
            "special_audit_required",
            "special_audit_details",
            "suspension_recommended",
            "suspension_certificates",
            "revocation_recommended",
            "revocation_certificates",
            "stage2_required",
            "decision_notes",
        ]
        widgets = {
            "special_audit_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "special_audit_details": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "suspension_recommended": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "suspension_certificates": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "revocation_recommended": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "revocation_certificates": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "stage2_required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "decision_notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        special_audit_required = cleaned_data.get("special_audit_required", False)
        special_audit_details = cleaned_data.get("special_audit_details", "").strip()
        suspension_recommended = cleaned_data.get("suspension_recommended", False)
        suspension_certificates = cleaned_data.get("suspension_certificates", "").strip()
        revocation_recommended = cleaned_data.get("revocation_recommended", False)
        revocation_certificates = cleaned_data.get("revocation_certificates", "").strip()

        if special_audit_required and not special_audit_details:
            raise ValidationError({"special_audit_details": "Details are required when special audit is recommended."})

        if suspension_recommended and not suspension_certificates:
            raise ValidationError(
                {"suspension_certificates": "Certificate list is required when suspension is recommended."}
            )

        if revocation_recommended and not revocation_certificates:
            raise ValidationError(
                {"revocation_certificates": "Certificate list is required when revocation is recommended."}
            )

        return cleaned_data

"""
Forms for Complaints and Appeals (Phase 2A).
"""

from django import forms

from certification.models import Appeal, Complaint


class ComplaintForm(forms.ModelForm):
    """Form for submitting a complaint."""

    class Meta:
        model = Complaint
        fields = [
            "complainant_name",
            "complainant_email",
            "organization",
            "complaint_type",
            "description",
            "related_audit",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class AppealForm(forms.ModelForm):
    """Form for submitting an appeal."""

    class Meta:
        model = Appeal
        fields = [
            "appellant_name",
            "appellant_email",
            "related_complaint",
            "related_decision",
            "grounds",
        ]
        widgets = {
            "grounds": forms.Textarea(attrs={"rows": 5}),
        }

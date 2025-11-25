"""
Forms for Audit Program management.
"""

from django import forms
from django.utils import timezone

from audits.models import AuditProgram


class AuditProgramForm(forms.ModelForm):
    """Form for creating and updating Audit Programs."""

    class Meta:
        model = AuditProgram
        fields = ["title", "year", "status", "objectives", "risks_opportunities"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 2025 Internal Audit Program"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "min": 2000, "max": 2100}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "objectives": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Define the objectives of this audit program..."}),
            "risks_opportunities": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Identify risks and opportunities..."}),
        }
        help_texts = {
            "objectives": "What do you want to achieve with this program? (ISO 19011 5.2)",
            "risks_opportunities": "What risks and opportunities affect this program? (ISO 19011 5.3)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial["year"] = timezone.now().year

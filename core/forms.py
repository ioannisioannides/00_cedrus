from django import forms

from .models import CertificateHistory, SurveillanceSchedule


class SurveillanceScheduleForm(forms.ModelForm):
    class Meta:
        model = SurveillanceSchedule
        fields = [
            "surveillance_1_due_date",
            "surveillance_2_due_date",
            "recertification_due_date",
            "surveillance_1_completed",
            "surveillance_2_completed",
            "recertification_completed",
        ]
        widgets = {
            "surveillance_1_due_date": forms.DateInput(attrs={"type": "date"}),
            "surveillance_2_due_date": forms.DateInput(attrs={"type": "date"}),
            "recertification_due_date": forms.DateInput(attrs={"type": "date"}),
        }


class CertificateHistoryForm(forms.ModelForm):
    class Meta:
        model = CertificateHistory
        fields = [
            "certification",
            "action",
            "action_date",
            "action_reason",
            "internal_notes",
        ]
        widgets = {
            "action_date": forms.DateInput(attrs={"type": "date"}),
            "action_reason": forms.Textarea(attrs={"rows": 3}),
            "internal_notes": forms.Textarea(attrs={"rows": 3}),
        }

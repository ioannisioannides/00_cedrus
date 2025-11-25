from django import forms
from django.contrib.auth.models import User

from .models import (
    AuditorCompetenceEvaluation,
    AuditorQualification,
    AuditorTrainingRecord,
    ConflictOfInterest,
    ImpartialityDeclaration,
)


class AuditorQualificationForm(forms.ModelForm):
    class Meta:
        model = AuditorQualification
        fields = [
            "auditor",
            "qualification_type",
            "issuing_body",
            "certificate_number",
            "issue_date",
            "expiry_date",
            "standards",
            "nace_codes",
            "ea_codes",
            "certificate_file",
            "status",
            "notes",
        ]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
            "standards": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter auditors only for the auditor field
        self.fields["auditor"].queryset = User.objects.filter(groups__name__in=["auditor", "lead_auditor"]).distinct()


class AuditorTrainingRecordForm(forms.ModelForm):
    class Meta:
        model = AuditorTrainingRecord
        fields = [
            "auditor",
            "course_title",
            "training_provider",
            "course_date",
            "duration_hours",
            "standards_covered",
            "cpd_points",
            "certificate_file",
            "notes",
        ]
        widgets = {
            "course_date": forms.DateInput(attrs={"type": "date"}),
            "standards_covered": forms.CheckboxSelectMultiple(),
        }


class AuditorCompetenceEvaluationForm(forms.ModelForm):
    class Meta:
        model = AuditorCompetenceEvaluation
        fields = [
            "auditor",
            "evaluation_date",
            "evaluator",
            "technical_knowledge_score",
            "audit_skills_score",
            "communication_skills_score",
            "report_writing_score",
            "witness_audit_date",
            "witness_audit_observer",
            "witness_audit_notes",
            "overall_assessment",
            "development_plan",
        ]
        widgets = {
            "evaluation_date": forms.DateInput(attrs={"type": "date"}),
            "witness_audit_date": forms.DateInput(attrs={"type": "date"}),
            "development_plan": forms.Textarea(attrs={"rows": 4}),
        }


class ConflictOfInterestForm(forms.ModelForm):
    class Meta:
        model = ConflictOfInterest
        fields = [
            "auditor",
            "organization",
            "relationship_type",
            "description",
            "relationship_start_date",
            "relationship_end_date",
            "impartiality_risk",
            "mitigation_measures",
            "is_active",
        ]
        widgets = {
            "relationship_start_date": forms.DateInput(attrs={"type": "date"}),
            "relationship_end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "mitigation_measures": forms.Textarea(attrs={"rows": 3}),
        }


class ImpartialityDeclarationForm(forms.ModelForm):
    class Meta:
        model = ImpartialityDeclaration
        fields = [
            "declaration_period_year",
            "no_conflicts_declared",
            "conflicts_detailed",
        ]
        widgets = {
            "conflicts_detailed": forms.Textarea(attrs={"rows": 4}),
        }

"""
Forms for evidence file management.
"""

from django import forms

from .models import EvidenceFile


class EvidenceFileForm(forms.ModelForm):
    """Form for uploading evidence files."""

    class Meta:
        model = EvidenceFile
        fields = ["file", "finding"]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png",
                }
            ),
            "finding": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, audit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit = audit

        # Filter findings to only nonconformities from this audit
        if audit:
            self.fields["finding"].queryset = audit.nonconformity_set.all()
            self.fields["finding"].required = False
            self.fields["finding"].empty_label = (
                "General audit evidence (not linked to specific NC)"
            )
        else:
            from .models import Nonconformity

            self.fields["finding"].queryset = Nonconformity.objects.none()

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 10MB.")

            # Check file extension
            allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png"]
            file_ext = file.name.lower().split(".")[-1] if "." in file.name else ""
            if file_ext not in [ext.lstrip(".") for ext in allowed_extensions]:
                raise forms.ValidationError(
                    f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                )

        return file

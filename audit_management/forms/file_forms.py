"""
Forms for evidence file management.
"""

import os

from django import forms
from django.conf import settings

from audit_management.models import EvidenceFile


class EvidenceFileForm(forms.ModelForm):
    """Form for uploading evidence files."""

    class Meta:
        model = EvidenceFile
        fields = ["file", "finding"]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ",".join(settings.EVIDENCE_ALLOWED_EXTENSIONS),
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
            self.fields["finding"].empty_label = "General audit evidence (not linked to specific NC)"
        else:
            from audit_management.models import Nonconformity

            self.fields["finding"].queryset = Nonconformity.objects.none()

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Check file size
            max_size = settings.EVIDENCE_MAX_FILE_SIZE
            if file.size > max_size:
                max_mb = max_size / (1024 * 1024)
                raise forms.ValidationError(f"File size cannot exceed {max_mb:.0f}MB.")

            # Check file extension
            allowed_extensions = settings.EVIDENCE_ALLOWED_EXTENSIONS
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in allowed_extensions:
                raise forms.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

        return file

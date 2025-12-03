"""
Service for managing evidence files.
"""

from audit_management.models import EvidenceFile
from trunk.events import EventType, event_dispatcher


class EvidenceService:
    """Business logic for evidence file management."""

    @staticmethod
    def upload_evidence(audit, user, file_data, finding=None):
        """
        Upload an evidence file.

        Args:
            audit: The audit instance.
            user: The user uploading the file.
            file_data: Dictionary containing file and metadata (file, evidence_type, description).
            finding: Optional finding to link evidence to.

        Returns:
            EvidenceFile: The created evidence file.
        """
        # Handle finding being in file_data (e.g. from form.cleaned_data)
        if "finding" in file_data:
            finding_from_data = file_data.pop("finding")
            if finding is None:
                finding = finding_from_data

        evidence = EvidenceFile(audit=audit, uploaded_by=user, finding=finding, **file_data)
        evidence.full_clean()  # Validates file size/type via model clean()
        evidence.save()

        # Emit event
        event_dispatcher.emit(EventType.EVIDENCE_UPLOADED, {"audit": audit, "evidence": evidence, "uploaded_by": user})

        return evidence

    @staticmethod
    def delete_evidence(evidence_file, user):
        """
        Delete an evidence file.

        Args:
            evidence_file: The EvidenceFile instance.
            user: The user deleting the file.
        """
        audit = evidence_file.audit
        filename = evidence_file.file.name

        # Delete physical file and record
        evidence_file.file.delete()
        evidence_file.delete()

        # Emit event
        event_dispatcher.emit(EventType.EVIDENCE_DELETED, {"audit": audit, "filename": filename, "deleted_by": user})

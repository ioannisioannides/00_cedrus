from unittest.mock import Mock, patch

from trunk.events import EventType
from trunk.services.evidence_service import EvidenceService


class TestEvidenceService:
    @patch("trunk.services.evidence_service.EvidenceFile")
    @patch("trunk.services.evidence_service.event_dispatcher")
    def test_upload_evidence(self, mock_dispatcher, mock_evidence_class):
        # Setup
        mock_audit = Mock()
        mock_user = Mock()
        mock_finding = Mock()
        file_data = {"file": Mock(), "evidence_type": "document", "description": "Test evidence"}

        mock_evidence_instance = Mock()
        mock_evidence_class.return_value = mock_evidence_instance

        # Execute
        result = EvidenceService.upload_evidence(mock_audit, mock_user, file_data, finding=mock_finding)

        # Verify
        mock_evidence_class.assert_called_once_with(
            audit=mock_audit,
            uploaded_by=mock_user,
            finding=mock_finding,
            file=file_data["file"],
            evidence_type="document",
            description="Test evidence",
        )
        mock_evidence_instance.full_clean.assert_called_once()
        mock_evidence_instance.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.EVIDENCE_UPLOADED,
            {"audit": mock_audit, "evidence": mock_evidence_instance, "uploaded_by": mock_user},
        )
        assert result == mock_evidence_instance

    @patch("trunk.services.evidence_service.EvidenceFile")
    @patch("trunk.services.evidence_service.event_dispatcher")
    def test_upload_evidence_with_finding_in_data(self, mock_dispatcher, mock_evidence_class):
        # Setup
        mock_audit = Mock()
        mock_user = Mock()
        mock_finding = Mock()
        file_data = {
            "file": Mock(),
            "evidence_type": "document",
            "description": "Test evidence",
            "finding": mock_finding,
        }

        mock_evidence_instance = Mock()
        mock_evidence_class.return_value = mock_evidence_instance

        # Execute
        result = EvidenceService.upload_evidence(mock_audit, mock_user, file_data)

        # Verify
        # finding should be extracted from file_data and passed as kwarg
        mock_evidence_class.assert_called_once_with(
            audit=mock_audit,
            uploaded_by=mock_user,
            finding=mock_finding,
            file=file_data["file"],
            evidence_type="document",
            description="Test evidence",
        )
        assert result == mock_evidence_instance

    @patch("trunk.services.evidence_service.event_dispatcher")
    def test_delete_evidence(self, mock_dispatcher):
        # Setup
        mock_evidence = Mock()
        mock_evidence.file.name = "test_file.pdf"
        mock_user = Mock()
        mock_audit = Mock()
        mock_evidence.audit = mock_audit

        # Execute
        EvidenceService.delete_evidence(mock_evidence, mock_user)

        # Verify
        mock_evidence.file.delete.assert_called_once()
        mock_evidence.delete.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.EVIDENCE_DELETED, {"audit": mock_audit, "filename": "test_file.pdf", "deleted_by": mock_user}
        )

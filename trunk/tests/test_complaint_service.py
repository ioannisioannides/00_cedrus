from unittest.mock import Mock, patch

from trunk.events import EventType
from trunk.services.complaint_service import ComplaintService


class TestComplaintService:
    @patch("trunk.services.complaint_service.Complaint")
    @patch("trunk.services.complaint_service.event_dispatcher")
    def test_create_complaint(self, mock_dispatcher, mock_complaint_model):
        mock_user = Mock(id=1)
        data = {"description": "Test complaint"}
        mock_complaint = Mock(id=10)
        mock_complaint_model.objects.create.return_value = mock_complaint

        result = ComplaintService.create_complaint(data, mock_user)

        mock_complaint_model.objects.create.assert_called_once()
        call_kwargs = mock_complaint_model.objects.create.call_args[1]
        assert call_kwargs["submitted_by"] == mock_user
        assert call_kwargs["description"] == "Test complaint"
        assert call_kwargs["complaint_number"].startswith("COMP-")

        mock_dispatcher.emit.assert_called_once_with(
            EventType.COMPLAINT_RECEIVED, {"complaint_id": 10, "created_by_id": 1}
        )
        assert result == mock_complaint

    @patch("trunk.services.complaint_service.event_dispatcher")
    def test_update_complaint_status(self, mock_dispatcher):
        mock_user = Mock(id=1)
        mock_complaint = Mock(id=10, status="open")

        result = ComplaintService.update_complaint_status(mock_complaint, "resolved", mock_user, notes="Fixed")

        assert mock_complaint.status == "resolved"
        assert mock_complaint.resolution_notes == "Fixed"
        mock_complaint.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.COMPLAINT_STATUS_CHANGED,
            {
                "complaint_id": 10,
                "old_status": "open",
                "new_status": "resolved",
                "changed_by_id": 1,
            },
        )
        assert result == mock_complaint

    @patch("trunk.services.complaint_service.Appeal")
    @patch("trunk.services.complaint_service.event_dispatcher")
    def test_create_appeal(self, mock_dispatcher, mock_appeal_model):
        mock_user = Mock(id=1)
        data = {"description": "Test appeal"}
        mock_appeal = Mock(id=20)
        mock_appeal_model.objects.create.return_value = mock_appeal

        result = ComplaintService.create_appeal(data, mock_user)

        mock_appeal_model.objects.create.assert_called_once()
        call_kwargs = mock_appeal_model.objects.create.call_args[1]
        assert call_kwargs["submitted_by"] == mock_user
        assert call_kwargs["description"] == "Test appeal"
        assert call_kwargs["appeal_number"].startswith("APP-")

        mock_dispatcher.emit.assert_called_once_with(EventType.APPEAL_RECEIVED, {"appeal_id": 20, "created_by_id": 1})
        assert result == mock_appeal

    @patch("trunk.services.complaint_service.event_dispatcher")
    def test_decide_appeal(self, mock_dispatcher):
        mock_user = Mock(id=1)
        mock_appeal = Mock(id=20, status="open")

        result = ComplaintService.decide_appeal(mock_appeal, "upheld", mock_user, notes="Valid appeal")

        assert mock_appeal.status == "closed"
        assert "Decision: upheld" in mock_appeal.resolution_notes
        assert "Notes: Valid appeal" in mock_appeal.resolution_notes
        mock_appeal.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.APPEAL_DECIDED,
            {
                "appeal_id": 20,
                "old_status": "open",
                "decision": "upheld",
                "decided_by_id": 1,
                "notes": "Valid appeal",
            },
        )
        assert result == mock_appeal

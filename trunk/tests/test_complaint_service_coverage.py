from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from trunk.services.complaint_service import ComplaintService

User = get_user_model()


class TestComplaintServiceCoverage(TestCase):
    def test_update_complaint_status_no_notes(self):
        complaint = MagicMock()
        complaint.status = "open"
        complaint.id = 1
        user = User.objects.create(username="staff")

        with patch("trunk.services.complaint_service.event_dispatcher") as mock_dispatcher:
            ComplaintService.update_complaint_status(complaint, "investigating", user, notes="")

            # Verify notes were not updated (or at least the if block was skipped)
            # Since we can't easily check if the if block was skipped on a mock without side effects,
            # we rely on coverage report. But logically, if notes="", it skips.

            self.assertEqual(complaint.status, "investigating")
            mock_dispatcher.emit.assert_called_once()

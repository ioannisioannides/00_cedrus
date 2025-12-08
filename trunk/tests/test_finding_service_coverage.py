from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from trunk.services.finding_service import FindingService

User = get_user_model()


class TestFindingServiceCoverage(TestCase):
    def test_verify_nonconformity_invalid_action(self):
        nc = MagicMock()
        nc.verification_status = "open"
        user = User.objects.create(username="auditor")

        # Pass an invalid action
        FindingService.verify_nonconformity(nc, user, action="invalid_action")

        # Should just save and return
        nc.save.assert_called_once()
        # Status should not change
        self.assertEqual(nc.verification_status, "open")

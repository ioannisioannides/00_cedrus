from unittest.mock import MagicMock, patch

from django.test import TestCase

from trunk.services.audit_service import AuditService


class MockAudit:
    def __init__(self):
        self.status = "draft"
        self.id = 1
        self.some_other_field = "original"
        self.certifications = MagicMock()
        self.sites = MagicMock()
        self.created_by = "user"
        self.created_at = "date"
        self.updated_at = "date"

    def save(self):
        pass


class TestAuditServiceCoverageV2(TestCase):
    def test_update_audit_ignored_fields(self):
        audit = MockAudit()
        # 'id' should be ignored
        data = {"id": 999, "some_other_field": "new_value"}

        with patch("trunk.services.audit_service.event_dispatcher"):
            AuditService.update_audit(audit, data)

        # Verify id was NOT updated
        self.assertEqual(audit.id, 1)
        # Verify some_other_field WAS updated
        self.assertEqual(audit.some_other_field, "new_value")

    def test_update_audit_non_existent_field(self):
        audit = MockAudit()
        # 'non_existent' should be ignored because hasattr returns False
        data = {"non_existent": "value"}

        with patch("trunk.services.audit_service.event_dispatcher"):
            AuditService.update_audit(audit, data)

        # Verify non_existent was NOT added
        self.assertFalse(hasattr(audit, "non_existent"))

from django.contrib.auth import get_user_model
from django.test import TestCase

from trunk.services.competence_service import CompetenceService

User = get_user_model()


class TestCompetenceServiceCoverage(TestCase):
    def test_ensure_auditor_has_active_qualification_no_certifications_attr(self):
        user = User.objects.create(username="auditor")

        # Create a mock object that doesn't have 'certifications' attribute
        # We can't use Audit model because it has the attribute
        class MockAudit:
            pass

        audit = MockAudit()

        # Should return None
        result = CompetenceService.ensure_auditor_has_active_qualification(user, audit)
        self.assertIsNone(result)

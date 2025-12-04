from unittest.mock import MagicMock, patch

import pytest

from trunk.events import EventType
from trunk.services.documentation_service import DocumentationService


@pytest.mark.django_db
class TestDocumentationService:
    @pytest.fixture
    def mock_audit(self):
        audit = MagicMock()
        audit.pk = 1
        return audit

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.pk = 101
        return user

    @patch("trunk.services.documentation_service.AuditChanges")
    @patch("trunk.services.documentation_service.event_dispatcher")
    def test_update_audit_changes(self, mock_dispatcher, mock_changes_class, mock_audit, mock_user):
        # Setup
        mock_changes = MagicMock()
        mock_changes_class.objects.get_or_create.return_value = (mock_changes, True)

        data = {"changes_identified": True, "details": "Scope changed"}

        # Execute
        result = DocumentationService.update_audit_changes(mock_audit, data, mock_user)

        # Verify
        mock_changes_class.objects.get_or_create.assert_called_once_with(audit=mock_audit)
        assert mock_changes.changes_identified is True
        assert mock_changes.details == "Scope changed"
        mock_changes.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_DOCUMENTATION_UPDATED,
            {
                "audit_id": mock_audit.pk,
                "documentation_type": "changes",
                "updated_by": mock_user.pk,
            },
        )
        assert result == mock_changes

    @patch("trunk.services.documentation_service.AuditPlanReview")
    @patch("trunk.services.documentation_service.event_dispatcher")
    def test_update_audit_plan_review(self, mock_dispatcher, mock_plan_review_class, mock_audit, mock_user):
        # Setup
        mock_plan_review = MagicMock()
        mock_plan_review_class.objects.get_or_create.return_value = (mock_plan_review, True)

        data = {"review_comments": "Plan looks good"}

        # Execute
        result = DocumentationService.update_audit_plan_review(mock_audit, data, mock_user)

        # Verify
        mock_plan_review_class.objects.get_or_create.assert_called_once_with(audit=mock_audit)
        assert mock_plan_review.review_comments == "Plan looks good"
        mock_plan_review.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_DOCUMENTATION_UPDATED,
            {
                "audit_id": mock_audit.pk,
                "documentation_type": "plan_review",
                "updated_by": mock_user.pk,
            },
        )
        assert result == mock_plan_review

    @patch("trunk.services.documentation_service.AuditSummary")
    @patch("trunk.services.documentation_service.event_dispatcher")
    def test_update_audit_summary(self, mock_dispatcher, mock_summary_class, mock_audit, mock_user):
        # Setup
        mock_summary = MagicMock()
        mock_summary_class.objects.get_or_create.return_value = (mock_summary, True)

        data = {"summary_text": "Audit went well"}

        # Execute
        result = DocumentationService.update_audit_summary(mock_audit, data, mock_user)

        # Verify
        mock_summary_class.objects.get_or_create.assert_called_once_with(audit=mock_audit)
        assert mock_summary.summary_text == "Audit went well"
        mock_summary.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_DOCUMENTATION_UPDATED,
            {
                "audit_id": mock_audit.pk,
                "documentation_type": "summary",
                "updated_by": mock_user.pk,
            },
        )
        assert result == mock_summary

    @patch("trunk.services.documentation_service.AuditRecommendation")
    @patch("trunk.services.documentation_service.event_dispatcher")
    def test_update_audit_recommendation(self, mock_dispatcher, mock_recommendation_class, mock_audit, mock_user):
        # Setup
        mock_recommendation = MagicMock()
        mock_recommendation_class.objects.get_or_create.return_value = (mock_recommendation, True)

        data = {"recommendation": "Grant Certification"}

        # Execute
        result = DocumentationService.update_audit_recommendation(mock_audit, data, mock_user)

        # Verify
        mock_recommendation_class.objects.get_or_create.assert_called_once_with(audit=mock_audit)
        assert mock_recommendation.recommendation == "Grant Certification"
        mock_recommendation.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_DOCUMENTATION_UPDATED,
            {
                "audit_id": mock_audit.pk,
                "documentation_type": "recommendation",
                "updated_by": mock_user.pk,
            },
        )
        assert result == mock_recommendation

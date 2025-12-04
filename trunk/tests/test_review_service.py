from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from trunk.events import EventType
from trunk.services.review_service import ReviewService


@pytest.mark.django_db
class TestReviewService:
    @pytest.fixture
    def mock_audit(self):
        audit = MagicMock()
        audit.id = 1
        audit.status = "technical_review"
        # Ensure hasattr(audit, "technical_review") returns False initially
        # MagicMock creates attributes on access, so we need to be careful.
        # We can use a spec or explicitly delete the attribute.
        # However, del only works if it exists.
        # A safer way for hasattr checks on mocks is to use spec.
        # But let's try deleting it first, wrapping in try/except just in case.
        try:
            del audit.technical_review
        except AttributeError:
            pass
        try:
            del audit.certification_decision
        except AttributeError:
            pass
        return audit

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = 101
        user.get_full_name.return_value = "Test User"
        return user

    @patch("trunk.services.review_service.TechnicalReview")
    @patch("trunk.services.review_service.AuditService")
    @patch("trunk.services.review_service.event_dispatcher")
    def test_conduct_technical_review_create(
        self, mock_dispatcher, mock_audit_service, mock_technical_review_class, mock_audit, mock_user
    ):
        # Setup
        mock_review_instance = MagicMock()
        mock_review_instance.status = "approved"
        mock_review_instance.id = 501
        mock_technical_review_class.objects.create.return_value = mock_review_instance

        data = {"status": "approved", "comments": "Good job"}

        # Execute
        result = ReviewService.conduct_technical_review(mock_audit, mock_user, data)

        # Verify
        mock_technical_review_class.objects.create.assert_called_once_with(audit=mock_audit, reviewer=mock_user, **data)
        mock_audit_service.transition_status.assert_called_once_with(
            mock_audit, "decision_pending", mock_user, notes="Technical review approved by Test User"
        )
        mock_dispatcher.emit.assert_called_once_with(
            EventType.TECHNICAL_REVIEW_COMPLETED,
            {"audit_id": mock_audit.id, "review_id": mock_review_instance.id, "reviewer_id": mock_user.id},
        )
        assert result == mock_review_instance

    @patch("trunk.services.review_service.AuditService")
    @patch("trunk.services.review_service.event_dispatcher")
    def test_conduct_technical_review_update(self, mock_dispatcher, mock_audit_service, mock_audit, mock_user):
        # Setup
        mock_review = MagicMock()
        mock_review.status = "pending"
        mock_review.id = 501
        mock_audit.technical_review = mock_review  # Exists now

        data = {"status": "approved", "comments": "Updated comments"}

        # Execute
        result = ReviewService.conduct_technical_review(mock_audit, mock_user, data)

        # Verify
        assert mock_review.status == "approved"
        assert mock_review.comments == "Updated comments"
        mock_review.save.assert_called_once()

        mock_audit_service.transition_status.assert_called_once()
        mock_dispatcher.emit.assert_called_once_with(
            EventType.TECHNICAL_REVIEW_COMPLETED,
            {"audit_id": mock_audit.id, "review_id": mock_review.id, "reviewer_id": mock_user.id},
        )
        assert result == mock_review

    @patch("trunk.services.review_service.CertificationDecision")
    @patch("trunk.services.review_service.AuditService")
    @patch("trunk.services.review_service.CertificateService")
    @patch("trunk.services.review_service.event_dispatcher")
    def test_make_certification_decision(
        self,
        mock_dispatcher,
        mock_cert_service,
        mock_audit_service,
        mock_decision_class,
        mock_audit,
        mock_user,
    ):
        # Setup
        mock_decision_instance = MagicMock()
        mock_decision_instance.id = 601
        mock_decision_instance.get_decision_display.return_value = "Granted"
        mock_decision_class.objects.create.return_value = mock_decision_instance

        cert1 = MagicMock()
        cert2 = MagicMock()
        data = {
            "decision": "granted",
            "comments": "Approved",
            "certifications_affected": [cert1, cert2],
        }

        # Execute
        result = ReviewService.make_certification_decision(mock_audit, mock_user, data)

        # Verify
        mock_decision_class.objects.create.assert_called_once()
        # Check that certifications_affected was popped from data before create
        call_kwargs = mock_decision_class.objects.create.call_args[1]
        assert "certifications_affected" not in call_kwargs

        mock_decision_instance.certifications_affected.set.assert_called_once_with([cert1, cert2])

        mock_audit_service.transition_status.assert_called_once_with(
            mock_audit, "closed", mock_user, notes="Decision: Granted by Test User"
        )

        mock_cert_service.record_decision.assert_called_once_with(mock_decision_instance)

        mock_dispatcher.emit.assert_called_once_with(
            EventType.CERTIFICATION_DECISION_MADE,
            {"audit_id": mock_audit.id, "decision_id": mock_decision_instance.id, "maker_id": mock_user.id},
        )
        assert result == mock_decision_instance

    def test_make_certification_decision_already_exists(self, mock_audit, mock_user):
        # Setup
        mock_audit.certification_decision = MagicMock()

        # Execute & Verify
        with pytest.raises(ValidationError, match="Certification decision already exists"):
            ReviewService.make_certification_decision(mock_audit, mock_user, {})

    @patch("trunk.services.review_service.event_dispatcher")
    def test_update_certification_decision(self, mock_dispatcher, mock_user):
        # Setup
        mock_decision = MagicMock()
        mock_decision.id = 601
        mock_decision.audit.id = 1

        cert1 = MagicMock()
        data = {"decision": "refused", "certifications_affected": [cert1]}

        # Execute
        result = ReviewService.update_certification_decision(mock_decision, mock_user, data)

        # Verify
        assert mock_decision.decision == "refused"
        mock_decision.save.assert_called_once()
        mock_decision.certifications_affected.set.assert_called_once_with([cert1])

        mock_dispatcher.emit.assert_called_once_with(
            EventType.CERTIFICATION_DECISION_UPDATED,
            {"audit_id": 1, "decision_id": mock_decision.id, "maker_id": mock_user.id},
        )
        assert result == mock_decision

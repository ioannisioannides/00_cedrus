from datetime import date, timedelta
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from trunk.services.competence_service import CompetenceService


class TestCompetenceService:
    @patch("trunk.services.competence_service.AuditorQualification")
    def test_get_active_qualifications(self, mock_qual_model):
        mock_user = Mock()
        mock_qs = Mock()
        mock_qual_model.objects.filter.return_value = mock_qs
        mock_qs.order_by.return_value = ["qual1", "qual2"]

        result = CompetenceService.get_active_qualifications(mock_user)

        mock_qual_model.objects.filter.assert_called_once_with(auditor=mock_user, status="active")
        mock_qs.order_by.assert_called_once_with("-issue_date")
        assert result == ["qual1", "qual2"]

    @patch("trunk.services.competence_service.CompetenceService.get_active_qualifications")
    def test_ensure_auditor_has_active_qualification_no_quals(self, mock_get_quals):
        mock_user = Mock(username="testuser")
        mock_audit = Mock()
        mock_audit.certifications.all.return_value = [Mock(standard_id=1)]

        mock_get_quals.return_value = []

        with pytest.raises(ValidationError, match="lacks active qualifications"):
            CompetenceService.ensure_auditor_has_active_qualification(mock_user, mock_audit)

    @patch("trunk.services.competence_service.CompetenceService.get_active_qualifications")
    def test_ensure_auditor_has_active_qualification_no_coverage(self, mock_get_quals):
        mock_user = Mock(username="testuser")
        mock_audit = Mock()
        mock_audit.certifications.all.return_value = [Mock(standard_id=1)]

        mock_qual = Mock()
        mock_qual.standards.values_list.return_value = [2, 3]  # Different standards
        mock_get_quals.return_value = [mock_qual]

        with pytest.raises(ValidationError, match="qualifications do not cover audit standards"):
            CompetenceService.ensure_auditor_has_active_qualification(mock_user, mock_audit)

    @patch("trunk.services.competence_service.CompetenceService.get_active_qualifications")
    def test_ensure_auditor_has_active_qualification_success(self, mock_get_quals):
        mock_user = Mock(username="testuser")
        mock_audit = Mock()
        mock_audit.certifications.all.return_value = [Mock(standard_id=1)]

        mock_qual = Mock()
        mock_qual.standards.values_list.return_value = [1, 2]  # Matches standard 1
        mock_get_quals.return_value = [mock_qual]

        # Should not raise
        CompetenceService.ensure_auditor_has_active_qualification(mock_user, mock_audit)

    @patch("trunk.services.competence_service.AuditorCompetenceEvaluation")
    def test_check_recent_competence_evaluation_none(self, mock_eval_model):
        mock_user = Mock(username="testuser")
        mock_eval_model.objects.filter.return_value.order_by.return_value.first.return_value = None

        with pytest.raises(ValidationError, match="has no competence evaluation record"):
            CompetenceService.check_recent_competence_evaluation(mock_user)

    @patch("trunk.services.competence_service.AuditorCompetenceEvaluation")
    def test_check_recent_competence_evaluation_old(self, mock_eval_model):
        mock_user = Mock(username="testuser")
        mock_eval = Mock()
        mock_eval.evaluation_date = date.today() - timedelta(days=366)
        mock_eval_model.objects.filter.return_value.order_by.return_value.first.return_value = mock_eval

        with pytest.raises(ValidationError, match="competence evaluation is older than 12 months"):
            CompetenceService.check_recent_competence_evaluation(mock_user)

    @patch("trunk.services.competence_service.AuditorCompetenceEvaluation")
    def test_check_recent_competence_evaluation_valid(self, mock_eval_model):
        mock_user = Mock(username="testuser")
        mock_eval = Mock()
        mock_eval.evaluation_date = date.today() - timedelta(days=300)
        mock_eval_model.objects.filter.return_value.order_by.return_value.first.return_value = mock_eval

        # Should not raise
        CompetenceService.check_recent_competence_evaluation(mock_user)

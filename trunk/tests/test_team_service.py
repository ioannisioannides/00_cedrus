from unittest.mock import Mock, patch

import pytest

from trunk.events import EventType
from trunk.services.team_service import TeamService


@pytest.mark.django_db
class TestTeamService:
    @patch("trunk.services.team_service.AuditTeamMember")
    @patch("trunk.services.team_service.event_dispatcher")
    @patch("trunk.services.team_service.TeamService.check_competence")
    def test_add_team_member(self, mock_check_competence, mock_dispatcher, mock_member_model):
        mock_audit = Mock(id=1)
        mock_user = Mock(id=10)
        data = {"user": mock_user, "role": "Lead Auditor"}
        mock_member = Mock(id=100, user=mock_user)
        mock_member_model.objects.create.return_value = mock_member

        result = TeamService.add_team_member(mock_audit, data, mock_user)

        mock_member_model.objects.create.assert_called_once_with(audit=mock_audit, **data)
        mock_check_competence.assert_called_once_with(mock_audit, mock_user)

        mock_dispatcher.emit.assert_called_once_with(
            EventType.TEAM_MEMBER_ADDED, {"audit_id": 1, "team_member_id": 100, "added_by_id": 10}
        )
        assert result == mock_member

    @patch("trunk.services.team_service.AuditTeamMember")
    @patch("trunk.services.team_service.event_dispatcher")
    @patch("trunk.services.team_service.TeamService.check_competence")
    def test_add_team_member_no_user(self, mock_check_competence, mock_dispatcher, mock_member_model):
        mock_audit = Mock(id=1)
        data = {"name": "External Expert", "role": "Technical Expert"}
        mock_member = Mock(id=100, user=None)
        mock_member_model.objects.create.return_value = mock_member

        result = TeamService.add_team_member(mock_audit, data)

        mock_member_model.objects.create.assert_called_once_with(audit=mock_audit, **data)
        mock_check_competence.assert_not_called()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.TEAM_MEMBER_ADDED, {"audit_id": 1, "team_member_id": 100, "added_by_id": None}
        )
        assert result == mock_member

    @patch("trunk.services.team_service.TeamService.check_competence")
    def test_update_team_member(self, mock_check_competence):
        mock_member = Mock(audit=Mock())
        mock_user = Mock()
        mock_member.user = mock_user
        data = {"role": "Auditor", "user": mock_user}

        result = TeamService.update_team_member(mock_member, data)

        assert mock_member.role == "Auditor"
        mock_member.save.assert_called_once()
        mock_check_competence.assert_called_once_with(mock_member.audit, mock_user)
        assert result == mock_member

    @patch("trunk.services.team_service.event_dispatcher")
    def test_remove_team_member(self, mock_dispatcher):
        mock_audit = Mock(id=1)
        mock_member = Mock(audit=mock_audit)
        mock_member.name = "John Doe"
        mock_user = Mock(id=10)

        TeamService.remove_team_member(mock_member, mock_user)

        mock_member.delete.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.TEAM_MEMBER_REMOVED, {"audit_id": 1, "member_name": "John Doe", "removed_by_id": 10}
        )

    def test_check_competence(self):
        # It's a placeholder, just ensure it runs without error
        TeamService.check_competence(Mock(), Mock())

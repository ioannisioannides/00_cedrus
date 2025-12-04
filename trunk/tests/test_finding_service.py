from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

from trunk.events import EventType
from trunk.services.finding_service import FindingService


@pytest.mark.django_db
class TestFindingService:
    @pytest.fixture
    def mock_audit(self):
        audit = MagicMock()
        audit.id = 1
        return audit

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = 101
        return user

    @patch("trunk.services.finding_service.Nonconformity")
    @patch("trunk.services.finding_service.event_dispatcher")
    def test_create_nonconformity(self, mock_dispatcher, mock_nc_class, mock_audit, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201
        mock_nc_class.return_value = mock_nc

        data = {"description": "Bad thing happened"}

        # Execute
        result = FindingService.create_nonconformity(mock_audit, mock_user, data)

        # Verify
        mock_nc_class.assert_called_once_with(
            audit=mock_audit, created_by=mock_user, verification_status="open", **data
        )
        mock_nc.save.assert_called_once()
        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_CREATED,
            {
                "finding_id": mock_nc.id,
                "finding_type": "nonconformity",
                "audit_id": mock_audit.id,
                "created_by_id": mock_user.id,
            },
        )
        assert result == mock_nc

    @patch("trunk.services.finding_service.Observation")
    @patch("trunk.services.finding_service.event_dispatcher")
    def test_create_observation(self, mock_dispatcher, mock_obs_class, mock_audit, mock_user):
        # Setup
        mock_obs = MagicMock()
        mock_obs.id = 301
        mock_obs_class.return_value = mock_obs

        data = {"description": "Just looking"}

        # Execute
        result = FindingService.create_observation(mock_audit, mock_user, data)

        # Verify
        mock_obs_class.assert_called_once_with(audit=mock_audit, created_by=mock_user, **data)
        mock_obs.save.assert_called_once()
        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_CREATED,
            {
                "finding_id": mock_obs.id,
                "finding_type": "observation",
                "audit_id": mock_audit.id,
                "created_by_id": mock_user.id,
            },
        )
        assert result == mock_obs

    @patch("trunk.services.finding_service.OpportunityForImprovement")
    @patch("trunk.services.finding_service.event_dispatcher")
    def test_create_ofi(self, mock_dispatcher, mock_ofi_class, mock_audit, mock_user):
        # Setup
        mock_ofi = MagicMock()
        mock_ofi.id = 401
        mock_ofi_class.return_value = mock_ofi

        data = {"description": "Could be better"}

        # Execute
        result = FindingService.create_ofi(mock_audit, mock_user, data)

        # Verify
        mock_ofi_class.assert_called_once_with(audit=mock_audit, created_by=mock_user, **data)
        mock_ofi.save.assert_called_once()
        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_CREATED,
            {
                "finding_id": mock_ofi.id,
                "finding_type": "ofi",
                "audit_id": mock_audit.id,
                "created_by_id": mock_user.id,
            },
        )
        assert result == mock_ofi

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_respond_to_nonconformity(self, mock_dispatcher):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201
        mock_nc.audit.id = 1

        response_data = {"root_cause": "Human error", "correction": "Fixed it"}

        # Execute
        result = FindingService.respond_to_nonconformity(mock_nc, response_data)

        # Verify
        assert mock_nc.root_cause == "Human error"
        assert mock_nc.correction == "Fixed it"
        assert mock_nc.verification_status == "client_responded"
        mock_nc.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_CLIENT_RESPONDED,
            {"nonconformity_id": mock_nc.id, "audit_id": 1, "response_data": response_data},
        )
        assert result == mock_nc

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_verify_nonconformity_accept(self, mock_dispatcher, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201

        # Execute
        result = FindingService.verify_nonconformity(mock_nc, mock_user, "accept", notes="Looks good")

        # Verify
        assert mock_nc.verification_status == "accepted"
        assert mock_nc.verified_by == mock_user
        assert mock_nc.verification_notes == "Looks good"
        mock_nc.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_VERIFIED_ACCEPTED,
            {"nc_id": mock_nc.id, "verified_by_id": mock_user.id, "notes": "Looks good"},
        )
        assert result == mock_nc

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_verify_nonconformity_reject(self, mock_dispatcher, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201

        # Execute
        result = FindingService.verify_nonconformity(mock_nc, mock_user, "request_changes", notes="Not good enough")

        # Verify
        assert mock_nc.verification_status == "open"
        assert mock_nc.verification_notes == "Not good enough"
        mock_nc.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_VERIFIED_REJECTED,
            {"nc_id": mock_nc.id, "verified_by_id": mock_user.id, "notes": "Not good enough"},
        )
        assert result == mock_nc

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_verify_nonconformity_close(self, mock_dispatcher, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201
        mock_nc.verification_status = "accepted"

        # Execute
        result = FindingService.verify_nonconformity(mock_nc, mock_user, "close")

        # Verify
        assert mock_nc.verification_status == "closed"
        mock_nc.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.NC_CLOSED,
            {"nc_id": mock_nc.id, "closed_by_id": mock_user.id},
        )
        assert result == mock_nc

    def test_verify_nonconformity_close_invalid(self, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.verification_status = "open"

        # Execute & Verify
        with pytest.raises(ValidationError, match="Cannot close nonconformity that hasn't been accepted"):
            FindingService.verify_nonconformity(mock_nc, mock_user, "close")

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_update_nonconformity(self, mock_dispatcher, mock_user):
        # Setup
        mock_nc = MagicMock()
        mock_nc.id = 201
        mock_nc.audit.id = 1

        data = {"description": "Updated description"}

        # Execute
        result = FindingService.update_nonconformity(mock_nc, data, mock_user)

        # Verify
        assert mock_nc.description == "Updated description"
        mock_nc.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_UPDATED,
            {
                "finding_id": mock_nc.id,
                "finding_type": "nonconformity",
                "audit_id": 1,
                "updated_by_id": mock_user.id,
            },
        )
        assert result == mock_nc

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_update_observation(self, mock_dispatcher, mock_user):
        # Setup
        mock_obs = MagicMock()
        mock_obs.id = 301
        mock_obs.audit.id = 1

        data = {"description": "Updated obs"}

        # Execute
        result = FindingService.update_observation(mock_obs, data, mock_user)

        # Verify
        assert mock_obs.description == "Updated obs"
        mock_obs.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_UPDATED,
            {
                "finding_id": mock_obs.id,
                "finding_type": "observation",
                "audit_id": 1,
                "updated_by_id": mock_user.id,
            },
        )
        assert result == mock_obs

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_update_ofi(self, mock_dispatcher, mock_user):
        # Setup
        mock_ofi = MagicMock()
        mock_ofi.id = 401
        mock_ofi.audit.id = 1

        data = {"description": "Updated ofi"}

        # Execute
        result = FindingService.update_ofi(mock_ofi, data, mock_user)

        # Verify
        assert mock_ofi.description == "Updated ofi"
        mock_ofi.save.assert_called_once()

        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_UPDATED,
            {
                "finding_id": mock_ofi.id,
                "finding_type": "ofi",
                "audit_id": 1,
                "updated_by_id": mock_user.id,
            },
        )
        assert result == mock_ofi

    @patch("trunk.services.finding_service.event_dispatcher")
    def test_delete_finding(self, mock_dispatcher, mock_user):
        # Setup
        mock_finding = MagicMock()
        mock_finding.id = 999
        mock_finding.audit.id = 1
        mock_finding.__class__.__name__ = "Nonconformity"

        # Execute
        FindingService.delete_finding(mock_finding, mock_user)

        # Verify
        mock_finding.delete.assert_called_once()
        mock_dispatcher.emit.assert_called_once_with(
            EventType.FINDING_DELETED,
            {
                "finding_type": "nonconformity",
                "audit_id": 1,
                "deleted_by_id": mock_user.id,
            },
        )

from unittest.mock import Mock, patch

from trunk.events.handlers import (
    on_appeal_received,
    on_audit_status_changed,
    on_certificate_history_created,
    on_complaint_received,
    on_nc_verified,
    register_event_handlers,
)


class TestTrunkHandlersCoverage:
    def test_on_audit_status_changed_missing_data(self):
        on_audit_status_changed({})
        on_audit_status_changed({"new_status": "submitted"})
        on_audit_status_changed({"audit_id": 1})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_audit_status_changed_not_found(self, mock_get_model):
        mock_audit_model = Mock()
        mock_audit_model.objects.get.side_effect = Exception("Audit.DoesNotExist")  # Simulating DoesNotExist
        # We need to mock the DoesNotExist exception class on the model
        mock_audit_model.DoesNotExist = Exception

        mock_user_model = Mock()
        mock_user_model.DoesNotExist = Exception

        mock_get_model.side_effect = [mock_audit_model, mock_user_model]

        on_audit_status_changed({"audit_id": 1, "new_status": "submitted", "changed_by_id": 1})

    def test_on_nc_verified_missing_data(self):
        on_nc_verified({})
        on_nc_verified({"verification_status": "accepted"})
        on_nc_verified({"nc_id": 1})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_nc_verified_not_found(self, mock_get_model):
        mock_nc_model = Mock()
        mock_nc_model.DoesNotExist = Exception
        mock_nc_model.objects.get.side_effect = Exception("Nonconformity.DoesNotExist")
        mock_get_model.return_value = mock_nc_model

        on_nc_verified({"nc_id": 1, "verification_status": "accepted"})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_nc_verified_unknown_status(self, mock_get_model):
        mock_nc_model = Mock()
        mock_nc = Mock()
        mock_nc_model.objects.get.return_value = mock_nc
        mock_get_model.return_value = mock_nc_model

        on_nc_verified({"nc_id": 1, "verification_status": "unknown"})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_complaint_received_not_found(self, mock_get_model):
        mock_complaint_model = Mock()
        mock_complaint_model.DoesNotExist = Exception
        mock_complaint_model.objects.get.side_effect = Exception("Complaint.DoesNotExist")
        mock_get_model.return_value = mock_complaint_model

        on_complaint_received({"complaint_id": 1})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_appeal_received_not_found(self, mock_get_model):
        mock_appeal_model = Mock()
        mock_appeal_model.DoesNotExist = Exception
        mock_appeal_model.objects.get.side_effect = Exception("Appeal.DoesNotExist")
        mock_get_model.return_value = mock_appeal_model

        on_appeal_received({"appeal_id": 1})

    @patch("trunk.events.handlers.apps.get_model")
    def test_on_certificate_history_created_not_found(self, mock_get_model):
        mock_history_model = Mock()
        mock_history_model.DoesNotExist = Exception
        mock_history_model.objects.get.side_effect = Exception("CertificateHistory.DoesNotExist")
        mock_get_model.return_value = mock_history_model

        on_certificate_history_created({"history_id": 1})

    @patch("trunk.events.handlers.event_dispatcher")
    @patch("trunk.events.handlers.logger")
    def test_register_event_handlers(self, mock_logger, mock_dispatcher):
        register_event_handlers()
        assert mock_dispatcher.register.call_count >= 4

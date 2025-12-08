from unittest.mock import Mock, patch

from core.events.handlers import on_audit_status_changed, on_nc_verified, register_event_handlers


class TestHandlersCoverage:
    def test_on_audit_status_changed_missing_data(self):
        # Test with empty payload
        on_audit_status_changed({})

        # Test with missing audit
        on_audit_status_changed({"new_status": "submitted"})

        # Test with missing new_status
        on_audit_status_changed({"audit": Mock()})

    def test_on_nc_verified_missing_data(self):
        # Test with empty payload
        on_nc_verified({})

        # Test with missing nc
        on_nc_verified({"verification_status": "accepted"})

        # Test with missing verification_status
        on_nc_verified({"nc": Mock()})

        # Test with unknown verification_status
        on_nc_verified({"nc": Mock(), "verification_status": "unknown_status"})

    @patch("core.events.handlers.event_dispatcher")
    @patch("core.events.handlers.logger")
    def test_register_event_handlers(self, mock_logger, mock_dispatcher):
        register_event_handlers()

        assert mock_dispatcher.register.call_count >= 4
        mock_logger.info.assert_called_with("Registered event handlers for audit lifecycle events")

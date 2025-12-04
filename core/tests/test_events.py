from unittest.mock import Mock, patch

from core.events.dispatcher import EventDispatcher
from core.events.handlers import (
    on_appeal_received,
    on_audit_status_changed,
    on_certificate_history_created,
    on_complaint_received,
    on_nc_verified,
)
from trunk.events import EventType


class TestEventDispatcher:
    def test_register_and_emit(self):
        dispatcher = EventDispatcher()
        handler = Mock()
        event_type = "test_event"
        payload = {"data": "test"}

        dispatcher.register(event_type, handler)
        dispatcher.emit(event_type, payload)

        handler.assert_called_once_with(payload)

    def test_unregister(self):
        dispatcher = EventDispatcher()
        handler = Mock()
        event_type = "test_event"
        payload = {"data": "test"}

        dispatcher.register(event_type, handler)
        dispatcher.unregister(event_type, handler)
        dispatcher.emit(event_type, payload)

        handler.assert_not_called()

    def test_emit_no_handlers(self):
        dispatcher = EventDispatcher()
        event_type = "test_event"
        payload = {"data": "test"}

        # Should not raise error
        dispatcher.emit(event_type, payload)

    def test_handler_exception_handling(self):
        dispatcher = EventDispatcher()
        handler = Mock(side_effect=Exception("Test error"))
        event_type = "test_event"
        payload = {"data": "test"}

        dispatcher.register(event_type, handler)

        # Should catch exception and log error, not crash
        dispatcher.emit(event_type, payload)

        handler.assert_called_once_with(payload)

    def test_clear_specific_event(self):
        dispatcher = EventDispatcher()
        handler1 = Mock()
        handler2 = Mock()

        dispatcher.register("event1", handler1)
        dispatcher.register("event2", handler2)

        dispatcher.clear("event1")

        dispatcher.emit("event1", {})
        dispatcher.emit("event2", {})

        handler1.assert_not_called()
        handler2.assert_called_once()

    def test_clear_all(self):
        dispatcher = EventDispatcher()
        handler1 = Mock()
        handler2 = Mock()

        dispatcher.register("event1", handler1)
        dispatcher.register("event2", handler2)

        dispatcher.clear()

        dispatcher.emit("event1", {})
        dispatcher.emit("event2", {})

        handler1.assert_not_called()
        handler2.assert_not_called()


@patch("core.events.handlers.event_dispatcher")
class TestEventHandlers:
    def test_on_audit_status_changed_client_review(self, mock_dispatcher):
        audit = Mock()
        audit.id = 1
        payload = {"audit": audit, "new_status": "client_review", "changed_by": "user"}

        on_audit_status_changed(payload)

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_SUBMITTED_TO_CLIENT, {"audit": audit, "changed_by": "user"}
        )

    def test_on_audit_status_changed_submitted(self, mock_dispatcher):
        audit = Mock()
        audit.id = 1
        payload = {"audit": audit, "new_status": "submitted", "changed_by": "user"}

        on_audit_status_changed(payload)

        mock_dispatcher.emit.assert_called_once_with(
            EventType.AUDIT_SUBMITTED_TO_CB, {"audit": audit, "changed_by": "user"}
        )

    def test_on_audit_status_changed_decided(self, mock_dispatcher):
        audit = Mock()
        audit.id = 1
        payload = {"audit": audit, "new_status": "decided", "changed_by": "user"}

        on_audit_status_changed(payload)

        mock_dispatcher.emit.assert_called_once_with(EventType.AUDIT_DECIDED, {"audit": audit, "changed_by": "user"})

    def test_on_audit_status_changed_ignored_status(self, mock_dispatcher):
        audit = Mock()
        payload = {"audit": audit, "new_status": "draft", "changed_by": "user"}

        on_audit_status_changed(payload)

        mock_dispatcher.emit.assert_not_called()

    def test_on_nc_verified_accepted(self, mock_dispatcher):
        nc = Mock()
        nc.id = 1
        nc.clause = "4.1"
        payload = {"nc": nc, "verification_status": "accepted"}

        on_nc_verified(payload)

        mock_dispatcher.emit.assert_called_once_with(EventType.NC_VERIFIED_ACCEPTED, {"nc": nc})

    def test_on_nc_verified_rejected(self, mock_dispatcher):
        nc = Mock()
        nc.id = 1
        nc.clause = "4.1"
        payload = {"nc": nc, "verification_status": "rejected"}

        on_nc_verified(payload)

        mock_dispatcher.emit.assert_called_once_with(EventType.NC_VERIFIED_REJECTED, {"nc": nc})

    def test_on_nc_verified_closed(self, mock_dispatcher):
        nc = Mock()
        nc.id = 1
        nc.clause = "4.1"
        payload = {"nc": nc, "verification_status": "closed"}

        on_nc_verified(payload)

        mock_dispatcher.emit.assert_called_once_with(EventType.NC_CLOSED, {"nc": nc})

    def test_on_complaint_received(self, mock_dispatcher):
        complaint = Mock()
        complaint.complaint_number = "C-001"
        complaint.complainant_name = "John Doe"
        payload = {"complaint": complaint}

        on_complaint_received(payload)

        # Just logs, doesn't emit
        mock_dispatcher.emit.assert_not_called()

    def test_on_appeal_received(self, mock_dispatcher):
        appeal = Mock()
        appeal.appeal_number = "A-001"
        appeal.appellant_name = "Jane Doe"
        payload = {"appeal": appeal}

        on_appeal_received(payload)

        # Just logs, doesn't emit
        mock_dispatcher.emit.assert_not_called()

    def test_on_certificate_history_created(self, mock_dispatcher):
        history = Mock()
        history.action = "issued"
        history.certification.certificate_id = "CERT-001"
        payload = {"history": history}

        on_certificate_history_created(payload)

        # Just logs, doesn't emit
        mock_dispatcher.emit.assert_not_called()

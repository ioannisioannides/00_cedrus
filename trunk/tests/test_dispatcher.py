from unittest.mock import MagicMock, patch

from trunk.events.dispatcher import EventDispatcher


class TestEventDispatcher:
    def test_register_and_dispatch_sync(self):
        dispatcher = EventDispatcher()
        mock_handler = MagicMock()

        dispatcher.register("TEST_EVENT", mock_handler)

        payload = {"data": 123}
        dispatcher.dispatch_sync("TEST_EVENT", payload)

        mock_handler.assert_called_once_with(payload)

    def test_unregister(self):
        dispatcher = EventDispatcher()
        mock_handler = MagicMock()

        dispatcher.register("TEST_EVENT", mock_handler)
        dispatcher.unregister("TEST_EVENT", mock_handler)

        dispatcher.dispatch_sync("TEST_EVENT", {})

        mock_handler.assert_not_called()

    def test_unregister_not_found(self):
        dispatcher = EventDispatcher()
        mock_handler = MagicMock()

        # Should not raise error
        dispatcher.unregister("TEST_EVENT", mock_handler)

    def test_clear_all(self):
        dispatcher = EventDispatcher()
        mock_handler = MagicMock()

        dispatcher.register("TEST_EVENT", mock_handler)
        dispatcher.clear()

        dispatcher.dispatch_sync("TEST_EVENT", {})

        mock_handler.assert_not_called()

    def test_clear_specific(self):
        dispatcher = EventDispatcher()
        mock_handler1 = MagicMock()
        mock_handler2 = MagicMock()

        dispatcher.register("EVENT_1", mock_handler1)
        dispatcher.register("EVENT_2", mock_handler2)

        dispatcher.clear("EVENT_1")

        dispatcher.dispatch_sync("EVENT_1", {})
        dispatcher.dispatch_sync("EVENT_2", {})

        mock_handler1.assert_not_called()
        mock_handler2.assert_called_once()

    @patch("trunk.events.tasks.dispatch_event_task")
    def test_emit(self, mock_task):
        dispatcher = EventDispatcher()

        dispatcher.emit("TEST_EVENT", {"data": 1})

        mock_task.delay.assert_called_once_with("TEST_EVENT", {"data": 1})

    def test_dispatch_sync_handler_error(self):
        dispatcher = EventDispatcher()
        mock_handler = MagicMock(side_effect=Exception("Boom"))

        dispatcher.register("TEST_EVENT", mock_handler)

        # Should catch exception and log error, not raise
        dispatcher.dispatch_sync("TEST_EVENT", {})

        mock_handler.assert_called_once()

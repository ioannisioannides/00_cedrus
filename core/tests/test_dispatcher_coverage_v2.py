from unittest.mock import Mock

from core.events.dispatcher import EventDispatcher


class TestCoreDispatcherCoverage:
    def test_unregister_not_found(self):
        """Test unregistering a handler that is not registered in core dispatcher."""
        dispatcher = EventDispatcher()
        handler = Mock()

        # Register a different handler so the list isn't empty (optional but good for realism)
        other_handler = Mock()
        dispatcher.register("test_event", other_handler)

        # Try to unregister the handler that isn't there
        # This should trigger list.remove(x) raising ValueError, which is caught
        dispatcher.unregister("test_event", handler)

        # Verify the other handler is still there
        assert other_handler in dispatcher._handlers["test_event"]

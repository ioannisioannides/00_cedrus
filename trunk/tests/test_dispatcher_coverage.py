from unittest.mock import Mock

from trunk.events.dispatcher import EventDispatcher


class TestDispatcherCoverage:
    def test_unregister_not_found(self):
        """Test unregistering a handler that is not registered."""
        dispatcher = EventDispatcher()
        handler = Mock()

        # Register a handler for an event
        dispatcher.register("test_event", handler)

        # Try to unregister a DIFFERENT handler for the same event
        # This should trigger the ValueError inside the remove() call
        # but it should be caught and ignored
        other_handler = Mock()
        dispatcher.unregister("test_event", other_handler)

        # Verify the original handler is still there
        assert handler in dispatcher._handlers["test_event"]

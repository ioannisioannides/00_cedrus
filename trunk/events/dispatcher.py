"""
Event dispatcher for the Cedrus event system.

Provides a simple event dispatcher for publishing and subscribing to events.
This enables decoupled communication between different parts of the application.
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Simple event dispatcher for publish-subscribe pattern.

    Allows handlers to register for specific event types and receive
    notifications when those events are emitted.
    """

    def __init__(self):
        self._handlers = defaultdict(list)

    def register(self, event_type, handler):
        """
        Register an event handler.

        Args:
            event_type: The event type to listen for (string)
            handler: Callable that will be invoked when event is emitted
        """
        self._handlers[event_type].append(handler)
        logger.debug("Registered handler for event type: %s", event_type)

    def unregister(self, event_type, handler):
        """
        Unregister an event handler.

        Args:
            event_type: The event type
            handler: The handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug("Unregistered handler for event type: %s", event_type)
            except ValueError:
                pass

    def emit(self, event_type, payload):
        """
        Emit an event asynchronously via Celery.

        Args:
            event_type: The event type (string)
            payload: The event payload (must be JSON serializable)
        """
        from trunk.events.tasks import dispatch_event_task

        logger.info("Queueing event: %s", event_type)
        # We use .delay() to send the task to Celery
        dispatch_event_task.delay(event_type, payload)

    def dispatch_sync(self, event_type, payload):
        """
        Dispatch an event synchronously to all registered handlers.
        This is called by the Celery worker.

        Args:
            event_type: The event type (string)
            payload: The event payload
        """
        logger.info("Dispatching event sync: %s", event_type)

        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error in event handler for %s: %s", event_type, e, exc_info=True)

    def clear(self, event_type=None):
        """
        Clear event handlers.

        Args:
            event_type: Optional specific event type to clear. If None, clears all.
        """
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()


# Global singleton instance
event_dispatcher = EventDispatcher()

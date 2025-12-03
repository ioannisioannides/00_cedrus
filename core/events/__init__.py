"""
Event system for Cedrus.

Provides a lightweight event dispatcher for decoupled communication
between different parts of the application.
"""

from .dispatcher import EventDispatcher, event_dispatcher
from .types import EventType

__all__ = ["event_dispatcher", "EventDispatcher", "EventType"]

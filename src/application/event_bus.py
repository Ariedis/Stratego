"""
src/application/event_bus.py

Publish/subscribe event bus for the Stratego application layer.
Specification: system_design.md §7
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """A simple synchronous publish/subscribe event dispatcher.

    Subscribers register callables for specific event types.  When an event is
    published, all registered callbacks for that type are invoked.  Exceptions
    raised by individual callbacks are caught and logged so that one failing
    subscriber does not block others.
    """

    def __init__(self) -> None:
        """Initialise the event bus with an empty subscriber registry."""
        self._subscribers: dict[type, list[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event_type: type, callback: Callable[..., Any]) -> None:
        """Register *callback* to be called whenever an event of *event_type* is published.

        Args:
            event_type: The class of event to listen for.
            callback: A callable that accepts a single positional argument (the event).
        """
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: type, callback: Callable[..., Any]) -> None:
        """Remove *callback* from the subscriber list for *event_type*.

        Does nothing if the callback is not currently subscribed.

        Args:
            event_type: The class of event the callback was registered for.
            callback: The callable to remove.
        """
        try:
            self._subscribers[event_type].remove(callback)
        except ValueError:
            pass

    def publish(self, event: Any) -> None:
        """Dispatch *event* to all subscribers registered for its type.

        Each callback is invoked with *event* as the sole argument.  If a
        callback raises, the exception is logged at ERROR level and the
        remaining subscribers are still called.

        Args:
            event: The event instance to dispatch.
        """
        event_type = type(event)
        for callback in list(self._subscribers.get(event_type, [])):
            try:
                callback(event)
            except Exception:
                logger.exception(
                    "EventBus: subscriber %r raised an exception for event %r",
                    callback,
                    event,
                )

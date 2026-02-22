"""
src/presentation/screens/base.py

Abstract base class for all game screens.
Specification: screen_flow.md §4
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Screen(ABC):
    """Abstract base class that every game screen must implement.

    Screens are managed by ``ScreenManager`` via a push/pop/replace stack.
    Each concrete screen is responsible for rendering its own content,
    handling input events, and running per-frame logic.
    """

    @abstractmethod
    def on_enter(self, data: dict[str, Any]) -> None:
        """Called when this screen becomes the active (top-of-stack) screen.

        Args:
            data: A dictionary of context data passed by the previous screen
                  or by ``ScreenManager.push()``/``replace()``.
        """

    @abstractmethod
    def on_exit(self) -> dict[str, Any]:
        """Called when this screen is popped from the stack.

        Returns:
            A dictionary of data to pass to the previous screen's
            ``on_enter()`` call.
        """

    @abstractmethod
    def render(self, surface: Any) -> None:
        """Draw this screen onto *surface*.

        Args:
            surface: The target drawing surface (e.g. ``pygame.Surface``).
        """

    @abstractmethod
    def handle_event(self, event: Any) -> None:
        """Process a single input event.

        Args:
            event: A pygame event (or equivalent mock in tests).
        """

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Advance this screen's internal state by *delta_time* seconds.

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

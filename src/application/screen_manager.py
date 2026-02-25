"""
src/application/screen_manager.py

ScreenManager — push/pop/replace stack for game screens.
Specification: screen_flow.md §4
"""
from __future__ import annotations

import logging
from typing import Any

from src.presentation.screens.base import Screen

logger = logging.getLogger(__name__)


class ScreenManager:
    """A LIFO stack of :class:`Screen` objects.

    Only the top-of-stack screen is active at any one time.  Screens are
    notified via ``on_enter`` / ``on_exit`` lifecycle hooks whenever the stack
    changes.
    """

    def __init__(self) -> None:
        """Initialise the manager with an empty screen stack."""
        self._stack: list[Screen] = []

    # ------------------------------------------------------------------
    # Stack operations
    # ------------------------------------------------------------------

    def push(self, screen: Screen, data: dict[str, Any] | None = None) -> None:
        """Push *screen* onto the stack and call its ``on_enter`` hook.

        Args:
            screen: The screen to push.
            data: Optional context data forwarded to ``screen.on_enter()``.
                  Defaults to an empty ``dict`` if ``None``.
        """
        screen.on_enter(data if data is not None else {})
        self._stack.append(screen)

    def pop(self) -> dict[str, Any]:
        """Pop the current screen and restore the previous one.

        The popped screen's ``on_exit()`` return value is passed to the
        previous screen's ``on_enter()`` method.

        Returns:
            The exit data returned by the popped screen.

        Raises:
            IndexError: If the stack is empty.
        """
        if not self._stack:
            raise IndexError("Cannot pop from an empty ScreenManager stack.")
        top = self._stack.pop()
        exit_data = top.on_exit()
        if self._stack:
            self._stack[-1].on_enter(exit_data)
        return exit_data

    def replace(self, screen: Screen, data: dict[str, Any] | None = None) -> None:
        """Replace the current top screen with *screen*.

        The replaced screen's ``on_exit()`` is called (return value discarded).
        The new screen's ``on_enter()`` is called with *data*.

        Args:
            screen: The replacement screen.
            data: Optional context data forwarded to ``screen.on_enter()``.
                  Defaults to an empty ``dict`` if ``None``.
        """
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
        screen.on_enter(data if data is not None else {})
        self._stack.append(screen)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def stack(self) -> list[Screen]:
        """Return a read-only view of the screen stack (bottom → top)."""
        return self._stack

    def current(self) -> Screen:
        """Return the top-of-stack (currently active) screen.

        Raises:
            IndexError: If the stack is empty.
        """
        if not self._stack:
            raise IndexError("ScreenManager stack is empty — no current screen.")
        return self._stack[-1]

    # ------------------------------------------------------------------
    # Delegation helpers (called by GameLoop)
    # ------------------------------------------------------------------

    def render(self, surface: Any) -> None:
        """Delegate ``render`` to the current screen.

        Args:
            surface: The target drawing surface.
        """
        self.current().render(surface)

    def handle_event(self, event: Any) -> None:
        """Delegate ``handle_event`` to the current screen.

        Args:
            event: The input event to process.
        """
        self.current().handle_event(event)

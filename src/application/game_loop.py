"""
src/application/game_loop.py

GameLoop — orchestrates the process_input → update → render cycle.
Specification: system_design.md §3
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

FPS: int = 60


class GameLoop:
    """Drives the main game loop: process_input → update → render.

    The loop is intentionally decoupled from pygame's display module so that
    it can be exercised headlessly in tests.  A ``clock`` abstraction (anything
    with a ``tick(fps)`` method) is injected rather than using
    ``pygame.time.Clock`` directly.
    """

    def __init__(
        self,
        controller: Any,
        renderer: Any,
        clock: Any,
        screen_manager: Any,
        turn_manager: Any | None = None,
    ) -> None:
        """Initialise the game loop with its collaborators.

        Args:
            controller: The ``GameController`` instance.
            renderer: An object with a ``render(state)`` method.
            clock: An object with a ``tick(fps: int)`` method.
            screen_manager: The ``ScreenManager`` instance.
            turn_manager: Optional ``TurnManager``; if ``None`` AI is disabled.
        """
        self._controller = controller
        self._renderer = renderer
        self._clock = clock
        self._screen_manager = screen_manager
        self._turn_manager = turn_manager
        self._running = False

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, max_frames: int | None = None) -> None:
        """Enter the game loop.

        Args:
            max_frames: If given, the loop exits after this many iterations
                (used for headless testing).  ``None`` means run indefinitely
                until a quit event is received.
        """
        self._running = True
        frame_count = 0

        while self._running:
            if max_frames is not None and frame_count >= max_frames:
                break

            self._process_input()
            self._update()
            self._render()
            self._clock.tick(FPS)
            frame_count += 1

    def stop(self) -> None:
        """Signal the loop to exit on the next iteration."""
        self._running = False

    # ------------------------------------------------------------------
    # Per-frame phases
    # ------------------------------------------------------------------

    def _process_input(self) -> None:
        """Poll pending events and forward them to the current screen.

        In headless environments where pygame is unavailable or the display
        is not initialised, ``screen_manager.handle_event`` is called once
        per frame with ``None`` so that per-frame processing still occurs.
        """
        events_processed = False
        try:
            import pygame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                    events_processed = True
                    continue
                self._screen_manager.handle_event(event)
                events_processed = True
        except Exception:  # noqa: S110
            logger.debug("GameLoop: pygame event poll unavailable (headless mode)")

        if not events_processed:
            # Ensure at least one handle_event call per frame in headless mode.
            self._screen_manager.handle_event(None)

    def _update(self) -> None:
        """Advance game state: collect AI results and tick the current screen."""
        if self._turn_manager is not None:
            self._turn_manager.collect_ai_result()
        current_screen = self._screen_manager.current()
        current_screen.update(1.0 / FPS)

    def _render(self) -> None:
        """Render the current frame.

        In graphical (pygame) mode, rendering is screen-driven: the active
        screen draws itself (main menu, setup, playing, etc.) onto the display
        surface and the frame is flipped.  In headless/test environments,
        fall back to the legacy state renderer to preserve existing test
        behavior.
        """
        try:
            import pygame

            surface = pygame.display.get_surface()
            if surface is not None:
                self._screen_manager.render(surface)
                pygame.display.flip()
                return
        except Exception:  # noqa: S110
            logger.debug("GameLoop: pygame display unavailable, using fallback renderer")

        self._renderer.render(self._controller.current_state)

"""
test_playing_screen_rehighlight.py — Unit tests for post-dismissal last-move re-highlight.

Epic: EPIC-8 | User Story: US-808
Covers acceptance criteria: AC-1 through AC-4
Specification: ux-user-journeys-task-popup.md §Journey 3 Opportunities;
               ux-wireframe-playing.md
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.application.event_bus import EventBus
from src.domain.enums import PlayerSide, PlayerType, Rank
from src.domain.piece import Piece, Position

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.screens.playing_screen import PlayingScreen

    _PLAYING_SCREEN_AVAILABLE = True
except ImportError:
    PlayingScreen = None  # type: ignore[assignment, misc]
    _PLAYING_SCREEN_AVAILABLE = False

try:
    from src.domain.army_mod import UnitCustomisation, UnitTask  # type: ignore[attr-defined]

    _UNIT_TASK_AVAILABLE = True
except (ImportError, AttributeError):
    UnitTask = None  # type: ignore[assignment, misc]
    UnitCustomisation = None  # type: ignore[assignment, misc]
    _UNIT_TASK_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _PLAYING_SCREEN_AVAILABLE or not _UNIT_TASK_AVAILABLE,
    reason="PlayingScreen or UnitTask not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Colour constants from the specification
# ---------------------------------------------------------------------------

_COLOUR_MOVE_LAST_FROM = (230, 126, 34)   # #E67E22
_COLOUR_MOVE_LAST_TO = (243, 156, 18)     # #F39C12
_REHIGHLIGHT_DURATION_MS = 2000


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_piece(rank: Rank, owner: PlayerSide) -> Piece:
    return Piece(rank=rank, owner=owner, revealed=False, has_moved=False, position=Position(5, 5))


def _make_controller() -> MagicMock:
    ctrl = MagicMock()
    state = MagicMock()
    state.active_player = PlayerSide.BLUE
    state.turn_number = 14
    red = MagicMock()
    red.player_type = PlayerType.HUMAN
    blue = MagicMock()
    blue.player_type = PlayerType.HUMAN
    state.players = {PlayerSide.RED: red, PlayerSide.BLUE: blue}
    board = MagicMock()
    sq = MagicMock()
    sq.piece = None
    board.get_square.return_value = sq
    state.board = board
    ctrl.current_state = state
    return ctrl


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def playing_screen(event_bus: EventBus) -> object:
    ctrl = _make_controller()
    sm = MagicMock()
    screen = PlayingScreen(  # type: ignore[misc]
        controller=ctrl,
        screen_manager=sm,
        event_bus=event_bus,
        renderer=MagicMock(),
        viewing_player=PlayerSide.RED,
    )
    screen.on_enter({})
    return screen


def _trigger_popup_and_dismiss(screen: object, event_bus: EventBus) -> None:
    """Trigger a combat event with tasks and then call dismiss on the popup."""
    from src.application.events import CombatResolved

    attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
    defender = _make_piece(Rank.MINER, PlayerSide.RED)

    task = UnitTask(description="Do pushups", image_path=None)  # type: ignore[misc]
    customisation = UnitCustomisation(  # type: ignore[misc]
        rank=Rank.LIEUTENANT,
        display_name="Scout Rider",
        display_name_plural="Scout Riders",
        image_paths=(),
        tasks=[task],
    )

    with patch.object(type(screen), "_get_unit_customisation", return_value=customisation, create=True):
        event_bus.publish(
            CombatResolved(
                attacker=attacker,
                defender=defender,
                winner=PlayerSide.BLUE,
            )
        )

    # Dismiss the popup
    if hasattr(screen, "dismiss_popup"):
        screen.dismiss_popup()  # type: ignore[union-attr]
    elif hasattr(screen, "_popup") and screen._popup is not None:  # type: ignore[union-attr]
        screen._popup.dismiss()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-808 AC-1: Re-highlight applied for 2 seconds after popup dismissal
# ---------------------------------------------------------------------------


class TestRehighlightApplied:
    """AC-1: From/To squares are re-highlighted for 2 seconds after popup dismissal."""

    def test_rehighlight_timer_set_after_dismiss(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-1: post_popup_rehighlight_timer is set to ~2000 ms after dismissal."""
        _trigger_popup_and_dismiss(playing_screen, event_bus)
        timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
        assert timer > 0

    def test_rehighlight_timer_is_2000ms(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-1: Timer is exactly 2000 ms."""
        _trigger_popup_and_dismiss(playing_screen, event_bus)
        timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
        assert timer == _REHIGHLIGHT_DURATION_MS

    def test_from_colour_is_orange(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-1: 'From' square colour is COLOUR_MOVE_LAST_FROM #E67E22."""
        assert (
            getattr(playing_screen, "rehighlight_from_colour", None)
            == _COLOUR_MOVE_LAST_FROM
        )

    def test_to_colour_is_yellow(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-1: 'To' square colour is COLOUR_MOVE_LAST_TO #F39C12."""
        assert (
            getattr(playing_screen, "rehighlight_to_colour", None)
            == _COLOUR_MOVE_LAST_TO
        )


# ---------------------------------------------------------------------------
# US-808 AC-2: Highlight fades out after timer expires
# ---------------------------------------------------------------------------


class TestRehighlightExpiry:
    """AC-2: After 2 seconds the highlight is removed (no abrupt disappearance)."""

    def test_timer_decrements_on_update(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-2: Calling update(delta_time_ms=100) decrements the timer by 100."""
        _trigger_popup_and_dismiss(playing_screen, event_bus)
        initial_timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
        assert initial_timer > 0

        if hasattr(playing_screen, "update"):
            playing_screen.update(delta_time_ms=100)  # type: ignore[union-attr]
            new_timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
            assert new_timer < initial_timer

    def test_timer_reaches_zero_after_2000ms(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-2: Timer reaches 0 after update totalling 2000 ms."""
        _trigger_popup_and_dismiss(playing_screen, event_bus)
        if hasattr(playing_screen, "update"):
            playing_screen.update(delta_time_ms=2000)  # type: ignore[union-attr]
            timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
            assert timer <= 0


# ---------------------------------------------------------------------------
# US-808 AC-3: No re-highlight when no popup was shown (normal combat)
# ---------------------------------------------------------------------------


class TestNoRehighlightWithoutPopup:
    """AC-3: No re-highlight when task popup was NOT shown this turn."""

    def test_no_timer_without_popup(self, playing_screen: object, event_bus: EventBus) -> None:
        """AC-3: Normal combat (no tasks) → post_popup_rehighlight_timer stays 0."""
        from src.application.events import CombatResolved

        attacker = _make_piece(Rank.MARSHAL, PlayerSide.BLUE)
        defender = _make_piece(Rank.GENERAL, PlayerSide.RED)

        # Classic army: no tasks
        if UnitCustomisation is not None:
            customisation = UnitCustomisation(  # type: ignore[misc]
                rank=Rank.MARSHAL,
                display_name="Marshal",
                display_name_plural="Marshals",
                image_paths=(),
                tasks=[],
            )
            with patch.object(
                type(playing_screen),
                "_get_unit_customisation",
                return_value=customisation,
                create=True,
            ):
                event_bus.publish(
                    CombatResolved(
                        attacker=attacker,
                        defender=defender,
                        winner=PlayerSide.BLUE,
                    )
                )
        else:
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
            )

        timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
        assert timer == 0


# ---------------------------------------------------------------------------
# US-808 AC-4: New move cancels the re-highlight timer
# ---------------------------------------------------------------------------


class TestRehighlightCancelledOnNewMove:
    """AC-4: A new move cancels the re-highlight timer before it expires."""

    def test_new_move_cancels_timer(
        self, playing_screen: object, event_bus: EventBus
    ) -> None:
        """AC-4: Cancelling re-highlight when player starts a new move."""
        _trigger_popup_and_dismiss(playing_screen, event_bus)

        # Simulate a new move starting — the screen should cancel the timer
        if hasattr(playing_screen, "cancel_rehighlight"):
            playing_screen.cancel_rehighlight()  # type: ignore[union-attr]
            timer = getattr(playing_screen, "post_popup_rehighlight_timer", 0)
            assert timer == 0
        else:
            # If cancel_rehighlight method not yet added, mark as expected failure
            pytest.xfail("cancel_rehighlight method not yet implemented")

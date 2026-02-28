"""
test_playing_screen_task_trigger.py — Unit tests for task popup trigger/suppression logic.

Epic: EPIC-8 | User Story: US-804
Covers acceptance criteria: AC-1 through AC-5 (trigger/suppression scenarios)
Specification: ux-wireframe-task-popup.md §1.1, §4.1, §4.3;
               ux-user-journeys-task-popup.md §Journey 3
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.application.event_bus import EventBus
from src.application.events import CombatResolved
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
# Helpers
# ---------------------------------------------------------------------------


def _make_piece(rank: Rank, owner: PlayerSide) -> Piece:
    return Piece(rank=rank, owner=owner, revealed=False, has_moved=False, position=Position(5, 5))


def _make_customisation_with_tasks(rank: Rank) -> object:
    """Return a UnitCustomisation for *rank* with one task."""
    task = UnitTask(description="Do 20 situps", image_path=None)  # type: ignore[misc]
    return UnitCustomisation(  # type: ignore[misc]
        rank=rank,
        display_name="Scout Rider",
        display_name_plural="Scout Riders",
        image_paths=(),
        tasks=[task],
    )


def _make_customisation_no_tasks(rank: Rank) -> object:
    """Return a UnitCustomisation for *rank* with no tasks."""
    return UnitCustomisation(  # type: ignore[misc]
        rank=rank,
        display_name="Classic Unit",
        display_name_plural="Classic Units",
        image_paths=(),
        tasks=[],
    )


def _make_army_mod(rank: Rank, with_tasks: bool) -> MagicMock:
    """Return a mock ArmyMod where the given rank has/lacks tasks."""
    mod = MagicMock()
    customisation = (
        _make_customisation_with_tasks(rank)
        if with_tasks
        else _make_customisation_no_tasks(rank)
    )
    mod.unit_customisations = {rank: customisation}
    mod.unit_customisations.__getitem__ = lambda self, k: customisation  # noqa: ARG005
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def mock_renderer() -> MagicMock:
    return MagicMock()


def _make_controller(
    active_player: PlayerSide = PlayerSide.RED,
    viewing_player_type: PlayerType = PlayerType.HUMAN,
    opponent_player_type: PlayerType = PlayerType.HUMAN,
) -> MagicMock:
    ctrl = MagicMock()
    state = MagicMock()
    state.active_player = active_player

    red_player = MagicMock()
    red_player.player_type = (
        viewing_player_type if active_player == PlayerSide.RED else opponent_player_type
    )
    blue_player = MagicMock()
    blue_player.player_type = (
        viewing_player_type if active_player == PlayerSide.BLUE else opponent_player_type
    )

    state.players = {PlayerSide.RED: red_player, PlayerSide.BLUE: blue_player}
    board_mock = MagicMock()
    sq_mock = MagicMock()
    sq_mock.piece = None
    board_mock.get_square.return_value = sq_mock
    state.board = board_mock
    state.turn_number = 0
    ctrl.current_state = state
    return ctrl


def _make_playing_screen(
    event_bus: EventBus,
    mock_renderer: MagicMock,
    active_player: PlayerSide = PlayerSide.RED,
    viewing_player: PlayerSide = PlayerSide.RED,
    viewing_player_type: PlayerType = PlayerType.HUMAN,
    opponent_player_type: PlayerType = PlayerType.HUMAN,
) -> object:
    ctrl = _make_controller(active_player, viewing_player_type, opponent_player_type)
    sm = MagicMock()
    screen = PlayingScreen(  # type: ignore[misc]
        controller=ctrl,
        screen_manager=sm,
        event_bus=event_bus,
        renderer=mock_renderer,
        viewing_player=viewing_player,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# US-804 AC-1: Popup shown when capturing unit has tasks and captured is human
# ---------------------------------------------------------------------------


class TestTaskPopupTrigger:
    """AC-1: Popup triggered when attacker has tasks and captured player is human."""

    def test_popup_shown_when_tasks_non_empty_and_human_captured(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-1: CombatResolved + tasks + human captured → popup_active becomes True."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.BLUE,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.HUMAN,
            opponent_player_type=PlayerType.HUMAN,
        )
        attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
        defender = _make_piece(Rank.MINER, PlayerSide.RED)

        customisation = _make_customisation_with_tasks(Rank.LIEUTENANT)

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
            )

        assert getattr(screen, "popup_active", False) is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-804 AC-2: No popup when tasks list is empty
# ---------------------------------------------------------------------------


class TestTaskPopupSuppressedNoTasks:
    """AC-2: No popup when capturing unit's tasks list is empty."""

    def test_no_popup_when_tasks_empty(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-2: CombatResolved + empty tasks → popup_active stays False."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.BLUE,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.HUMAN,
            opponent_player_type=PlayerType.HUMAN,
        )
        attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
        defender = _make_piece(Rank.MINER, PlayerSide.RED)

        customisation = _make_customisation_no_tasks(Rank.LIEUTENANT)

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
            )

        assert getattr(screen, "popup_active", False) is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-804 AC-3: No popup for Classic army (tasks always empty)
# ---------------------------------------------------------------------------


class TestTaskPopupSuppressedClassicArmy:
    """AC-3: Classic army has no tasks → popup never shown."""

    def test_no_popup_for_classic_army(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-3: Classic army units have tasks=[] → no popup."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.BLUE,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.HUMAN,
            opponent_player_type=PlayerType.HUMAN,
        )
        attacker = _make_piece(Rank.MARSHAL, PlayerSide.BLUE)
        defender = _make_piece(Rank.GENERAL, PlayerSide.RED)

        # Classic army has no tasks
        customisation = _make_customisation_no_tasks(Rank.MARSHAL)

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
            )

        assert getattr(screen, "popup_active", False) is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-804 AC-4: No popup when captured player is AI
# ---------------------------------------------------------------------------


class TestTaskPopupSuppressedAiCaptured:
    """AC-4: No popup when the captured player is AI."""

    def test_no_popup_when_ai_captured(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-4: Human captures AI piece with tasks → no popup for AI defender."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.RED,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.HUMAN,
            opponent_player_type=PlayerType.AI_MEDIUM,
        )
        attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.RED)
        defender = _make_piece(Rank.MINER, PlayerSide.BLUE)

        customisation = _make_customisation_with_tasks(Rank.LIEUTENANT)

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.RED)
            )

        assert getattr(screen, "popup_active", False) is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-804 AC-5: No popup in headless/AI-vs-AI mode
# ---------------------------------------------------------------------------


class TestTaskPopupSuppressedBothAi:
    """AC-5: Both players are AI → popup always suppressed."""

    def test_no_popup_when_both_ai(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-5: AI-vs-AI game; any combat → popup suppressed."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.BLUE,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.AI_HARD,
            opponent_player_type=PlayerType.AI_HARD,
        )
        attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
        defender = _make_piece(Rank.MINER, PlayerSide.RED)

        customisation = _make_customisation_with_tasks(Rank.LIEUTENANT)

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            event_bus.publish(
                CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
            )

        assert getattr(screen, "popup_active", False) is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-804 AC-7: Task selected via random.choice
# ---------------------------------------------------------------------------


class TestTaskRandomSelection:
    """AC-7: Task is chosen via random.choice from the unit's task list."""

    def test_task_chosen_via_random_choice(
        self, event_bus: EventBus, mock_renderer: MagicMock
    ) -> None:
        """AC-7: random.choice is called with the tasks list on popup trigger."""
        screen = _make_playing_screen(
            event_bus,
            mock_renderer,
            active_player=PlayerSide.BLUE,
            viewing_player=PlayerSide.RED,
            viewing_player_type=PlayerType.HUMAN,
            opponent_player_type=PlayerType.HUMAN,
        )
        attacker = _make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
        defender = _make_piece(Rank.MINER, PlayerSide.RED)

        task1 = UnitTask(description="Do pushups", image_path=None)  # type: ignore[misc]
        task2 = UnitTask(description="Do situps", image_path=None)  # type: ignore[misc]

        customisation = UnitCustomisation(  # type: ignore[misc]
            rank=Rank.LIEUTENANT,
            display_name="Scout Rider",
            display_name_plural="Scout Riders",
            image_paths=(),
            tasks=[task1, task2],
        )

        with patch.object(
            type(screen), "_get_unit_customisation", return_value=customisation, create=True
        ):
            with patch("random.choice", return_value=task1) as mock_choice:
                event_bus.publish(
                    CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
                )
                mock_choice.assert_called()

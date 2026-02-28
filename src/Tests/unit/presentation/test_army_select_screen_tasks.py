"""
test_army_select_screen_tasks.py — Unit tests for Army Select Screen task notification.

Epic: EPIC-8 | User Story: US-807
Covers acceptance criteria: AC-1 through AC-4
Specification: ux-user-journeys-task-popup.md §Journey 3 Opportunities;
               screen_flow.md §3.3
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.enums import PlayerType, Rank

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.screens.army_select_screen import ArmySelectScreen
    from src.presentation.screens.start_game_screen import (
        GAME_MODE_TWO_PLAYER,
        GAME_MODE_VS_AI,
    )
except ImportError:
    ArmySelectScreen = None  # type: ignore[assignment, misc]
    GAME_MODE_TWO_PLAYER = "TWO_PLAYER"  # type: ignore[assignment]
    GAME_MODE_VS_AI = "VS_AI"  # type: ignore[assignment]

try:
    from src.domain.army_mod import (  # type: ignore[attr-defined]
        ArmyMod,
        UnitCustomisation,
        UnitTask,
    )

    _ARMY_MOD_AVAILABLE = True
except (ImportError, AttributeError):
    ArmyMod = None  # type: ignore[assignment, misc]
    UnitCustomisation = None  # type: ignore[assignment, misc]
    UnitTask = None  # type: ignore[assignment, misc]
    _ARMY_MOD_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    ArmySelectScreen is None or not _ARMY_MOD_AVAILABLE,
    reason="ArmySelectScreen or UnitTask not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TASK_NOTICE_TEXT = "ℹ This army includes unit tasks"
_TOOLTIP_TEXT = (
    "When a unit with tasks captures an enemy piece, you will be asked "
    "to complete a physical exercise before the game continues."
)


def _make_army_mod_with_tasks() -> object:
    """Return a minimal ArmyMod where LIEUTENANT has one task."""
    task = UnitTask(description="Do 20 situps", image_path=None)  # type: ignore[misc]
    customisations = {}
    for rank in Rank:
        tasks = [task] if rank == Rank.LIEUTENANT else []
        customisations[rank] = UnitCustomisation(  # type: ignore[misc]
            rank=rank,
            display_name=rank.name.capitalize(),
            display_name_plural=rank.name.capitalize() + "s",
            image_paths=(),
            tasks=tasks,
        )
    return ArmyMod(  # type: ignore[misc]
        mod_id="fitness_army",
        army_name="Fitness Army",
        unit_customisations=customisations,
    )


def _make_army_mod_no_tasks() -> object:
    """Return a minimal ArmyMod (Classic) where no unit has tasks."""
    customisations = {}
    for rank in Rank:
        customisations[rank] = UnitCustomisation(  # type: ignore[misc]
            rank=rank,
            display_name=rank.name.capitalize(),
            display_name_plural=rank.name.capitalize() + "s",
            image_paths=(),
            tasks=[],
        )
    return ArmyMod(  # type: ignore[misc]
        mod_id="classic",
        army_name="Classic Army",
        unit_customisations=customisations,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    sm = MagicMock()
    sm.push = MagicMock()
    sm.pop = MagicMock()
    sm.replace = MagicMock()
    return sm


@pytest.fixture
def mock_game_context() -> MagicMock:
    ctx = MagicMock()
    ctx.start_new_game = MagicMock()
    return ctx


@pytest.fixture
def army_screen(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    """ArmySelectScreen in VS_AI mode."""
    screen = ArmySelectScreen(  # type: ignore[misc]
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
        game_mode=GAME_MODE_VS_AI,
        ai_difficulty=PlayerType.AI_MEDIUM,
    )
    screen.on_enter({})
    return screen


@pytest.fixture
def army_screen_two_player(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    """ArmySelectScreen in TWO_PLAYER mode."""
    screen = ArmySelectScreen(  # type: ignore[misc]
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
        game_mode=GAME_MODE_TWO_PLAYER,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# US-807 AC-1: Task notice shown when army has tasks
# ---------------------------------------------------------------------------


class TestTaskNoticeShown:
    """AC-1: Task notice shown in preview panel when selected army has tasks."""

    def test_task_notice_visible_for_army_with_tasks(self, army_screen: object) -> None:
        """AC-1: Selecting army with tasks → show_task_notice_player1 is True."""
        army_with_tasks = _make_army_mod_with_tasks()
        army_screen.select_army(player=1, army_mod=army_with_tasks)  # type: ignore[union-attr]
        assert army_screen.show_task_notice_player1 is True  # type: ignore[union-attr]

    def test_task_notice_text_is_correct(self, army_screen: object) -> None:
        """AC-1: task notice text matches the specified wording."""
        army_with_tasks = _make_army_mod_with_tasks()
        army_screen.select_army(player=1, army_mod=army_with_tasks)  # type: ignore[union-attr]
        assert army_screen.task_notice_text == _TASK_NOTICE_TEXT  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-807 AC-2: Task notice not shown for Classic army (no tasks)
# ---------------------------------------------------------------------------


class TestTaskNoticeHiddenClassic:
    """AC-2: Task notice hidden when Classic army (no tasks) is selected."""

    def test_task_notice_hidden_for_classic_army(self, army_screen: object) -> None:
        """AC-2: Selecting Classic army → show_task_notice_player1 is False."""
        classic_army = _make_army_mod_no_tasks()
        army_screen.select_army(player=1, army_mod=classic_army)  # type: ignore[union-attr]
        assert army_screen.show_task_notice_player1 is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-807 AC-3: Tooltip text on notice hover is correct
# ---------------------------------------------------------------------------


class TestTaskNoticeTooltip:
    """AC-3: Hovering the task notice shows the correct tooltip text."""

    def test_tooltip_text_is_correct(self, army_screen: object) -> None:
        """AC-3: task_notice_tooltip matches the specified explanation."""
        assert army_screen.task_notice_tooltip == _TOOLTIP_TEXT  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-807 AC-4: 2-player mode — Player 2 notice is independent of Player 1
# ---------------------------------------------------------------------------


class TestTaskNoticeIndependentPlayers:
    """AC-4: In 2-player mode, Player 2's notice is independent of Player 1's."""

    def test_player2_notice_shown_independently(
        self, army_screen_two_player: object
    ) -> None:
        """AC-4: Player 2 selects army with tasks → show_task_notice_player2 True."""
        army_no_tasks = _make_army_mod_no_tasks()
        army_with_tasks = _make_army_mod_with_tasks()

        army_screen_two_player.select_army(player=1, army_mod=army_no_tasks)  # type: ignore[union-attr]
        army_screen_two_player.select_army(player=2, army_mod=army_with_tasks)  # type: ignore[union-attr]

        assert army_screen_two_player.show_task_notice_player1 is False  # type: ignore[union-attr]
        assert army_screen_two_player.show_task_notice_player2 is True  # type: ignore[union-attr]

    def test_player1_notice_shown_independently(
        self, army_screen_two_player: object
    ) -> None:
        """AC-4: Player 1 selects army with tasks → show_task_notice_player1 True."""
        army_with_tasks = _make_army_mod_with_tasks()
        army_no_tasks = _make_army_mod_no_tasks()

        army_screen_two_player.select_army(player=1, army_mod=army_with_tasks)  # type: ignore[union-attr]
        army_screen_two_player.select_army(player=2, army_mod=army_no_tasks)  # type: ignore[union-attr]

        assert army_screen_two_player.show_task_notice_player1 is True  # type: ignore[union-attr]
        assert army_screen_two_player.show_task_notice_player2 is False  # type: ignore[union-attr]

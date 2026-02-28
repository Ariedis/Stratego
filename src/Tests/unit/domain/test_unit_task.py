"""
test_unit_task.py — Unit tests for UnitTask value object and UnitCustomisation.tasks field.

Epic: EPIC-8 | User Story: US-801
Covers acceptance criteria: AC-1 through AC-5
Specification: data_models.md, ux-wireframe-task-popup.md §7.2–§7.3
"""
from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.domain.army_mod import UnitCustomisation, UnitTask  # type: ignore[attr-defined]

    _UNIT_TASK_AVAILABLE = True
except (ImportError, AttributeError):
    UnitTask = None  # type: ignore[assignment, misc]
    UnitCustomisation = None  # type: ignore[assignment, misc]
    _UNIT_TASK_AVAILABLE = False

try:
    from src.domain.enums import Rank

    _RANK_AVAILABLE = True
except ImportError:
    Rank = None  # type: ignore[assignment, misc]
    _RANK_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _UNIT_TASK_AVAILABLE,
    reason="UnitTask not yet implemented in src.domain.army_mod",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def situps_task() -> object:
    """Return a UnitTask with a description and image_path."""
    return UnitTask(  # type: ignore[misc]
        description="Do 20 situps",
        image_path=Path("mods/fitness_army/images/tasks/situps.gif"),
    )


@pytest.fixture
def no_image_task() -> object:
    """Return a UnitTask with image_path=None."""
    return UnitTask(description="Do 10 pushups", image_path=None)  # type: ignore[misc]


@pytest.fixture
def lieutenant_customisation(situps_task: object) -> object:
    """Return a UnitCustomisation for LIEUTENANT with one task."""
    return UnitCustomisation(  # type: ignore[misc]
        rank=Rank.LIEUTENANT,
        display_name="Scout Rider",
        display_name_plural="Scout Riders",
        image_paths=(),
        tasks=[situps_task],
    )


# ---------------------------------------------------------------------------
# US-801 AC-1: UnitTask constructed with description and image_path
# ---------------------------------------------------------------------------


class TestUnitTaskConstruction:
    """AC-1: UnitTask stores description and image_path correctly."""

    def test_description_stored_correctly(self, situps_task: object) -> None:
        """AC-1: task.description == 'Do 20 situps'."""
        assert situps_task.description == "Do 20 situps"  # type: ignore[union-attr]

    def test_image_path_stored_correctly(self, situps_task: object) -> None:
        """AC-1: task.image_path resolves to the expected Path."""
        expected = Path("mods/fitness_army/images/tasks/situps.gif")
        assert situps_task.image_path == expected  # type: ignore[union-attr]

    def test_image_path_is_path_instance(self, situps_task: object) -> None:
        """AC-1: image_path must be a pathlib.Path."""
        assert isinstance(situps_task.image_path, Path)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-801 AC-2: UnitTask with image_path=None
# ---------------------------------------------------------------------------


class TestUnitTaskNoImage:
    """AC-2: UnitTask with image_path=None raises no error; returns None."""

    def test_none_image_path_accepted(self, no_image_task: object) -> None:
        """AC-2: Constructing UnitTask with image_path=None does not raise."""
        assert no_image_task is not None

    def test_none_image_path_returns_none(self, no_image_task: object) -> None:
        """AC-2: task.image_path is None when constructed with None."""
        assert no_image_task.image_path is None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-801 AC-3: UnitCustomisation.tasks defaults to empty list
# ---------------------------------------------------------------------------


class TestUnitCustomisationDefaultTasks:
    """AC-3: UnitCustomisation.tasks defaults to an empty list (not None)."""

    def test_tasks_defaults_to_empty_list(self) -> None:
        """AC-3: tasks not provided → unit_customisation.tasks == []."""
        customisation = UnitCustomisation(  # type: ignore[misc]
            rank=Rank.CAPTAIN,
            display_name="Officer",
            display_name_plural="Officers",
            image_paths=(),
        )
        assert customisation.tasks == []  # type: ignore[union-attr]

    def test_tasks_is_not_none_when_omitted(self) -> None:
        """AC-3: tasks attribute is never None when not provided."""
        customisation = UnitCustomisation(  # type: ignore[misc]
            rank=Rank.SERGEANT,
            display_name="Soldier",
            display_name_plural="Soldiers",
            image_paths=(),
        )
        assert customisation.tasks is not None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-801 AC-4: UnitCustomisation.tasks preserves order
# ---------------------------------------------------------------------------


class TestUnitCustomisationTasksOrder:
    """AC-4: UnitCustomisation.tasks preserves the order of provided tasks."""

    def test_two_tasks_both_present(self) -> None:
        """AC-4: Two tasks provided → both tasks present in .tasks."""
        task1 = UnitTask(description="Do 10 pushups", image_path=None)  # type: ignore[misc]
        task2 = UnitTask(description="Do 20 situps", image_path=None)  # type: ignore[misc]
        customisation = UnitCustomisation(  # type: ignore[misc]
            rank=Rank.LIEUTENANT,
            display_name="Scout Rider",
            display_name_plural="Scout Riders",
            image_paths=(),
            tasks=[task1, task2],
        )
        assert len(customisation.tasks) == 2  # type: ignore[union-attr]

    def test_task_order_preserved(self) -> None:
        """AC-4: Order of tasks is preserved (first in, first out)."""
        task1 = UnitTask(description="First task", image_path=None)  # type: ignore[misc]
        task2 = UnitTask(description="Second task", image_path=None)  # type: ignore[misc]
        customisation = UnitCustomisation(  # type: ignore[misc]
            rank=Rank.MINER,
            display_name="Sapper",
            display_name_plural="Sappers",
            image_paths=(),
            tasks=[task1, task2],
        )
        assert customisation.tasks[0].description == "First task"  # type: ignore[union-attr]
        assert customisation.tasks[1].description == "Second task"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-801 AC-5: UnitTask is immutable (frozen)
# ---------------------------------------------------------------------------


class TestUnitTaskImmutability:
    """AC-5: UnitTask is a frozen value object; mutation raises an error."""

    def test_mutating_description_raises(self, situps_task: object) -> None:
        """AC-5: Assigning to task.description must raise FrozenInstanceError."""
        with pytest.raises(Exception):  # FrozenInstanceError is a subclass of AttributeError
            situps_task.description = "Do 30 burpees"  # type: ignore[union-attr]

    def test_mutating_image_path_raises(self, situps_task: object) -> None:
        """AC-5: Assigning to task.image_path must raise FrozenInstanceError."""
        with pytest.raises(Exception):
            situps_task.image_path = Path("other/path.gif")  # type: ignore[union-attr]

    def test_unit_task_is_hashable(self, situps_task: object) -> None:
        """AC-5 (corollary): A frozen dataclass must be hashable."""
        task_set = {situps_task}
        assert len(task_set) == 1

    def test_unit_task_equality_by_value(self) -> None:
        """AC-5 (corollary): Two UnitTask instances with same fields are equal."""
        t1 = UnitTask(description="Do 20 situps", image_path=Path("a/b.gif"))  # type: ignore[misc]
        t2 = UnitTask(description="Do 20 situps", image_path=Path("a/b.gif"))  # type: ignore[misc]
        assert t1 == t2

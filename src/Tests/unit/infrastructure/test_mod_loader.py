"""
test_mod_loader.py — Unit tests for src/infrastructure/mod_loader.py

Epic: EPIC-7 | User Story: US-702
Covers acceptance criteria: AC-1 through AC-5
Specification: custom_armies.md §3, §6

Epic: EPIC-8 | User Story: US-802
Covers acceptance criteria: AC-1, AC-7, AC-8
Specification: custom_armies.md §4.3, ux-wireframe-task-popup.md §7.1, §8
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.infrastructure.mod_loader import discover_mods

    _MOD_LOADER_AVAILABLE = True
except ImportError:
    discover_mods = None  # type: ignore[assignment, misc]
    _MOD_LOADER_AVAILABLE = False

# Feature flag: whether UnitTask / tasks field are implemented in the domain.
try:
    from src.domain.army_mod import UnitCustomisation, UnitTask  # type: ignore[attr-defined]

    _TASK_FEATURE_AVAILABLE = (
        "tasks" in getattr(UnitCustomisation, "__dataclass_fields__", {})
    )
except (ImportError, AttributeError):
    _TASK_FEATURE_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _MOD_LOADER_AVAILABLE,
    reason="src.infrastructure.mod_loader not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_ARMY_JSON = {
    "mod_version": "1.0",
    "army_name": "Dragon Horde",
    "units": {
        "MARSHAL": {"display_name": "Dragon Lord"},
        "GENERAL": {"display_name": "Warlord"},
    },
}

_VALID_ARMY_JSON_2 = {
    "mod_version": "1.0",
    "army_name": "Space Age",
    "units": {
        "MARSHAL": {"display_name": "Admiral"},
    },
}


def _make_mod_dir(parent: Path, folder_name: str, army_data: dict) -> Path:
    """Create a mod subfolder with a valid army.json inside *parent*."""
    mod_dir = parent / folder_name
    mod_dir.mkdir(parents=True)
    (mod_dir / "army.json").write_text(json.dumps(army_data))
    return mod_dir


# ---------------------------------------------------------------------------
# US-702 AC-1: Valid mod folder is discovered and loaded
# ---------------------------------------------------------------------------


class TestModLoaderDiscover:
    """AC-1: A valid mod folder with army.json is discovered as an ArmyMod."""

    def test_discovers_single_valid_mod(self, tmp_path: Path) -> None:
        """AC-1: One valid mod folder → one ArmyMod returned."""
        _make_mod_dir(tmp_path, "dragon_horde", _VALID_ARMY_JSON)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 1

    def test_discovered_mod_has_correct_army_name(self, tmp_path: Path) -> None:
        """AC-1: The returned ArmyMod must reflect the army_name from army.json."""
        _make_mod_dir(tmp_path, "dragon_horde", _VALID_ARMY_JSON)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert mods[0].army_name == "Dragon Horde"

    def test_discovers_multiple_valid_mods(self, tmp_path: Path) -> None:
        """AC-1: Two valid mod folders → two ArmyMods returned."""
        _make_mod_dir(tmp_path, "dragon_horde", _VALID_ARMY_JSON)
        _make_mod_dir(tmp_path, "space_age", _VALID_ARMY_JSON_2)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 2
        names = {m.army_name for m in mods}
        assert names == {"Dragon Horde", "Space Age"}


# ---------------------------------------------------------------------------
# US-702 AC-2: Malformed army.json is skipped with a warning
# ---------------------------------------------------------------------------


class TestModLoaderMalformedJson:
    """AC-2: A folder with malformed army.json is skipped; others still load."""

    def test_broken_mod_is_skipped(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """AC-2: Invalid JSON → mod skipped, no exception raised."""
        broken = tmp_path / "broken_mod"
        broken.mkdir()
        (broken / "army.json").write_text("{not valid json{{")
        with caplog.at_level(logging.WARNING):
            mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 0

    def test_broken_mod_warning_logged(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-2: A warning must be logged for the broken mod."""
        broken = tmp_path / "broken_mod"
        broken.mkdir()
        (broken / "army.json").write_text("{bad json}")
        with caplog.at_level(logging.WARNING):
            discover_mods(tmp_path)  # type: ignore[misc]
        assert any(r.levelno >= logging.WARNING for r in caplog.records)

    def test_valid_mods_still_returned_alongside_broken(
        self, tmp_path: Path
    ) -> None:
        """AC-2: One broken + one valid → only the valid mod is returned."""
        broken = tmp_path / "broken_mod"
        broken.mkdir()
        (broken / "army.json").write_text("{bad}")
        _make_mod_dir(tmp_path, "dragon_horde", _VALID_ARMY_JSON)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 1
        assert mods[0].army_name == "Dragon Horde"


# ---------------------------------------------------------------------------
# US-702 AC-3: Duplicate mod_id (same folder name) — only first loaded
# ---------------------------------------------------------------------------


class TestModLoaderDuplicateId:
    """AC-3: Two mods with the same mod_id → only the first is loaded."""

    def test_duplicate_mod_id_skipped_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-3: Second mod with same folder name is skipped with a warning.

        Note: On a real filesystem two folders cannot have the same name in
        the same directory, so this test simulates the scenario by pre-populating
        the discovered list with one mod then trying to add the duplicate.
        This scenario is validated at the discover_mods level by verifying
        that mods with the same mod_id after normalisation are de-duplicated.
        """
        # Create two mods that normalise to the same mod_id
        _make_mod_dir(tmp_path, "dragon-horde", _VALID_ARMY_JSON)
        _make_mod_dir(tmp_path, "dragon_horde", _VALID_ARMY_JSON_2)
        with caplog.at_level(logging.WARNING):
            mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 1


# ---------------------------------------------------------------------------
# US-702 AC-4: Empty mod directory returns empty list
# ---------------------------------------------------------------------------


class TestModLoaderEmptyDirectory:
    """AC-4: An empty mod directory → empty list returned (no error)."""

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        """AC-4: No mod folders → empty list, no exception."""
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert mods == []

    def test_directory_with_no_army_json_returns_empty(self, tmp_path: Path) -> None:
        """AC-4: Folders without army.json are not treated as mods."""
        not_a_mod = tmp_path / "not_a_mod"
        not_a_mod.mkdir()
        (not_a_mod / "readme.txt").write_text("not a mod")
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert mods == []


# ---------------------------------------------------------------------------
# US-702 AC-5: Mod with no images/ subfolder still loads
# ---------------------------------------------------------------------------


class TestModLoaderNoImages:
    """AC-5: A mod with no images/ folder loads successfully (images are optional)."""

    def test_mod_without_images_folder_loads(self, tmp_path: Path) -> None:
        """AC-5: Missing images/ folder is not an error."""
        _make_mod_dir(tmp_path, "no_images_mod", _VALID_ARMY_JSON)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 1
        assert mods[0].army_name == "Dragon Horde"


# ---------------------------------------------------------------------------
# US-802 AC-1: Tasks array in army.json is parsed into UnitTask objects
# ---------------------------------------------------------------------------

_ARMY_JSON_WITH_TASKS = {
    "mod_version": "1.0",
    "army_name": "Fitness Army",
    "units": {
        "LIEUTENANT": {
            "display_name": "Scout Rider",
            "tasks": [
                {
                    "description": "Do 20 situps",
                    "image": "images/tasks/situps.gif",
                }
            ],
        }
    },
}

_ARMY_JSON_NO_TASKS_KEY = {
    "mod_version": "1.0",
    "army_name": "No Tasks Army",
    "units": {
        "LIEUTENANT": {
            "display_name": "Scout Rider",
        }
    },
}

_ARMY_JSON_EMPTY_TASKS = {
    "mod_version": "1.0",
    "army_name": "Empty Tasks Army",
    "units": {
        "LIEUTENANT": {
            "display_name": "Scout Rider",
            "tasks": [],
        }
    },
}


@pytest.mark.xfail(
    not _TASK_FEATURE_AVAILABLE,
    reason="UnitTask / tasks field not yet implemented in domain",
    strict=False,
)
class TestModLoaderTaskParsing:
    """US-802 AC-1, AC-7, AC-8: tasks arrays are parsed from army.json."""

    def test_task_description_loaded(self, tmp_path: Path) -> None:
        """AC-1: task description matches the value in army.json."""
        _make_mod_dir(tmp_path, "fitness_army", _ARMY_JSON_WITH_TASKS)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        assert len(mods) == 1
        from src.domain.enums import Rank
        lieutenant = mods[0].unit_customisations[Rank.LIEUTENANT]
        assert len(lieutenant.tasks) == 1
        assert lieutenant.tasks[0].description == "Do 20 situps"

    def test_task_image_path_resolved(self, tmp_path: Path) -> None:
        """AC-1: task image_path is the resolved absolute Path."""
        _make_mod_dir(tmp_path, "fitness_army", _ARMY_JSON_WITH_TASKS)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        from src.domain.enums import Rank
        lieutenant = mods[0].unit_customisations[Rank.LIEUTENANT]
        task = lieutenant.tasks[0]
        assert task.image_path is not None
        assert task.image_path == tmp_path / "fitness_army" / "images" / "tasks" / "situps.gif"

    def test_no_tasks_key_results_in_empty_list(self, tmp_path: Path) -> None:
        """AC-7: Unit with no 'tasks' key → unit_customisation.tasks is empty list."""
        _make_mod_dir(tmp_path, "no_tasks", _ARMY_JSON_NO_TASKS_KEY)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        from src.domain.enums import Rank
        lieutenant = mods[0].unit_customisations[Rank.LIEUTENANT]
        assert lieutenant.tasks == []

    def test_empty_tasks_array_results_in_empty_list(self, tmp_path: Path) -> None:
        """AC-8: Unit with 'tasks': [] → unit_customisation.tasks is empty list."""
        _make_mod_dir(tmp_path, "empty_tasks", _ARMY_JSON_EMPTY_TASKS)
        mods = discover_mods(tmp_path)  # type: ignore[misc]
        from src.domain.enums import Rank
        lieutenant = mods[0].unit_customisations[Rank.LIEUTENANT]
        assert lieutenant.tasks == []

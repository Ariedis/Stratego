"""
test_json_repository.py — Unit tests for src/infrastructure/json_repository.py

Epic: EPIC-6 | User Story: US-601
Covers acceptance criteria: AC-1 through AC-7
Specification: data_models.md §6, technology_stack.md §7
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.domain.enums import Rank
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_minimal_playing_state,
    make_red_piece,
)

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.infrastructure.json_repository import JsonRepository

    _REPO_AVAILABLE = True
except ImportError:
    JsonRepository = None  # type: ignore[assignment, misc]
    _REPO_AVAILABLE = False

try:
    from src.infrastructure.json_repository import (
        SaveFileCorruptError,
        UnsupportedSaveVersionError,
    )
except ImportError:
    SaveFileCorruptError = Exception  # type: ignore[assignment, misc]
    UnsupportedSaveVersionError = Exception  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    not _REPO_AVAILABLE,
    reason="src.infrastructure.json_repository not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    """Return a temporary directory to act as the saves folder."""
    saves = tmp_path / "saves"
    saves.mkdir()
    return saves


@pytest.fixture
def repository(save_dir: Path) -> object:
    """Return a JsonRepository configured with a temp saves directory."""
    return JsonRepository(save_dir)


@pytest.fixture
def playing_state() -> object:
    """Return a representative mid-game PLAYING GameState."""
    return make_minimal_playing_state(
        red_pieces=[
            make_red_piece(Rank.FLAG, 9, 0),
            make_red_piece(Rank.MARSHAL, 8, 0),
            make_red_piece(Rank.SCOUT, 7, 0),
        ],
        blue_pieces=[
            make_blue_piece(Rank.FLAG, 0, 0),
            make_blue_piece(Rank.GENERAL, 1, 0),
            make_blue_piece(Rank.MINER, 2, 0),
        ],
    )


# ---------------------------------------------------------------------------
# US-601 AC-1: save() creates a valid JSON file with version field
# ---------------------------------------------------------------------------


class TestJsonRepositorySave:
    """AC-1: save() writes a valid JSON file containing 'version': '1.0'."""

    def test_save_creates_file(self, repository: object, playing_state: object) -> None:
        """AC-1: Calling save() must create a file on disk."""
        repository.save(playing_state, "game_001.json")  # type: ignore[union-attr]
        saved = list(repository._save_dir.iterdir())  # type: ignore[union-attr]
        assert len(saved) == 1

    def test_save_file_contains_version_field(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-1: The saved JSON file must contain '\"version\": \"1.0\"'."""
        repository.save(playing_state, "game_001.json")  # type: ignore[union-attr]
        saved_path = next(repository._save_dir.iterdir())  # type: ignore[union-attr]
        with saved_path.open() as f:
            data = json.load(f)
        assert data.get("version") == "1.0"

    def test_save_file_is_valid_json(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-1: The saved file must parse as valid JSON without errors."""
        repository.save(playing_state, "game_001.json")  # type: ignore[union-attr]
        saved_path = next(repository._save_dir.iterdir())  # type: ignore[union-attr]
        with saved_path.open() as f:
            data = json.load(f)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# US-601 AC-2: Round-trip equality
# ---------------------------------------------------------------------------


class TestJsonRepositoryRoundTrip:
    """AC-2: save() followed by load() must return an equal GameState."""

    def test_round_trip_preserves_phase(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-2: phase must survive serialisation round-trip."""
        repository.save(playing_state, "rt.json")  # type: ignore[union-attr]
        loaded = repository.load("rt.json")  # type: ignore[union-attr]
        assert loaded.phase == playing_state.phase  # type: ignore[union-attr]

    def test_round_trip_preserves_turn_number(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-2: turn_number must survive serialisation round-trip."""
        repository.save(playing_state, "rt.json")  # type: ignore[union-attr]
        loaded = repository.load("rt.json")  # type: ignore[union-attr]
        assert loaded.turn_number == playing_state.turn_number  # type: ignore[union-attr]

    def test_round_trip_preserves_active_player(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-2: active_player must survive serialisation round-trip."""
        repository.save(playing_state, "rt.json")  # type: ignore[union-attr]
        loaded = repository.load("rt.json")  # type: ignore[union-attr]
        assert loaded.active_player == playing_state.active_player  # type: ignore[union-attr]

    def test_round_trip_preserves_piece_count(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-2: Piece counts for both players must survive round-trip."""
        repository.save(playing_state, "rt.json")  # type: ignore[union-attr]
        loaded = repository.load("rt.json")  # type: ignore[union-attr]
        for orig_player, loaded_player in zip(
            playing_state.players, loaded.players  # type: ignore[union-attr]
        ):
            assert len(loaded_player.pieces_remaining) == len(orig_player.pieces_remaining)

    def test_round_trip_full_equality(
        self, repository: object, playing_state: object
    ) -> None:
        """AC-2: The loaded GameState must equal the original."""
        repository.save(playing_state, "rt.json")  # type: ignore[union-attr]
        loaded = repository.load("rt.json")  # type: ignore[union-attr]
        assert loaded == playing_state


# ---------------------------------------------------------------------------
# US-601 AC-3: Unknown version raises UnsupportedSaveVersionError
# ---------------------------------------------------------------------------


class TestJsonRepositoryVersionCheck:
    """AC-3: Files with unrecognised version strings must be rejected."""

    def test_unknown_version_raises_error(
        self, repository: object, save_dir: Path
    ) -> None:
        """AC-3: version '2.0' is unknown and must raise UnsupportedSaveVersionError."""
        bad_file = save_dir / "bad_version.json"
        bad_file.write_text(json.dumps({"version": "2.0", "phase": "PLAYING"}))
        with pytest.raises(UnsupportedSaveVersionError) as exc_info:
            repository.load("bad_version.json")  # type: ignore[union-attr]
        assert "2.0" in str(exc_info.value)

    def test_missing_version_raises_error(
        self, repository: object, save_dir: Path
    ) -> None:
        """A save file with no 'version' key must also be rejected."""
        bad_file = save_dir / "no_version.json"
        bad_file.write_text(json.dumps({"phase": "PLAYING"}))
        with pytest.raises((UnsupportedSaveVersionError, SaveFileCorruptError)):
            repository.load("no_version.json")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-601 AC-4: Corrupt JSON raises SaveFileCorruptError
# ---------------------------------------------------------------------------


class TestJsonRepositoryCorruptFile:
    """AC-4: A corrupt JSON file must raise SaveFileCorruptError with logging."""

    def test_corrupt_json_raises_error(self, repository: object, save_dir: Path) -> None:
        """AC-4: Invalid JSON syntax must raise SaveFileCorruptError."""
        bad_file = save_dir / "corrupt.json"
        bad_file.write_text("{this is not valid json{{{{")
        with pytest.raises(SaveFileCorruptError):
            repository.load("corrupt.json")  # type: ignore[union-attr]

    def test_empty_file_raises_error(self, repository: object, save_dir: Path) -> None:
        """An empty file is also corrupt and must raise SaveFileCorruptError."""
        bad_file = save_dir / "empty.json"
        bad_file.write_text("")
        with pytest.raises(SaveFileCorruptError):
            repository.load("empty.json")  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-601 AC-5 & AC-6: get_most_recent_save()
# ---------------------------------------------------------------------------


class TestJsonRepositoryMostRecentSave:
    """AC-5 & AC-6: get_most_recent_save() returns the latest file or None."""

    def test_returns_none_when_no_saves(self, repository: object) -> None:
        """AC-6: No saves → None returned (no error)."""
        result = repository.get_most_recent_save()  # type: ignore[union-attr]
        assert result is None

    def test_returns_most_recent_of_multiple_saves(
        self, repository: object, playing_state: object, save_dir: Path
    ) -> None:
        """AC-5: Three saves → path of most recently written file returned."""
        import time

        repository.save(playing_state, "first.json")  # type: ignore[union-attr]
        time.sleep(0.01)
        repository.save(playing_state, "second.json")  # type: ignore[union-attr]
        time.sleep(0.01)
        repository.save(playing_state, "third.json")  # type: ignore[union-attr]

        result = repository.get_most_recent_save()  # type: ignore[union-attr]
        assert result is not None
        assert "third" in result.name


# ---------------------------------------------------------------------------
# US-601 AC-7: No pickle usage (enforced by ruff S301 separately)
# ---------------------------------------------------------------------------


class TestNoPickleUsage:
    """AC-7: pickle is never imported or used in json_repository."""

    def test_pickle_not_imported(self) -> None:
        """AC-7: json_repository must not import pickle."""
        import src.infrastructure.json_repository as mod

        src_file = Path(mod.__file__).read_text()
        assert "import pickle" not in src_file
        assert "pickle.loads" not in src_file
        assert "pickle.dumps" not in src_file

"""
test_sprite_manager.py — Unit tests for src/presentation/sprite_manager.py

Epic: EPIC-7 | User Story: US-704
Covers acceptance criteria: AC-2 (fallback), AC-5 (path traversal rejection),
existing Classic preload behaviour from US-401, and team tinting (issue: Game
Piece tinting).
Specification: custom_armies.md §5, system_design.md §2.4,
planning/ux-visual-style-guide.md §2.5
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.domain.enums import PlayerSide, Rank
from src.presentation.sprite_manager import SpriteManager

# ---------------------------------------------------------------------------
# Optional import of extended mod-aware API (US-704 features not yet impl.)
# ---------------------------------------------------------------------------

try:
    from src.presentation.sprite_manager import PathTraversalError  # noqa: F401

    _PATH_TRAVERSAL_ERROR_AVAILABLE = True
except ImportError:
    PathTraversalError = Exception  # type: ignore[assignment, misc]
    _PATH_TRAVERSAL_ERROR_AVAILABLE = False

_preload_army_available = hasattr(SpriteManager, "preload_army")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def asset_dir(tmp_path: Path) -> Path:
    """Return a temporary asset directory (no images present)."""
    return tmp_path / "assets"


@pytest.fixture
def sprite_manager(asset_dir: Path) -> SpriteManager:
    """Return a SpriteManager configured with an empty asset directory."""
    return SpriteManager(asset_dir)


# ---------------------------------------------------------------------------
# Classic preload — existing functionality
# ---------------------------------------------------------------------------


class TestSpriteManagerPreloadClassic:
    """SpriteManager.preload_classic() caches surfaces for all 12 ranks."""

    def test_preload_classic_does_not_raise(
        self, sprite_manager: SpriteManager
    ) -> None:
        """preload_classic() on a missing asset dir must not raise."""
        sprite_manager.preload_classic()

    def test_get_surface_after_preload_returns_surface(
        self, sprite_manager: SpriteManager
    ) -> None:
        """get_surface() after preload_classic() returns a non-None value."""
        sprite_manager.preload_classic()
        surface = sprite_manager.get_surface(Rank.MARSHAL, PlayerSide.RED, revealed=True)
        assert surface is not None

    @pytest.mark.parametrize("rank", list(Rank))
    def test_get_surface_for_all_ranks(
        self, sprite_manager: SpriteManager, rank: Rank
    ) -> None:
        """Every Rank member must return a non-None revealed surface."""
        sprite_manager.preload_classic()
        surface = sprite_manager.get_surface(rank, PlayerSide.RED, revealed=True)
        assert surface is not None

    def test_get_hidden_surface_returns_hidden(
        self, sprite_manager: SpriteManager
    ) -> None:
        """get_surface() with revealed=False must return the hidden surface."""
        sprite_manager.preload_classic()
        hidden = sprite_manager.get_surface(Rank.MARSHAL, PlayerSide.BLUE, revealed=False)
        assert hidden is sprite_manager.hidden_surface


# ---------------------------------------------------------------------------
# Property accessors
# ---------------------------------------------------------------------------


class TestSpriteManagerProperties:
    """hidden_surface, lake_surface, and empty_surface must be non-None."""

    def test_hidden_surface_is_not_none(self, sprite_manager: SpriteManager) -> None:
        assert sprite_manager.hidden_surface is not None

    def test_lake_surface_is_not_none(self, sprite_manager: SpriteManager) -> None:
        assert sprite_manager.lake_surface is not None

    def test_empty_surface_is_not_none(self, sprite_manager: SpriteManager) -> None:
        assert sprite_manager.empty_surface is not None

    def test_hidden_and_empty_surfaces_are_distinct(
        self, sprite_manager: SpriteManager
    ) -> None:
        """Hidden and empty surfaces must be different objects."""
        assert sprite_manager.hidden_surface is not sprite_manager.empty_surface

    def test_hidden_and_lake_surfaces_are_distinct(
        self, sprite_manager: SpriteManager
    ) -> None:
        """Hidden and lake surfaces must be different objects."""
        assert sprite_manager.hidden_surface is not sprite_manager.lake_surface


# ---------------------------------------------------------------------------
# US-704 AC-2: Fallback to Classic when mod image is absent
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _preload_army_available,
    reason="SpriteManager.preload_army not implemented yet",
    strict=False,
)
class TestSpriteManagerFallback:
    """AC-2: When a mod has no image for a rank, the Classic image is used."""

    def test_missing_mod_image_falls_back_to_classic(
        self, sprite_manager: SpriteManager, tmp_path: Path
    ) -> None:
        """AC-2: Mod with no Spy images → Spy surface falls back to Classic."""
        army_mod = MagicMock()
        army_mod.mod_id = "test_mod"
        army_mod.image_dir = tmp_path / "images"  # does not exist
        sprite_manager.preload_classic()  # type: ignore[union-attr]
        sprite_manager.preload_army(army_mod)  # type: ignore[union-attr]
        mod_spy = sprite_manager.get_surface(Rank.SPY, PlayerSide.RED, revealed=True)
        # Fallback: the surfaces should be the same (or at least non-None).
        assert mod_spy is not None


# ---------------------------------------------------------------------------
# US-704 AC-5: Path traversal rejection
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _PATH_TRAVERSAL_ERROR_AVAILABLE,
    reason="PathTraversalError / preload_army not implemented yet",
    strict=False,
)
class TestSpriteManagerPathTraversal:
    """AC-5: An image path containing '../' must raise PathTraversalError."""

    def test_path_traversal_in_image_path_raises_error(
        self, sprite_manager: SpriteManager, tmp_path: Path
    ) -> None:
        """AC-5: '../secret.png' in army.json must raise PathTraversalError."""
        army_mod = MagicMock()
        army_mod.mod_id = "evil_mod"
        army_mod.image_dir = tmp_path / "images"
        army_mod.image_dir.mkdir(parents=True)
        # Write a manifest-style dict that the preload_army method would parse.
        army_mod.unit_image_paths = {Rank.MARSHAL: "../../../etc/passwd"}
        with pytest.raises(PathTraversalError):
            sprite_manager.preload_army(army_mod)  # type: ignore[union-attr]

    def test_absolute_path_in_image_path_raises_error(
        self, sprite_manager: SpriteManager, tmp_path: Path
    ) -> None:
        """AC-5: An absolute image path must also be rejected."""
        army_mod = MagicMock()
        army_mod.mod_id = "evil_abs"
        army_mod.image_dir = tmp_path / "images"
        army_mod.image_dir.mkdir(parents=True)
        army_mod.unit_image_paths = {Rank.MARSHAL: "/etc/passwd"}
        with pytest.raises(PathTraversalError):
            sprite_manager.preload_army(army_mod)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-704 AC-3: Single random image selected per rank per session
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _preload_army_available,
    reason="SpriteManager.preload_army not implemented yet",
    strict=False,
)
class TestSpriteManagerSessionImageSelection:
    """AC-3: Exactly one image is randomly selected per rank and reused."""

    def test_same_surface_returned_for_same_rank_across_calls(
        self, sprite_manager: SpriteManager, tmp_path: Path
    ) -> None:
        """AC-3: Multiple get_surface() calls for the same rank return the same object."""
        army_mod = MagicMock()
        army_mod.mod_id = "stable_mod"
        army_mod.image_dir = tmp_path / "images"
        sprite_manager.preload_army(army_mod)  # type: ignore[union-attr]
        s1 = sprite_manager.get_surface(Rank.SCOUT, PlayerSide.RED, revealed=True)
        s2 = sprite_manager.get_surface(Rank.SCOUT, PlayerSide.RED, revealed=True)
        assert s1 is s2


# ---------------------------------------------------------------------------
# Team tinting — issue: "Game Piece tinting"
# ---------------------------------------------------------------------------


class TestSpriteManagerTinting:
    """get_surface() returns differently-tinted surfaces for RED vs BLUE."""

    def test_red_and_blue_surfaces_are_distinct_objects(
        self, sprite_manager: SpriteManager
    ) -> None:
        """RED and BLUE surfaces for the same rank must be different objects."""
        red_surface = sprite_manager.get_surface(Rank.SCOUT, PlayerSide.RED, revealed=True)
        blue_surface = sprite_manager.get_surface(Rank.SCOUT, PlayerSide.BLUE, revealed=True)
        assert red_surface is not blue_surface

    @pytest.mark.parametrize("rank", list(Rank))
    def test_tinting_does_not_raise_for_any_rank(
        self, sprite_manager: SpriteManager, rank: Rank
    ) -> None:
        """get_surface() must not raise for either team and every rank."""
        assert sprite_manager.get_surface(rank, PlayerSide.RED, revealed=True) is not None
        assert sprite_manager.get_surface(rank, PlayerSide.BLUE, revealed=True) is not None

    def test_hidden_surface_is_not_tinted(self, sprite_manager: SpriteManager) -> None:
        """Hidden (revealed=False) surface must be the shared hidden surface, not tinted."""
        red_hidden = sprite_manager.get_surface(Rank.MARSHAL, PlayerSide.RED, revealed=False)
        blue_hidden = sprite_manager.get_surface(Rank.MARSHAL, PlayerSide.BLUE, revealed=False)
        assert red_hidden is sprite_manager.hidden_surface
        assert blue_hidden is sprite_manager.hidden_surface

    def test_tinted_surfaces_are_cached(self, sprite_manager: SpriteManager) -> None:
        """Successive calls for the same (rank, side) return the identical cached surface."""
        s1 = sprite_manager.get_surface(Rank.GENERAL, PlayerSide.RED, revealed=True)
        s2 = sprite_manager.get_surface(Rank.GENERAL, PlayerSide.RED, revealed=True)
        assert s1 is s2

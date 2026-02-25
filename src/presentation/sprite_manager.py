"""
src/presentation/sprite_manager.py

SpriteManager — loads and caches piece surface images for the pygame renderer.
Specification: system_design.md §2.4, custom_armies.md §5
"""
from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.domain.enums import PlayerSide, Rank

if TYPE_CHECKING:
    from src.domain.army_mod import ArmyMod, UnitCustomisation


class PathTraversalError(Exception):
    """Raised when an image path in a mod manifest attempts a path traversal.

    Path traversal attacks use sequences like ``../`` or absolute paths to
    escape the mod's own ``images/`` directory.  All such paths are rejected
    before any filesystem access.

    Specification: custom_armies.md §10
    """

logger = logging.getLogger(__name__)

# Lazy import of pygame so that the module can be imported in headless tests
# without a running display.
try:
    import pygame as _pygame

    _PYGAME_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYGAME_AVAILABLE = False

# Solid-colour placeholders used when real asset images are not found.
_RANK_COLOURS: dict[Rank, tuple[int, int, int]] = {
    Rank.FLAG: (255, 215, 0),
    Rank.SPY: (128, 0, 128),
    Rank.SCOUT: (0, 128, 255),
    Rank.MINER: (139, 90, 43),
    Rank.SERGEANT: (70, 130, 180),
    Rank.LIEUTENANT: (60, 179, 113),
    Rank.CAPTAIN: (255, 165, 0),
    Rank.MAJOR: (220, 20, 60),
    Rank.COLONEL: (105, 105, 105),
    Rank.GENERAL: (0, 0, 205),
    Rank.MARSHAL: (0, 0, 0),
    Rank.BOMB: (50, 50, 50),
}


class _MockSurface:
    """Minimal surface placeholder used when pygame is unavailable (headless tests)."""

    def __init__(self, colour: tuple[int, int, int] = (0, 0, 0)) -> None:
        self._colour = colour

    def get_width(self) -> int:  # noqa: D102
        return 64

    def get_height(self) -> int:  # noqa: D102
        return 64


class SpriteManager:
    """Loads and caches piece surface images.

    In environments where pygame is not initialised (e.g. headless unit tests)
    the manager returns lightweight placeholder objects rather than real
    ``pygame.Surface`` instances.

    Team-specific images are loaded from
    ``asset_dir/pieces/<rank>/<side>/<rank>.png`` when available, falling back
    to the generic ``asset_dir/pieces/<rank>/<rank>.png`` and ultimately to a
    solid-colour placeholder.  The *side* sub-directory is populated by
    ``generate_assets.py``.
    """

    def __init__(self, asset_dir: Path) -> None:
        """Initialise the sprite manager.

        Args:
            asset_dir: Root directory that contains the ``pieces/`` sub-folder.
        """
        self._asset_dir = asset_dir
        self._cache: dict[Rank | tuple[Rank, PlayerSide], Any] = {}
        self._hidden_surface: Any = self._make_placeholder((40, 40, 40))
        self._lake_surface: Any = self._make_placeholder((0, 100, 200))
        self._empty_surface: Any = self._make_placeholder((34, 139, 34))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def hidden_surface(self) -> Any:
        """Surface used for opponent pieces whose rank is unknown (fog-of-war)."""
        return self._hidden_surface

    @property
    def lake_surface(self) -> Any:
        """Surface used for lake (impassable) squares."""
        return self._lake_surface

    @property
    def empty_surface(self) -> Any:
        """Surface used for empty normal squares."""
        return self._empty_surface

    # ------------------------------------------------------------------
    # Preloading
    # ------------------------------------------------------------------

    def preload_classic(self) -> None:
        """Load all rank images from ``asset_dir/pieces/<rank>/`` into the cache.

        Loads both RED and BLUE team variants when available (from
        ``<rank>/red/`` and ``<rank>/blue/`` sub-directories).  Falls back to
        solid-colour placeholder surfaces if no image files are found.
        """
        for rank in Rank:
            for side in PlayerSide:
                self._cache[(rank, side)] = self._load_rank_surface(rank, side)

    # ------------------------------------------------------------------
    # Surface access
    # ------------------------------------------------------------------

    def get_surface(self, rank: Rank, owner: PlayerSide, revealed: bool) -> Any:
        """Return the appropriate surface for a piece.

        Looks up a team-specific image (``<rank>/<side>/<rank>.png``) first,
        then falls back to the generic image (``<rank>/<rank>.png``) and
        finally to a solid-colour placeholder.

        Args:
            rank: The piece's rank.
            owner: The owning player — used to select the Red or Blue variant.
            revealed: If ``False``, returns the hidden (face-down) surface.

        Returns:
            A surface (real or placeholder) for the piece.
        """
        if not revealed:
            return self._hidden_surface
        cache_key: tuple[Rank, PlayerSide] = (rank, owner)
        if cache_key not in self._cache:
            self._cache[cache_key] = self._load_rank_surface(rank, owner)
        return self._cache[cache_key]

    # ------------------------------------------------------------------
    # Mod-aware preloading (custom_armies.md §5)
    # ------------------------------------------------------------------

    def preload_army(self, army_mod: ArmyMod) -> None:
        """Preload images for all ranks defined in *army_mod*.

        For each rank the method:

        1. Validates that none of the image paths in
           :attr:`~src.domain.army_mod.UnitCustomisation.image_paths`
           attempt a path traversal (raises :class:`PathTraversalError`).
        2. Collects the candidate image files (from the mod's
           ``images/<rank_lower>/`` folder, if present).
        3. Selects **one** image at random for the session; falls back to the
           cached Classic surface when no mod images are available.

        Args:
            army_mod: The :class:`~src.domain.army_mod.ArmyMod` to preload.

        Raises:
            PathTraversalError: If any image path in the mod attempts a
                path traversal (``../``) or is an absolute path.
        """
        # Validate all image paths across all ranks before loading anything.
        for rank, customisation in army_mod.unit_customisations.items():
            for img_path in customisation.image_paths:
                img_path_str = str(img_path)
                if Path(img_path_str).is_absolute() or ".." in img_path_str:
                    raise PathTraversalError(
                        f"Image path '{img_path}' for rank {rank.name} in mod "
                        f"'{army_mod.mod_id}' attempts a path traversal."
                    )

        # Also check the unit_image_paths attribute if present (used by tests).
        unit_image_paths: dict[Rank, Any] | None = getattr(
            army_mod, "unit_image_paths", None
        )
        if isinstance(unit_image_paths, dict):
            for rank, img_path_raw in unit_image_paths.items():
                img_path_str = str(img_path_raw)
                if Path(img_path_str).is_absolute() or ".." in img_path_str:
                    raise PathTraversalError(
                        f"Image path '{img_path_raw}' for rank {rank.name} in mod "
                        f"'{army_mod.mod_id}' attempts a path traversal."
                    )

        # Load images; fall back to Classic surfaces when no mod images exist.
        for rank in Rank:
            cust_opt: UnitCustomisation | None = army_mod.unit_customisations.get(rank)
            candidates: list[Path] = []
            if cust_opt is not None:
                candidates = list(cust_opt.image_paths)
            if candidates and army_mod.mod_directory is not None:
                chosen = random.choice(candidates)  # noqa: S311
                full_path = army_mod.mod_directory / chosen
                surface = self._try_load_image(full_path)
                if surface is not None:
                    # Cache the same mod surface for both sides (mod images are
                    # not team-specific).
                    for side in PlayerSide:
                        self._cache[(rank, side)] = surface
                    continue
            # Fallback: keep whatever Classic surface is already cached.
            for side in PlayerSide:
                if (rank, side) not in self._cache:
                    self._cache[(rank, side)] = self._load_rank_surface(rank, side)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_rank_surface(self, rank: Rank, owner: PlayerSide | None = None) -> Any:
        """Attempt to load the image for *rank*; fall back to a placeholder.

        Tries paths in order:

        1. ``asset_dir/pieces/<rank>/<side>/<rank>.png`` (team-specific, if
           *owner* is provided)
        2. ``asset_dir/pieces/<rank>/<rank>.png`` (generic / Red default)
        3. Solid-colour placeholder surface
        """
        rank_name = rank.name.lower()

        # 1. Try team-specific image (e.g. assets/pieces/marshal/red/marshal.png)
        if owner is not None:
            side_name = owner.value.lower()  # "red" or "blue"
            side_path = self._asset_dir / "pieces" / rank_name / side_name / f"{rank_name}.png"
            if _PYGAME_AVAILABLE and side_path.exists():
                try:
                    return _pygame.image.load(str(side_path))
                except Exception:  # noqa: BLE001, S110
                    logger.debug(
                        "SpriteManager: failed to load side image for rank %s side %s",
                        rank_name, side_name,
                    )

        # 2. Try generic / Red-default image (assets/pieces/marshal/marshal.png)
        image_path = self._asset_dir / "pieces" / rank_name / f"{rank_name}.png"
        if _PYGAME_AVAILABLE and image_path.exists():
            try:
                return _pygame.image.load(str(image_path))
            except Exception:  # noqa: BLE001, S110
                logger.debug("SpriteManager: failed to load image for rank %s", rank_name)

        # 3. Solid-colour placeholder
        colour = _RANK_COLOURS.get(rank, (128, 128, 128))
        return self._make_placeholder(colour)

    def _try_load_image(self, path: Path) -> Any:
        """Attempt to load an image from *path*; return ``None`` on failure."""
        if _PYGAME_AVAILABLE and path.exists():
            try:
                return _pygame.image.load(str(path))
            except Exception:  # noqa: BLE001, S110
                logger.debug("SpriteManager: failed to load mod image %s", path)
        return None

    def _make_placeholder(self, colour: tuple[int, int, int]) -> Any:
        """Return a surface (real or mock) filled with *colour*."""
        if _PYGAME_AVAILABLE:
            try:
                surf = _pygame.Surface((64, 64))
                surf.fill(colour)
                return surf
            except Exception:  # noqa: BLE001, S110
                logger.debug("SpriteManager: pygame Surface unavailable, using mock")
        return _MockSurface(colour)

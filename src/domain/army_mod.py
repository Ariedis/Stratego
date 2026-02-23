"""
src/domain/army_mod.py

ArmyMod and UnitCustomisation domain value objects.

These models are part of the domain layer and carry no I/O or pygame
dependencies.  They describe the cosmetic overrides a mod may supply for
each piece rank.

Specification: custom_armies.md §7
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.domain.enums import Rank


@dataclass(frozen=True)
class UnitCustomisation:
    """Cosmetic overrides for a single piece rank supplied by an army mod.

    Attributes:
        rank: The piece rank this customisation applies to.
        display_name: Human-readable name shown in the UI.
        display_name_plural: Plural form; defaults to ``display_name + "s"`` when
            not supplied.
        image_paths: Relative image file paths found for this rank inside the
            mod's ``images/<rank_lower>/`` folder.  Empty when no images are
            provided.
    """

    rank: Rank
    display_name: str
    display_name_plural: str = ""
    image_paths: tuple[Path, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Derive plural form from display_name when not explicitly provided."""
        if not self.display_name_plural:
            # frozen=True prevents normal attribute assignment; use object.__setattr__.
            object.__setattr__(self, "display_name_plural", self.display_name + "s")


@dataclass(frozen=True)
class ArmyMod:
    """A complete army mod descriptor loaded from disk or built in at compile time.

    Attributes:
        mod_id: Unique identifier derived from the mod's folder name (lower-case).
        army_name: Human-readable army name displayed in the UI.
        unit_customisations: Mapping from every :class:`Rank` to a
            :class:`UnitCustomisation` for that rank.
        mod_directory: Absolute path to the mod's root folder, or ``None`` for
            built-in mods that are not loaded from disk.
        author: Optional creator attribution string.
        description: Optional short description shown in the army preview panel.
    """

    mod_id: str
    army_name: str
    unit_customisations: dict[Rank, UnitCustomisation]
    mod_directory: Path | None = None
    author: str | None = None
    description: str | None = None

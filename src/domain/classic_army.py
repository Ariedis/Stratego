"""
src/domain/classic_army.py

Built-in "Classic" army definition.

The Classic army:
- Uses the standard Stratego piece names and default artwork.
- Cannot be deleted or modified.
- Is always listed first in any army list (mod_id ``"classic"`` sorts first
  alphabetically when the list is sorted by mod_id).
- Acts as the fallback when a mod's image files are missing or invalid.

Specification: custom_armies.md §8
"""
from __future__ import annotations

from src.domain.army_mod import ArmyMod, UnitCustomisation
from src.domain.enums import Rank

# Official display names from the Stratego Classic rulebook.
_CLASSIC_DISPLAY_NAMES: dict[Rank, str] = {
    Rank.FLAG: "Flag",
    Rank.SPY: "Spy",
    Rank.SCOUT: "Scout",
    Rank.MINER: "Miner",
    Rank.SERGEANT: "Sergeant",
    Rank.LIEUTENANT: "Lieutenant",
    Rank.CAPTAIN: "Captain",
    Rank.MAJOR: "Major",
    Rank.COLONEL: "Colonel",
    Rank.GENERAL: "General",
    Rank.MARSHAL: "Marshal",
    Rank.BOMB: "Bomb",
}


def _build_classic_army() -> ArmyMod:
    """Construct the immutable Classic ArmyMod instance."""
    customisations: dict[Rank, UnitCustomisation] = {
        rank: UnitCustomisation(rank=rank, display_name=name)
        for rank, name in _CLASSIC_DISPLAY_NAMES.items()
    }
    return ArmyMod(
        mod_id="classic",
        army_name="Classic",
        unit_customisations=customisations,
        mod_directory=None,
        author=None,
        description="The standard Stratego Classic army.",
    )


class ClassicArmy:
    """Provides access to the built-in Classic :class:`~src.domain.army_mod.ArmyMod`.

    This class is a simple namespace; all access is through :meth:`get`.
    The returned object is constructed once and shared across all callers.
    """

    _instance: ArmyMod | None = None

    @classmethod
    def get(cls) -> ArmyMod:
        """Return the singleton Classic :class:`~src.domain.army_mod.ArmyMod`.

        The instance is created on the first call and reused thereafter, so
        ``ClassicArmy.get() is ClassicArmy.get()`` is always ``True``.
        """
        if cls._instance is None:
            cls._instance = _build_classic_army()
        return cls._instance

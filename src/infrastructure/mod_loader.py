"""
src/infrastructure/mod_loader.py

Discovers and loads army mods from a mod directory.

Each mod is a sub-folder inside the configured mod directory that contains
a valid ``army.json`` manifest.  See ``custom_armies.md §3`` for the
expected folder structure.

Specification: custom_armies.md §6, system_design.md §2.6
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from src.domain.army_mod import ArmyMod, UnitCustomisation
from src.domain.classic_army import ClassicArmy
from src.domain.enums import Rank
from src.infrastructure.mod_validator import validate_manifest

logger = logging.getLogger(__name__)

# Regex used to normalise folder names to a canonical mod_id.
# Both ``dragon-horde`` and ``dragon_horde`` normalise to ``dragon_horde``.
_NORMALISE_RE = re.compile(r"[-\s]+")


def _normalise_mod_id(folder_name: str) -> str:
    """Return a canonical mod_id for *folder_name*."""
    return _NORMALISE_RE.sub("_", folder_name.lower())


def _build_army_mod(mod_dir: Path, manifest: dict[str, object]) -> ArmyMod:
    """Construct an :class:`~src.domain.army_mod.ArmyMod` from a validated manifest.

    Missing rank entries fall back to the Classic army's display name.

    Args:
        mod_dir: Path to the mod's root directory.
        manifest: Parsed and validated ``army.json`` content.

    Returns:
        A fully-populated :class:`~src.domain.army_mod.ArmyMod`.
    """
    classic = ClassicArmy.get()
    units_raw: object = manifest.get("units") or {}
    units_dict: dict[str, object] = units_raw if isinstance(units_raw, dict) else {}

    customisations: dict[Rank, UnitCustomisation] = {}
    for rank in Rank:
        unit_data = units_dict.get(rank.name)
        classic_name = classic.unit_customisations[rank].display_name

        if isinstance(unit_data, dict):
            display_name = str(unit_data.get("display_name") or classic_name)
            plural = str(unit_data.get("display_name_plural") or "")
        else:
            display_name = classic_name
            plural = ""

        # Collect image files from images/<rank_lower>/ if present.
        rank_image_dir = mod_dir / "images" / rank.name.lower()
        image_paths: tuple[Path, ...] = ()
        if rank_image_dir.is_dir():
            image_paths = tuple(
                p
                for p in sorted(rank_image_dir.iterdir())
                if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
            )

        customisations[rank] = UnitCustomisation(
            rank=rank,
            display_name=display_name,
            display_name_plural=plural or display_name + "s",
            image_paths=image_paths,
        )

    return ArmyMod(
        mod_id=_normalise_mod_id(mod_dir.name),
        army_name=str(manifest.get("army_name", mod_dir.name)),
        unit_customisations=customisations,
        mod_directory=mod_dir,
        author=str(manifest["author"]) if "author" in manifest else None,
        description=str(manifest["description"]) if "description" in manifest else None,
    )


def discover_mods(mod_directory: Path) -> list[ArmyMod]:
    """Discover and load all valid army mods from *mod_directory*.

    Each immediate sub-directory of *mod_directory* that contains an
    ``army.json`` file is treated as a potential mod.  Sub-directories
    without ``army.json`` are silently ignored.

    * Folders with malformed JSON are skipped; a warning is logged.
    * Folders whose manifest fails validation are skipped; a warning is
      logged.
    * If two folders normalise to the same :attr:`~ArmyMod.mod_id` the
      second is skipped with a warning.

    Args:
        mod_directory: Path to the top-level mods folder.

    Returns:
        A list of :class:`~src.domain.army_mod.ArmyMod` instances for
        every valid mod found.  The list may be empty.
    """
    result: list[ArmyMod] = []
    seen_ids: set[str] = set()

    if not mod_directory.is_dir():
        return result

    for entry in sorted(mod_directory.iterdir()):
        if not entry.is_dir():
            continue
        army_json = entry / "army.json"
        if not army_json.is_file():
            continue

        # Parse JSON.
        try:
            manifest: dict[str, object] = json.loads(army_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                    "mod_loader: skipping '%s' — cannot parse army.json: %s", entry.name, exc
                )
            continue

        # Validate.
        errors = validate_manifest(manifest)
        if errors:
            for err in errors:
                logger.warning(
                    "mod_loader: skipping '%s' — validation error on field '%s': %s",
                    entry.name,
                    err.field,
                    err.message,
                )
            continue

        # Deduplicate by normalised mod_id.
        mod_id = _normalise_mod_id(entry.name)
        if mod_id in seen_ids:
            logger.warning(
                "mod_loader: skipping '%s' — duplicate mod_id '%s'.", entry.name, mod_id
            )
            continue
        seen_ids.add(mod_id)

        try:
            army_mod = _build_army_mod(entry, manifest)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "mod_loader: skipping '%s' — failed to build ArmyMod: %s", entry.name, exc
            )
            continue

        result.append(army_mod)
        logger.info("mod_loader: loaded mod '%s' (%s).", army_mod.mod_id, army_mod.army_name)

    return result

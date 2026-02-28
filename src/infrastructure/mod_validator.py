"""
src/infrastructure/mod_validator.py

Validation logic for army mod manifests (``army.json``).

:func:`validate_manifest` returns a (possibly empty) list of
:class:`ValidationError` objects rather than raising exceptions, so that
callers can handle multiple validation problems at once.

Specification: custom_armies.md §4.3
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.enums import Rank

logger = logging.getLogger(__name__)

# Supported manifest schema versions.
_SUPPORTED_VERSIONS: frozenset[str] = frozenset({"1.0"})

# Known rank names derived from the Rank enum.
_KNOWN_RANK_NAMES: frozenset[str] = frozenset(r.name for r in Rank)

# Field length limits.
_ARMY_NAME_MIN = 1
_ARMY_NAME_MAX = 64
_DISPLAY_NAME_MAX = 32

# Task validation limits (US-802).
_TASK_DESCRIPTION_MIN = 1
_TASK_DESCRIPTION_MAX = 120

# Supported task image extensions (US-802).
_SUPPORTED_TASK_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
)


@dataclass(frozen=True)
class ValidationError:
    """A single validation problem found in a mod manifest.

    Attributes:
        field: Dot-separated path to the offending field
            (e.g. ``"army_name"`` or ``"units.MARSHAL.display_name"``).
        message: Human-readable description of the problem.
    """

    field: str
    message: str


def _validate_unit_tasks(rank_key: str, unit_data: dict[str, object]) -> None:
    """Log warnings for any invalid task entries in *unit_data*.

    Task validation issues produce log warnings only — they never add to the
    mod-level :class:`ValidationError` list so that a single bad task cannot
    block an otherwise valid mod from loading.  The mod loader is responsible
    for skipping invalid tasks or treating bad image paths as missing.

    Rules (US-802):
    - ``description`` must be 1–120 characters; otherwise the task is skipped.
    - ``image`` must be a relative path with no ``..`` segments and no leading
      ``/``; otherwise the image is treated as missing.
    - ``image`` extension must be in the supported set; otherwise treated as
      missing.

    Args:
        rank_key: Rank name string (e.g. ``"LIEUTENANT"``) used in log messages.
        unit_data: The unit's ``dict`` entry from the parsed manifest.
    """
    from pathlib import Path as _Path

    tasks_raw = unit_data.get("tasks")
    if not isinstance(tasks_raw, list):
        return

    for i, task_entry in enumerate(tasks_raw):
        if not isinstance(task_entry, dict):
            continue

        description = task_entry.get("description", "")
        if not isinstance(description, str) or not (
            _TASK_DESCRIPTION_MIN <= len(description) <= _TASK_DESCRIPTION_MAX
        ):
            logger.warning(
                "mod_validator: %s.tasks[%d].description invalid "
                "(must be %d–%d characters); task will be skipped.",
                rank_key,
                i,
                _TASK_DESCRIPTION_MIN,
                _TASK_DESCRIPTION_MAX,
            )
            continue

        image_raw = task_entry.get("image")
        if not isinstance(image_raw, str) or not image_raw:
            continue

        img_path = _Path(image_raw)
        if img_path.is_absolute():
            logger.warning(
                "mod_validator: %s.tasks[%d].image '%s' is an absolute path; "
                "image will be treated as missing.",
                rank_key,
                i,
                image_raw,
            )
            continue

        if ".." in img_path.parts:
            logger.warning(
                "mod_validator: %s.tasks[%d].image '%s' contains '..'; "
                "image will be treated as missing.",
                rank_key,
                i,
                image_raw,
            )
            continue

        if img_path.suffix.lower() not in _SUPPORTED_TASK_IMAGE_EXTENSIONS:
            logger.warning(
                "mod_validator: %s.tasks[%d].image '%s' has unsupported extension '%s'; "
                "image will be treated as missing.",
                rank_key,
                i,
                image_raw,
                img_path.suffix,
            )


def validate_manifest(manifest: dict[str, object]) -> list[ValidationError]:
    """Validate an ``army.json`` manifest dictionary.

    Args:
        manifest: Parsed JSON content of an ``army.json`` file.

    Returns:
        A list of :class:`ValidationError` objects.  An empty list means
        the manifest is fully valid.
    """
    errors: list[ValidationError] = []

    # ------------------------------------------------------------------
    # mod_version
    # ------------------------------------------------------------------
    mod_version = manifest.get("mod_version")
    if mod_version not in _SUPPORTED_VERSIONS:
        errors.append(
            ValidationError(
                field="mod_version",
                message=(
                    f"Unsupported mod_version '{mod_version}'. "
                    f"Supported versions: {sorted(_SUPPORTED_VERSIONS)}."
                ),
            )
        )

    # ------------------------------------------------------------------
    # army_name
    # ------------------------------------------------------------------
    army_name = manifest.get("army_name", "")
    if not isinstance(army_name, str) or not (_ARMY_NAME_MIN <= len(army_name) <= _ARMY_NAME_MAX):
        errors.append(
            ValidationError(
                field="army_name",
                message=(
                    f"army_name must be {_ARMY_NAME_MIN}–{_ARMY_NAME_MAX} characters; "
                    f"got {len(str(army_name))} character(s)."
                ),
            )
        )

    # ------------------------------------------------------------------
    # units
    # ------------------------------------------------------------------
    units = manifest.get("units") or {}
    if isinstance(units, dict):
        for rank_key, unit_data in units.items():
            if rank_key not in _KNOWN_RANK_NAMES:
                logger.warning(
                    "mod_validator: unknown rank key '%s' in units; ignoring.", rank_key
                )
                continue

            if not isinstance(unit_data, dict):
                continue

            display_name = unit_data.get("display_name", "")
            if not isinstance(display_name, str) or len(display_name) > _DISPLAY_NAME_MAX:
                errors.append(
                    ValidationError(
                        field=f"units.{rank_key}.display_name",
                        message=(
                            f"display_name must be ≤ {_DISPLAY_NAME_MAX} characters; "
                            f"got {len(str(display_name))}."
                        ),
                    )
                )

            # Validate task entries — issues produce warnings, not blocking errors (US-802).
            _validate_unit_tasks(rank_key, unit_data)

    return errors

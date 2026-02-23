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

    return errors

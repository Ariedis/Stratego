"""
test_mod_validator.py — Unit tests for src/infrastructure/mod_validator.py

Epic: EPIC-7 | User Story: US-703
Covers acceptance criteria: AC-1 through AC-6
Specification: custom_armies.md §4.3
"""
from __future__ import annotations

import logging

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.infrastructure.mod_validator import ValidationError, validate_manifest

    _VALIDATOR_AVAILABLE = True
except ImportError:
    validate_manifest = None  # type: ignore[assignment, misc]
    ValidationError = Exception  # type: ignore[assignment, misc]
    _VALIDATOR_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _VALIDATOR_AVAILABLE,
    reason="src.infrastructure.mod_validator not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_MANIFEST: dict = {
    "mod_version": "1.0",
    "army_name": "Dragon Horde",
    "units": {
        "MARSHAL": {"display_name": "Dragon Lord"},
    },
}


# ---------------------------------------------------------------------------
# US-703 AC-1: Unsupported mod_version raises ValidationError
# ---------------------------------------------------------------------------


class TestModValidatorVersion:
    """AC-1: mod_version '2.0' (unsupported) → ValidationError on that field."""

    def test_unsupported_version_returns_error(self) -> None:
        """AC-1: mod_version '2.0' must produce a ValidationError."""
        manifest = {**_VALID_MANIFEST, "mod_version": "2.0"}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        assert any(
            e.field == "mod_version" for e in errors
        ), "Expected a ValidationError for mod_version"

    def test_unsupported_version_error_message(self) -> None:
        """AC-1: The error message must mention the unsupported version."""
        manifest = {**_VALID_MANIFEST, "mod_version": "2.0"}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        version_errors = [e for e in errors if e.field == "mod_version"]
        assert any("2.0" in e.message for e in version_errors)

    def test_supported_version_no_error(self) -> None:
        """AC-1 (inverse): mod_version '1.0' must produce no version error."""
        errors = validate_manifest(_VALID_MANIFEST)  # type: ignore[misc]
        version_errors = [e for e in errors if e.field == "mod_version"]
        assert len(version_errors) == 0


# ---------------------------------------------------------------------------
# US-703 AC-2 & AC-3: army_name length validation
# ---------------------------------------------------------------------------


class TestModValidatorArmyName:
    """AC-2 & AC-3: army_name must be 1–64 characters."""

    def test_empty_army_name_returns_error(self) -> None:
        """AC-2: army_name='' → ValidationError with field='army_name'."""
        manifest = {**_VALID_MANIFEST, "army_name": ""}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        assert any(e.field == "army_name" for e in errors)

    def test_empty_army_name_error_message(self) -> None:
        """AC-2: Error message must mention the length constraint."""
        manifest = {**_VALID_MANIFEST, "army_name": ""}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        name_errors = [e for e in errors if e.field == "army_name"]
        assert any("1" in e.message or "64" in e.message or "character" in e.message.lower()
                   for e in name_errors)

    def test_too_long_army_name_returns_error(self) -> None:
        """AC-3: army_name of 65 characters → ValidationError."""
        manifest = {**_VALID_MANIFEST, "army_name": "A" * 65}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        assert any(e.field == "army_name" for e in errors)

    def test_exactly_64_chars_is_valid(self) -> None:
        """AC-3 (boundary): army_name of exactly 64 chars → no error."""
        manifest = {**_VALID_MANIFEST, "army_name": "A" * 64}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        name_errors = [e for e in errors if e.field == "army_name"]
        assert len(name_errors) == 0

    def test_one_char_army_name_is_valid(self) -> None:
        """AC-2 (boundary): army_name of 1 character → no error."""
        manifest = {**_VALID_MANIFEST, "army_name": "X"}
        errors = validate_manifest(manifest)  # type: ignore[misc]
        name_errors = [e for e in errors if e.field == "army_name"]
        assert len(name_errors) == 0


# ---------------------------------------------------------------------------
# US-703 AC-4: display_name length (max 32 characters)
# ---------------------------------------------------------------------------


class TestModValidatorDisplayName:
    """AC-4: display_name must be ≤ 32 characters."""

    def test_display_name_33_chars_returns_error(self) -> None:
        """AC-4: display_name of 33 characters → ValidationError."""
        manifest = {
            "mod_version": "1.0",
            "army_name": "Test",
            "units": {"MARSHAL": {"display_name": "A" * 33}},
        }
        errors = validate_manifest(manifest)  # type: ignore[misc]
        assert any("MARSHAL" in e.field and "display_name" in e.field for e in errors)

    def test_display_name_32_chars_is_valid(self) -> None:
        """AC-4 (boundary): display_name of exactly 32 characters → no error."""
        manifest = {
            "mod_version": "1.0",
            "army_name": "Test",
            "units": {"MARSHAL": {"display_name": "A" * 32}},
        }
        errors = validate_manifest(manifest)  # type: ignore[misc]
        display_errors = [
            e for e in errors
            if "MARSHAL" in e.field and "display_name" in e.field
        ]
        assert len(display_errors) == 0


# ---------------------------------------------------------------------------
# US-703 AC-5: Unknown rank key is warned but not an error
# ---------------------------------------------------------------------------


class TestModValidatorUnknownRankKey:
    """AC-5: Unknown rank key 'WIZARD' in units → warning logged, no ValidationError."""

    def test_unknown_rank_key_does_not_raise(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-5: Unknown rank key must not produce a ValidationError."""
        manifest = {
            "mod_version": "1.0",
            "army_name": "Test",
            "units": {"WIZARD": {"display_name": "Wizard"}},
        }
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        wizard_errors = [e for e in errors if "WIZARD" in e.field]
        assert len(wizard_errors) == 0


# ---------------------------------------------------------------------------
# US-703 AC-6: Fully valid manifest produces no errors
# ---------------------------------------------------------------------------


class TestModValidatorValidManifest:
    """AC-6: A fully valid manifest returns an empty error list."""

    def test_valid_manifest_returns_no_errors(self) -> None:
        """AC-6: _VALID_MANIFEST must pass validation with zero errors."""
        errors = validate_manifest(_VALID_MANIFEST)  # type: ignore[misc]
        assert errors == []

    def test_manifest_with_all_ranks_is_valid(self) -> None:
        """AC-6: All 12 known ranks with valid display names → no errors."""
        manifest = {
            "mod_version": "1.0",
            "army_name": "Full Army",
            "units": {
                rank_name: {"display_name": rank_name.capitalize()}
                for rank_name in [
                    "FLAG", "SPY", "SCOUT", "MINER", "SERGEANT",
                    "LIEUTENANT", "CAPTAIN", "MAJOR", "COLONEL",
                    "GENERAL", "MARSHAL", "BOMB",
                ]
            },
        }
        errors = validate_manifest(manifest)  # type: ignore[misc]
        assert errors == []

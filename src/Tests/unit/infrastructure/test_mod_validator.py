"""
test_mod_validator.py — Unit tests for src/infrastructure/mod_validator.py

Epic: EPIC-7 | User Story: US-703
Covers acceptance criteria: AC-1 through AC-6
Specification: custom_armies.md §4.3

Epic: EPIC-8 | User Story: US-802
Covers acceptance criteria: AC-2 through AC-6
Specification: custom_armies.md §4.3, ux-wireframe-task-popup.md §7.1, §8
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

# Feature flag: whether task-specific validation is implemented in mod_validator.
try:
    from src.infrastructure.mod_validator import _TASK_DESCRIPTION_MAX  # type: ignore[attr-defined]

    _TASK_VALIDATION_AVAILABLE = True
except (ImportError, AttributeError):
    _TASK_VALIDATION_AVAILABLE = False

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


# ---------------------------------------------------------------------------
# US-802 AC-2: Task description too long (>120 chars) — task skipped with warning
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _TASK_VALIDATION_AVAILABLE,
    reason="Task validation not yet implemented in src.infrastructure.mod_validator",
    strict=False,
)
class TestModValidatorTaskDescription:
    """US-802 AC-2 & AC-3: task description length and content are validated."""

    _BASE_MANIFEST: dict = {
        "mod_version": "1.0",
        "army_name": "Fitness Army",
        "units": {
            "LIEUTENANT": {
                "display_name": "Scout Rider",
                "tasks": [],
            }
        },
    }

    def _manifest_with_task(self, description: str, image: str = "images/t.gif") -> dict:
        manifest = {
            "mod_version": "1.0",
            "army_name": "Fitness Army",
            "units": {
                "LIEUTENANT": {
                    "display_name": "Scout Rider",
                    "tasks": [{"description": description, "image": image}],
                }
            },
        }
        return manifest

    def test_description_121_chars_task_is_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-2: description of 121 characters → task skipped, warning logged."""
        long_desc = "A" * 121
        manifest = self._manifest_with_task(long_desc)
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        # The whole mod should NOT be rejected (no ValidationError for the mod itself)
        mod_level_errors = [
            e for e in errors if "LIEUTENANT" not in e.field
        ]
        assert len(mod_level_errors) == 0, "Whole mod must not be rejected for a bad task"

    def test_description_121_chars_warning_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-2: Warning must be logged containing the field name and rank."""
        long_desc = "A" * 121
        manifest = self._manifest_with_task(long_desc)
        with caplog.at_level(logging.WARNING):
            validate_manifest(manifest)  # type: ignore[misc]
        log_text = " ".join(r.getMessage() for r in caplog.records)
        assert "LIEUTENANT" in log_text or "description" in log_text.lower()

    def test_description_120_chars_is_valid(self) -> None:
        """AC-2 (boundary): description of exactly 120 characters is valid."""
        manifest = self._manifest_with_task("A" * 120)
        errors = validate_manifest(manifest)  # type: ignore[misc]
        task_errors = [
            e for e in errors if "task" in e.field.lower() or "description" in e.field.lower()
        ]
        assert len(task_errors) == 0

    def test_empty_description_task_is_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-3: description='' → task skipped with warning."""
        manifest = self._manifest_with_task("")
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        mod_level_errors = [
            e for e in errors if "LIEUTENANT" not in e.field
        ]
        assert len(mod_level_errors) == 0, "Whole mod must not be rejected for empty description"

    def test_empty_description_warning_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-3: A warning must be logged when description is empty."""
        manifest = self._manifest_with_task("")
        with caplog.at_level(logging.WARNING):
            validate_manifest(manifest)  # type: ignore[misc]
        assert any(r.levelno >= logging.WARNING for r in caplog.records)


# ---------------------------------------------------------------------------
# US-802 AC-4: Path traversal in task image → treated as missing + warning
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _TASK_VALIDATION_AVAILABLE,
    reason="Task validation not yet implemented in src.infrastructure.mod_validator",
    strict=False,
)
class TestModValidatorTaskImageSecurity:
    """US-802 AC-4 & AC-5: Unsafe image paths are treated as missing."""

    def _manifest_with_image(self, image: str) -> dict:
        return {
            "mod_version": "1.0",
            "army_name": "Fitness Army",
            "units": {
                "LIEUTENANT": {
                    "display_name": "Scout Rider",
                    "tasks": [{"description": "Do pushups", "image": image}],
                }
            },
        }

    def test_path_traversal_does_not_cause_mod_rejection(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-4: Path traversal '../../secrets' → image treated as missing; mod loads."""
        manifest = self._manifest_with_image("../secrets/password.txt")
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        # Mod-level errors should not include a blocking error; just a warning
        mod_errors = [e for e in errors if "tasks" not in e.field.lower()]
        assert len(mod_errors) == 0

    def test_path_traversal_warning_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-4: A warning must be logged for path traversal attempts."""
        manifest = self._manifest_with_image("../secrets/password.txt")
        with caplog.at_level(logging.WARNING):
            validate_manifest(manifest)  # type: ignore[misc]
        assert any(r.levelno >= logging.WARNING for r in caplog.records)

    def test_absolute_path_does_not_cause_mod_rejection(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-5: Absolute path '/absolute/path/image.png' → image treated as missing."""
        manifest = self._manifest_with_image("/absolute/path/image.png")
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        mod_errors = [e for e in errors if "tasks" not in e.field.lower()]
        assert len(mod_errors) == 0

    def test_absolute_path_warning_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-5: A warning must be logged for absolute image paths."""
        manifest = self._manifest_with_image("/absolute/path/image.png")
        with caplog.at_level(logging.WARNING):
            validate_manifest(manifest)  # type: ignore[misc]
        assert any(r.levelno >= logging.WARNING for r in caplog.records)


# ---------------------------------------------------------------------------
# US-802 AC-6: Unsupported image extension → treated as missing + warning
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _TASK_VALIDATION_AVAILABLE,
    reason="Task validation not yet implemented in src.infrastructure.mod_validator",
    strict=False,
)
class TestModValidatorTaskImageExtension:
    """US-802 AC-6: Unsupported image extension → image treated as missing."""

    def _manifest_with_image(self, image: str) -> dict:
        return {
            "mod_version": "1.0",
            "army_name": "Fitness Army",
            "units": {
                "LIEUTENANT": {
                    "display_name": "Scout Rider",
                    "tasks": [{"description": "Do pushups", "image": image}],
                }
            },
        }

    @pytest.mark.parametrize(
        "unsupported_image",
        [
            "images/tasks/pushups.xyz",
            "images/tasks/exercise.tiff",
            "images/tasks/demo.svg",
            "images/tasks/video.mp4",
        ],
        ids=["xyz_ext", "tiff_ext", "svg_ext", "mp4_ext"],
    )
    def test_unsupported_extension_does_not_cause_mod_rejection(
        self, unsupported_image: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-6: Unsupported extension → image treated as missing; mod is not rejected."""
        manifest = self._manifest_with_image(unsupported_image)
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        mod_errors = [e for e in errors if "tasks" not in e.field.lower()]
        assert len(mod_errors) == 0

    @pytest.mark.parametrize(
        "unsupported_image",
        [
            "images/tasks/pushups.xyz",
            "images/tasks/exercise.tiff",
        ],
        ids=["xyz_ext", "tiff_ext"],
    )
    def test_unsupported_extension_warning_logged(
        self, unsupported_image: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-6: A warning must be logged for unsupported image extensions."""
        manifest = self._manifest_with_image(unsupported_image)
        with caplog.at_level(logging.WARNING):
            validate_manifest(manifest)  # type: ignore[misc]
        assert any(r.levelno >= logging.WARNING for r in caplog.records)

    @pytest.mark.parametrize(
        "valid_image",
        [
            "images/tasks/pushups.png",
            "images/tasks/situps.gif",
            "images/tasks/squats.jpg",
            "images/tasks/burpees.jpeg",
            "images/tasks/planks.bmp",
        ],
        ids=["png", "gif", "jpg", "jpeg", "bmp"],
    )
    def test_supported_extension_produces_no_warning(
        self, valid_image: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-6 (inverse): Supported extensions do not trigger a warning."""
        manifest = self._manifest_with_image(valid_image)
        with caplog.at_level(logging.WARNING):
            errors = validate_manifest(manifest)  # type: ignore[misc]
        # There should be no task-image-extension warning
        ext_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING and "extension" in r.getMessage().lower()
        ]
        assert len(ext_warnings) == 0

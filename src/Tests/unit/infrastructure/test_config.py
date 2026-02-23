"""
test_config.py — Unit tests for src/infrastructure/config.py

Epic: EPIC-6 | User Story: US-602
Covers acceptance criteria: AC-1 through AC-5
Specification: system_design.md §8
"""
from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.infrastructure.config import Config

    _CONFIG_AVAILABLE = True
except ImportError:
    Config = None  # type: ignore[assignment, misc]
    _CONFIG_AVAILABLE = False

try:
    from src.infrastructure.config import ConfigLoadError
except ImportError:
    ConfigLoadError = Exception  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    not _CONFIG_AVAILABLE,
    reason="src.infrastructure.config not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# US-602 AC-1: Defaults when config.yaml is absent
# ---------------------------------------------------------------------------


class TestConfigDefaults:
    """AC-1: Hardcoded defaults are used when config.yaml is absent."""

    def test_missing_file_uses_default_fps_cap(self, tmp_path: Path) -> None:
        """AC-1: No config.yaml → display.fps_cap defaults to 60."""
        missing = tmp_path / "config.yaml"
        config = Config.load(missing)  # type: ignore[union-attr]
        assert config.display.fps_cap == 60

    def test_missing_file_uses_default_difficulty(self, tmp_path: Path) -> None:
        """AC-1: No config.yaml → ai.default_difficulty defaults to 'medium'."""
        missing = tmp_path / "config.yaml"
        config = Config.load(missing)  # type: ignore[union-attr]
        assert config.ai.default_difficulty == "medium"

    def test_missing_file_uses_default_time_limit(self, tmp_path: Path) -> None:
        """AC-1: No config.yaml → ai.time_limit_ms defaults to 950."""
        missing = tmp_path / "config.yaml"
        config = Config.load(missing)  # type: ignore[union-attr]
        assert config.ai.time_limit_ms == 950

    def test_missing_file_does_not_raise(self, tmp_path: Path) -> None:
        """AC-1: Absent config file must not raise any exception."""
        missing = tmp_path / "config.yaml"
        config = Config.load(missing)  # type: ignore[union-attr]
        assert config is not None


# ---------------------------------------------------------------------------
# US-602 AC-2: Custom values from config.yaml are respected
# ---------------------------------------------------------------------------


class TestConfigCustomValues:
    """AC-2: Settings in config.yaml override the defaults."""

    def test_custom_fps_cap_loaded(self, tmp_path: Path) -> None:
        """AC-2: display.fps_cap: 144 in config → config.display.fps_cap == 144."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("display:\n  fps_cap: 144\n")
        config = Config.load(cfg_file)  # type: ignore[union-attr]
        assert config.display.fps_cap == 144

    def test_custom_ai_difficulty_loaded(self, tmp_path: Path) -> None:
        """AC-2: ai.default_difficulty can be overridden."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("ai:\n  default_difficulty: hard\n")
        config = Config.load(cfg_file)  # type: ignore[union-attr]
        assert config.ai.default_difficulty == "hard"

    def test_custom_search_depth_loaded(self, tmp_path: Path) -> None:
        """AC-2: ai.search_depth.hard should be overrideable."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("ai:\n  search_depth:\n    hard: 8\n")
        config = Config.load(cfg_file)  # type: ignore[union-attr]
        assert config.ai.search_depth.hard == 8


# ---------------------------------------------------------------------------
# US-602 AC-3: Missing sections use defaults
# ---------------------------------------------------------------------------


class TestConfigMissingSection:
    """AC-3: Config file with missing sections falls back to defaults for those sections."""

    def test_missing_ai_section_uses_defaults(self, tmp_path: Path) -> None:
        """AC-3: config.yaml with only 'display' → ai section defaults applied."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("display:\n  fps_cap: 120\n")
        config = Config.load(cfg_file)  # type: ignore[union-attr]
        assert config.ai.time_limit_ms == 950
        assert config.ai.default_difficulty == "medium"

    def test_missing_display_section_uses_defaults(self, tmp_path: Path) -> None:
        """AC-3: config.yaml with only 'ai' → display section defaults applied."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("ai:\n  default_difficulty: easy\n")
        config = Config.load(cfg_file)  # type: ignore[union-attr]
        assert config.display.fps_cap == 60


# ---------------------------------------------------------------------------
# US-602 AC-4: Invalid YAML raises ConfigLoadError
# ---------------------------------------------------------------------------


class TestConfigInvalidYaml:
    """AC-4: Malformed YAML raises ConfigLoadError with a descriptive message."""

    def test_invalid_yaml_raises_config_load_error(self, tmp_path: Path) -> None:
        """AC-4: A YAML parse error → ConfigLoadError raised."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("display:\n  fps_cap: [unclosed bracket\n")
        with pytest.raises(ConfigLoadError):
            Config.load(cfg_file)  # type: ignore[union-attr]

    def test_config_load_error_has_message(self, tmp_path: Path) -> None:
        """AC-4: ConfigLoadError must carry a descriptive message."""
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(": invalid yaml :")
        with pytest.raises(ConfigLoadError) as exc_info:
            Config.load(cfg_file)  # type: ignore[union-attr]
        assert str(exc_info.value)


# ---------------------------------------------------------------------------
# US-602 AC-5: Save/load round-trip
# ---------------------------------------------------------------------------


class TestConfigRoundTrip:
    """AC-5: Config.save() followed by Config.load() must return an equal config."""

    def test_round_trip_fps_cap(self, tmp_path: Path) -> None:
        """AC-5: fps_cap survives save/load round-trip."""
        cfg_file = tmp_path / "config.yaml"
        config = Config.load(tmp_path / "missing.yaml")  # type: ignore[union-attr]
        Config.save(config, cfg_file)  # type: ignore[union-attr]
        loaded = Config.load(cfg_file)  # type: ignore[union-attr]
        assert loaded.display.fps_cap == config.display.fps_cap

    def test_round_trip_full_equality(self, tmp_path: Path) -> None:
        """AC-5: loaded_config == config after round-trip."""
        cfg_file = tmp_path / "config.yaml"
        config = Config.load(tmp_path / "missing.yaml")  # type: ignore[union-attr]
        Config.save(config, cfg_file)  # type: ignore[union-attr]
        loaded = Config.load(cfg_file)  # type: ignore[union-attr]
        assert loaded == config

    def test_user_story_example(self, tmp_path: Path) -> None:
        """Verbatim example from US-602: search_depth.hard == 6 by default."""
        config = Config.load(tmp_path / "missing.yaml")  # type: ignore[union-attr]
        assert config.ai.search_depth.hard == 6
        assert config.persistence.save_directory == Path("~/.stratego/saves")

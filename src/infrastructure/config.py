"""
src/infrastructure/config.py

Configuration loader for the Stratego application.

Loads ``config.yaml`` from disk (if present) and merges with hard-coded
defaults.  Missing sections or missing files fall back to the defaults
without raising an error.  Malformed YAML raises
:class:`ConfigLoadError`.

Specification: system_design.md §8
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ConfigLoadError(Exception):
    """Raised when ``config.yaml`` exists but cannot be parsed."""


# ---------------------------------------------------------------------------
# Sub-sections
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchDepthConfig:
    """Per-difficulty minimax search depth settings."""

    easy: int = 2
    medium: int = 4
    hard: int = 6


@dataclass(frozen=True)
class AiConfig:
    """AI-related configuration values."""

    default_difficulty: str = "medium"
    time_limit_ms: int = 950
    search_depth: SearchDepthConfig = field(default_factory=SearchDepthConfig)


@dataclass(frozen=True)
class DisplayConfig:
    """Display-related configuration values."""

    fps_cap: int = 60
    resolution: tuple[int, int] = (1280, 720)
    fullscreen: bool = False


@dataclass(frozen=True)
class PersistenceConfig:
    """Persistence-related configuration values."""

    save_directory: Path = field(default_factory=lambda: Path("~/.stratego/saves"))


# ---------------------------------------------------------------------------
# Root config object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Config:
    """Root configuration object.

    Load via :meth:`Config.load`; persist via :meth:`Config.save`.
    """

    ai: AiConfig = field(default_factory=AiConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)

    # ------------------------------------------------------------------
    # Factory / persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load configuration from *path*.

        If *path* does not exist the hard-coded defaults are returned.
        If *path* exists but is not valid YAML, :class:`ConfigLoadError`
        is raised.

        Args:
            path: Path to a ``config.yaml`` file (need not exist).

        Returns:
            A fully-populated :class:`Config` instance.

        Raises:
            ConfigLoadError: If the file exists but cannot be parsed.
        """
        if not path.exists():
            return cls()

        raw_text = path.read_text(encoding="utf-8")
        try:
            data: object = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigLoadError(f"Failed to parse {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigLoadError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")

        return cls._from_dict(data)

    @classmethod
    def save(cls, config: Config, path: Path) -> None:
        """Write *config* to *path* as YAML.

        Args:
            config: The configuration to serialise.
            path: Destination file path (created or overwritten).
        """
        data: dict[str, object] = {
            "ai": {
                "default_difficulty": config.ai.default_difficulty,
                "time_limit_ms": config.ai.time_limit_ms,
                "search_depth": {
                    "easy": config.ai.search_depth.easy,
                    "medium": config.ai.search_depth.medium,
                    "hard": config.ai.search_depth.hard,
                },
            },
            "display": {
                "fps_cap": config.display.fps_cap,
                "resolution": list(config.display.resolution),
                "fullscreen": config.display.fullscreen,
            },
            "persistence": {
                "save_directory": str(config.persistence.save_directory),
            },
        }
        path.write_text(yaml.safe_dump(data, default_flow_style=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _from_dict(cls, data: dict[str, object]) -> Config:
        """Build a :class:`Config` from a raw parsed YAML dictionary."""
        ai_section = data.get("ai") or {}
        display_section = data.get("display") or {}
        persistence_section = data.get("persistence") or {}

        if not isinstance(ai_section, dict):
            ai_section = {}
        if not isinstance(display_section, dict):
            display_section = {}
        if not isinstance(persistence_section, dict):
            persistence_section = {}

        depth_raw = ai_section.get("search_depth") or {}
        if not isinstance(depth_raw, dict):
            depth_raw = {}
        search_depth = SearchDepthConfig(
            easy=int(depth_raw.get("easy", SearchDepthConfig.easy)),
            medium=int(depth_raw.get("medium", SearchDepthConfig.medium)),
            hard=int(depth_raw.get("hard", SearchDepthConfig.hard)),
        )

        ai = AiConfig(
            default_difficulty=str(
                ai_section.get("default_difficulty", AiConfig.default_difficulty)
            ),
            time_limit_ms=int(ai_section.get("time_limit_ms", AiConfig.time_limit_ms)),
            search_depth=search_depth,
        )

        res_raw = display_section.get("resolution", [1280, 720])
        if isinstance(res_raw, (list, tuple)) and len(res_raw) == 2:
            resolution: tuple[int, int] = (int(res_raw[0]), int(res_raw[1]))
        else:
            resolution = (1280, 720)
        display = DisplayConfig(
            fps_cap=int(display_section.get("fps_cap", DisplayConfig.fps_cap)),
            resolution=resolution,
            fullscreen=bool(display_section.get("fullscreen", DisplayConfig.fullscreen)),
        )

        save_dir_raw = persistence_section.get("save_directory", "~/.stratego/saves")
        persistence = PersistenceConfig(save_directory=Path(str(save_dir_raw)))

        return cls(ai=ai, display=display, persistence=persistence)

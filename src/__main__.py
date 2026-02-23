"""
src/__main__.py

Application entry point.  Invoked via:

    python -m src          # run directly from the repository root
    stratego               # after ``pip install .`` or ``pip install -e .``

Wires together all application-layer components (config, logging, domain,
event bus, game controller, screen manager, renderer, game loop) and starts
the main game loop.

Specification: system_design.md §1 (entry-point bootstrap)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.player import Player
from src.infrastructure.config import Config
from src.infrastructure.logger import setup_logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH = Path("~/.stratego/config.yaml")
_DEFAULT_LOG_DIR = Path("~/.stratego/logs")

# ---------------------------------------------------------------------------
# Standard Stratego army composition — 40 pieces per player
# (matches STANDARD_ARMY in src/Tests/unit/presentation/test_setup_screen.py)
# ---------------------------------------------------------------------------

_STANDARD_ARMY: list[Rank] = [
    Rank.MARSHAL,
    Rank.GENERAL,
    Rank.COLONEL, Rank.COLONEL,
    Rank.MAJOR, Rank.MAJOR, Rank.MAJOR,
    Rank.CAPTAIN, Rank.CAPTAIN, Rank.CAPTAIN, Rank.CAPTAIN,
    Rank.LIEUTENANT, Rank.LIEUTENANT, Rank.LIEUTENANT, Rank.LIEUTENANT,
    Rank.SERGEANT, Rank.SERGEANT, Rank.SERGEANT, Rank.SERGEANT,
    Rank.MINER, Rank.MINER, Rank.MINER, Rank.MINER, Rank.MINER,
    Rank.SCOUT, Rank.SCOUT, Rank.SCOUT, Rank.SCOUT,
    Rank.SCOUT, Rank.SCOUT, Rank.SCOUT, Rank.SCOUT,
    Rank.SPY,
    Rank.BOMB, Rank.BOMB, Rank.BOMB, Rank.BOMB, Rank.BOMB, Rank.BOMB,
    Rank.FLAG,
]

assert len(_STANDARD_ARMY) == 40, "Standard army must contain exactly 40 pieces"  # noqa: S101


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------


def _build_initial_state() -> GameState:
    """Return a fresh :class:`~src.domain.game_state.GameState` in ``SETUP`` phase.

    Both players start with no pieces placed on the board.  The
    :class:`~src.presentation.screens.setup_screen.SetupScreen` is responsible
    for populating the board before the ``PLAYING`` phase begins.
    """
    board = Board.create_empty()
    red_player = Player(
        side=PlayerSide.RED,
        player_type=PlayerType.HUMAN,
    )
    blue_player = Player(
        side=PlayerSide.BLUE,
        player_type=PlayerType.HUMAN,
    )
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.SETUP,
        turn_number=0,
    )


# ---------------------------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------------------------


def _launch_pygame(config: Config, initial_state: GameState) -> None:
    """Initialise pygame and run the full graphical game loop.

    Args:
        config: Application configuration (resolution, fps, …).
        initial_state: The starting ``GameState`` in ``SETUP`` phase.

    Raises:
        ImportError: If ``pygame`` or ``pygame_gui`` are not installed.
        pygame.error: If pygame cannot initialise a display.
    """
    import pygame

    import src.domain.rules_engine as _rules_engine
    from src.application.event_bus import EventBus
    from src.application.game_controller import GameController
    from src.application.game_loop import GameLoop
    from src.application.screen_manager import ScreenManager
    from src.presentation.pygame_renderer import PygameRenderer
    from src.presentation.screens.setup_screen import SetupScreen
    from src.presentation.sprite_manager import SpriteManager

    width, height = config.display.resolution
    pygame.init()
    flags = pygame.FULLSCREEN if config.display.fullscreen else 0
    display_surface = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Stratego")
    clock = pygame.time.Clock()

    event_bus = EventBus()
    controller = GameController(initial_state, event_bus, _rules_engine)
    screen_manager = ScreenManager()

    # Asset directory — placeholder surfaces are used when images are absent.
    asset_dir = Path(__file__).parent.parent / "assets"
    sprite_manager = SpriteManager(asset_dir)
    pygame_renderer = PygameRenderer(display_surface, sprite_manager)

    # Adapter: GameLoop calls render(state) but PygameRenderer needs
    # render(state, viewing_player).  Viewing perspective defaults to RED.
    viewing_player = PlayerSide.RED

    class _RendererAdapter:
        """Thin adapter that fixes the viewing-player for PygameRenderer."""

        def render(self, state: GameState) -> None:
            """Render *state* then flip the display buffer."""
            pygame_renderer.render(state, viewing_player)
            pygame.display.flip()

    setup_screen = SetupScreen(
        game_controller=controller,
        screen_manager=screen_manager,
        player_side=PlayerSide.RED,
        army=list(_STANDARD_ARMY),
    )
    screen_manager.push(setup_screen)

    game_loop = GameLoop(
        controller=controller,
        renderer=_RendererAdapter(),
        clock=clock,
        screen_manager=screen_manager,
    )

    logger.info(
        "Entering game loop (resolution=%dx%d, fps=%d)",
        width,
        height,
        config.display.fps_cap,
    )
    try:
        game_loop.run()
    finally:
        pygame.quit()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the Stratego launcher.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]`` when ``None``).

    Returns:
        Parsed :class:`argparse.Namespace`.
    """
    parser = argparse.ArgumentParser(
        prog="stratego",
        description="Stratego — the classic two-player board game.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        type=Path,
        default=_DEFAULT_CONFIG_PATH,
        help="Path to config.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Bootstrap and run the Stratego application.

    This is the console-script entry point registered in ``pyproject.toml``
    under ``[project.scripts]``.

    Args:
        argv: Optional argument list for programmatic invocation.  When
            ``None`` the process's ``sys.argv[1:]`` is used.
    """
    args = _parse_args(argv)

    log_dir = _DEFAULT_LOG_DIR.expanduser()
    setup_logging(log_dir=log_dir, level=args.log_level, console=True)
    logger.info("Stratego starting up …")

    config_path: Path = args.config.expanduser()
    config = Config.load(config_path)
    logger.debug("Config loaded from %s", config_path)

    initial_state = _build_initial_state()

    try:
        _launch_pygame(config, initial_state)
    except ImportError as exc:
        logger.error(
            "pygame is not installed — cannot launch the graphical frontend.\n"
            "Install it with:  pip install 'stratego[dev]'\n"
            "Error: %s",
            exc,
        )
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to launch Stratego: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

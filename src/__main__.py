"""
src/__main__.py

Application entry point.  Invoked via:

    python -m src          # run directly from the repository root
    stratego               # after ``pip install .`` or ``pip install -e .``

Wires together all application-layer components (config, logging, domain,
event bus, game controller, screen manager, renderer, game loop) and starts
the main game loop.  The application opens to the Main Menu; from there the
player configures a game session (game mode, AI difficulty, army placement)
before entering the playing screen.

Specification: system_design.md §1 (entry-point bootstrap); screen_flow.md §2
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

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


def _build_vs_ai_state(ai_difficulty: PlayerType) -> GameState:
    """Return a fresh :class:`~src.domain.game_state.GameState` for a vs-AI game.

    Player 1 (RED) is HUMAN; Player 2 (BLUE) is the requested AI type.

    Args:
        ai_difficulty: The ``PlayerType`` variant for the AI player
            (``AI_EASY``, ``AI_MEDIUM``, or ``AI_HARD``).
    """
    board = Board.create_empty()
    red_player = Player(
        side=PlayerSide.RED,
        player_type=PlayerType.HUMAN,
    )
    blue_player = Player(
        side=PlayerSide.BLUE,
        player_type=ai_difficulty,
    )
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.SETUP,
        turn_number=0,
    )


# ---------------------------------------------------------------------------
# Mutable holders (allow the game session to be replaced without restarting
# the game loop)
# ---------------------------------------------------------------------------


class _TurnManagerProxy:
    """Proxy for the active ``TurnManager``.

    The ``GameLoop`` holds a reference to this proxy and calls
    ``collect_ai_result()`` each frame.  When a new game session starts, the
    proxy's ``active`` attribute is updated to point at the fresh
    ``TurnManager`` (or ``None`` for a human-vs-human game).
    """

    def __init__(self) -> None:
        """Initialise the proxy with no active turn manager."""
        self.active: Any = None

    def collect_ai_result(self) -> None:
        """Delegate to the active ``TurnManager``, or no-op if absent."""
        if self.active is not None:
            self.active.collect_ai_result()


class _GameContext:
    """Mutable holder for the active game session.

    Acts as the ``controller`` argument to ``GameLoop`` (exposes
    ``current_state``).  Also serves as the factory that ``StartGameScreen``
    calls to create a new game session (``start_new_game``).
    """

    def __init__(
        self,
        initial_controller: Any,
        turn_manager_proxy: _TurnManagerProxy,
        renderer_adapter: Any,
        asset_dir: Path,
        config: Config | None = None,
    ) -> None:
        """Initialise the context with an existing controller.

        Args:
            initial_controller: The first ``GameController`` instance
                (created from ``_build_initial_state``).
            turn_manager_proxy: The shared ``_TurnManagerProxy`` that
                ``GameLoop`` observes.
            renderer_adapter: The renderer adapter used by ``SetupScreen`` and
                ``PlayingScreen`` to draw the board.
            asset_dir: Path to the assets directory (used if the renderer
                needs to be recreated — reserved for future use).
            config: The application ``Config``; used by the settings screen to
                read and persist display preferences.  Defaults to a fresh
                ``Config()`` when ``None``.
        """
        self._controller: Any = initial_controller
        self._turn_manager_proxy = turn_manager_proxy
        self._renderer_adapter: Any = renderer_adapter
        self._asset_dir = asset_dir
        self.config: Config = config if config is not None else Config()

    # Expose current_state so GameLoop can call self._controller.current_state.
    @property
    def current_state(self) -> Any:
        """Delegate to the active controller's ``current_state``."""
        return self._controller.current_state

    def start_new_game(
        self,
        game_mode: str,
        ai_difficulty: PlayerType | None,
        screen_manager: Any,
    ) -> None:
        """Create a fresh game session and push ``SetupScreen``.

        Called by ``StartGameScreen`` when the player clicks *Confirm*.

        Args:
            game_mode: ``"TWO_PLAYER"`` or ``"VS_AI"``.
            ai_difficulty: The ``PlayerType`` for the AI player, or ``None``
                for a two-player game.
            screen_manager: The ``ScreenManager`` that receives the new
                ``SetupScreen``.
        """
        import src.domain.rules_engine as _rules_engine
        from src.application.event_bus import EventBus
        from src.application.game_controller import GameController
        from src.application.turn_manager import TurnManager
        from src.presentation.screens.setup_screen import SetupScreen

        # Build fresh domain state.
        if game_mode == "VS_AI" and ai_difficulty is not None:
            initial_state = _build_vs_ai_state(ai_difficulty)
        else:
            initial_state = _build_initial_state()

        event_bus = EventBus()
        controller: GameController = GameController(
            initial_state, event_bus, _rules_engine
        )
        self._controller = controller

        # Set up AI turn management if required.
        if game_mode == "VS_AI" and ai_difficulty is not None:
            from src.ai.ai_orchestrator import AIOrchestrator

            ai_orch = AIOrchestrator()
            turn_manager = TurnManager(controller, event_bus, ai_orch)
            self._turn_manager_proxy.active = turn_manager
        else:
            self._turn_manager_proxy.active = None

        # Create the setup screen for RED (human player 1 always sets up).
        setup_screen = SetupScreen(
            game_controller=controller,
            screen_manager=screen_manager,
            player_side=PlayerSide.RED,
            army=list(_STANDARD_ARMY),
            event_bus=event_bus,
            renderer=self._renderer_adapter,
            viewing_player=PlayerSide.RED,
        )
        screen_manager.push(setup_screen)


# ---------------------------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------------------------


def _launch_pygame(config: Config, initial_state: GameState) -> None:
    """Initialise pygame and run the full graphical game loop.

    The application opens to the ``MainMenuScreen``.  From there the player
    navigates to ``StartGameScreen``, configures a game session, and proceeds
    through ``SetupScreen`` to ``PlayingScreen``.

    Args:
        config: Application configuration (resolution, fps, …).
        initial_state: The starting ``GameState`` in ``SETUP`` phase (used
            only as the initial state for the ``_GameContext``; a fresh state
            is created when the player starts a new game from the menu).

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
    from src.presentation.screens.main_menu_screen import MainMenuScreen
    from src.presentation.sprite_manager import SpriteManager

    width, height = config.display.resolution
    pygame.init()
    flags = pygame.FULLSCREEN if config.display.fullscreen else 0
    display_surface = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Stratego")
    clock = pygame.time.Clock()

    screen_manager = ScreenManager()

    # Asset directory — placeholder surfaces are used when images are absent.
    asset_dir = Path(__file__).parent.parent / "assets"
    sprite_manager = SpriteManager(asset_dir)
    pygame_renderer = PygameRenderer(display_surface, sprite_manager)

    # The renderer adapter wraps PygameRenderer so that screens only need
    # to call render(state) without carrying the viewing_player explicitly.
    # The viewing perspective is always RED (human player 1) here; PlayingScreen
    # can override this via its own logic if needed.
    _viewing_player = PlayerSide.RED

    class _RendererAdapter:
        """Thin adapter that fixes the viewing-player for PygameRenderer."""

        def render(self, state: GameState) -> None:
            """Render *state* for the configured viewing player."""
            pygame_renderer.render(state, _viewing_player)

    renderer_adapter = _RendererAdapter()

    # Create a placeholder initial controller (will be replaced when the
    # player starts a new game from the main menu).
    event_bus = EventBus()
    initial_controller = GameController(initial_state, event_bus, _rules_engine)

    # Mutable proxy objects — allow the game loop to observe the current
    # session without needing to be recreated.
    turn_manager_proxy = _TurnManagerProxy()
    game_context = _GameContext(
        initial_controller=initial_controller,
        turn_manager_proxy=turn_manager_proxy,
        renderer_adapter=renderer_adapter,
        asset_dir=asset_dir,
        config=config,
    )

    # Start at the Main Menu (screen_flow.md §2).
    main_menu_screen = MainMenuScreen(
        screen_manager=screen_manager,
        game_context=game_context,
    )
    screen_manager.push(main_menu_screen)

    game_loop = GameLoop(
        controller=game_context,   # _GameContext exposes current_state
        renderer=renderer_adapter,
        clock=clock,
        screen_manager=screen_manager,
        turn_manager=turn_manager_proxy,
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

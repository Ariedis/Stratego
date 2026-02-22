"""
src/domain/enums.py

All domain enumerations for the Stratego game.
Specification: data_models.md §3
"""
from __future__ import annotations

from enum import Enum, IntEnum


class Rank(IntEnum):
    """Piece ranks. Integer values enable direct combat comparison.

    BOMB is intentionally 99 (not 11) to make it unambiguous that Bombs
    are not part of the normal rank sequence.  See data_models.md §3.1.
    """

    FLAG = 0
    SPY = 1
    SCOUT = 2
    MINER = 3
    SERGEANT = 4
    LIEUTENANT = 5
    CAPTAIN = 6
    MAJOR = 7
    COLONEL = 8
    GENERAL = 9
    MARSHAL = 10
    BOMB = 99


class PlayerSide(Enum):
    """Identifies which player owns a piece or is currently active."""

    RED = "RED"
    BLUE = "BLUE"


class PlayerType(Enum):
    """Distinguishes human players from AI and network opponents."""

    HUMAN = "HUMAN"
    AI_EASY = "AI_EASY"
    AI_MEDIUM = "AI_MEDIUM"
    AI_HARD = "AI_HARD"
    NETWORK = "NETWORK"


class GamePhase(Enum):
    """High-level phases of a game session.  Drives the State Machine."""

    MAIN_MENU = "MAIN_MENU"
    SETUP = "SETUP"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"


class TerrainType(Enum):
    """Square terrain types.  LAKE squares are impassable."""

    NORMAL = "NORMAL"
    LAKE = "LAKE"


class MoveType(Enum):
    """Whether a move targets an empty square or an occupied enemy square."""

    MOVE = "MOVE"
    ATTACK = "ATTACK"


class CombatOutcome(Enum):
    """Result of a combat between two pieces."""

    ATTACKER_WINS = "ATTACKER_WINS"
    DEFENDER_WINS = "DEFENDER_WINS"
    DRAW = "DRAW"

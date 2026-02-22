"""Domain enumerations for the Stratego game."""

from enum import Enum, IntEnum


class Rank(IntEnum):
    """Piece ranks used in Stratego, ordered by combat strength."""

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
    """The two opposing sides in a Stratego game."""

    RED = "RED"
    BLUE = "BLUE"


class PlayerType(Enum):
    """Describes how a player's moves are generated."""

    HUMAN = "HUMAN"
    AI_EASY = "AI_EASY"
    AI_MEDIUM = "AI_MEDIUM"
    AI_HARD = "AI_HARD"
    NETWORK = "NETWORK"


class GamePhase(Enum):
    """High-level phase of the overall game lifecycle."""

    MAIN_MENU = "MAIN_MENU"
    SETUP = "SETUP"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"


class TerrainType(Enum):
    """Terrain types that can appear on a board square."""

    NORMAL = "NORMAL"
    LAKE = "LAKE"


class MoveType(Enum):
    """Classifies a move as a simple repositioning or an attack."""

    MOVE = "MOVE"
    ATTACK = "ATTACK"


class CombatOutcome(Enum):
    """Result of a combat engagement between two pieces."""

    ATTACKER_WINS = "ATTACKER_WINS"
    DEFENDER_WINS = "DEFENDER_WINS"
    DRAW = "DRAW"

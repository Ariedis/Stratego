"""
src/infrastructure/json_repository.py

JSON-based persistence for :class:`~src.domain.game_state.GameState`.

Save files are written to a configurable directory.  Each file contains
a top-level ``"version"`` key that is validated on load to support future
schema migrations.

Specification: data_models.md §6, system_design.md §8
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank, TerrainType
from src.domain.game_state import CombatRecord, GameState, MoveRecord
from src.domain.piece import Piece, Position
from src.domain.player import Player

_SAVE_VERSION = "1.0"
_SUPPORTED_VERSIONS: frozenset[str] = frozenset({"1.0"})


class UnsupportedSaveVersionError(Exception):
    """Raised when a save file carries an unrecognised version string."""


class SaveFileCorruptError(Exception):
    """Raised when a save file cannot be parsed or is structurally invalid."""


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _serialise_position(pos: Position) -> dict[str, int]:
    return {"row": pos.row, "col": pos.col}


def _serialise_piece(piece: Piece) -> dict[str, object]:
    return {
        "rank": piece.rank.name,
        "owner": piece.owner.value,
        "revealed": piece.revealed,
        "has_moved": piece.has_moved,
        "position": _serialise_position(piece.position),
    }


def _serialise_square(sq: Any) -> dict[str, object]:
    return {
        "row": sq.position.row,
        "col": sq.position.col,
        "terrain": sq.terrain.value,
        "piece": _serialise_piece(sq.piece) if sq.piece is not None else None,
    }


def _serialise_board(board: Board) -> dict[str, object]:
    squares_list = [
        _serialise_square(board.squares[(r, c)])
        for r in range(10)
        for c in range(10)
    ]
    return {"squares": squares_list}


def _serialise_player(player: Player) -> dict[str, object]:
    return {
        "side": player.side.value,
        "player_type": player.player_type.value,
        "pieces_remaining": [_serialise_piece(p) for p in player.pieces_remaining],
        "flag_position": (
            _serialise_position(player.flag_position)
            if player.flag_position is not None
            else None
        ),
    }


def _serialise_combat_record(cr: CombatRecord) -> dict[str, object]:
    return {
        "attacker_rank": cr.attacker_rank,
        "defender_rank": cr.defender_rank,
        "outcome": cr.outcome,
    }


def _serialise_move_record(mr: MoveRecord) -> dict[str, object]:
    return {
        "turn_number": mr.turn_number,
        "from_pos": list(mr.from_pos),
        "to_pos": list(mr.to_pos),
        "move_type": mr.move_type,
        "combat_result": (
            _serialise_combat_record(mr.combat_result)
            if mr.combat_result is not None
            else None
        ),
        "timestamp": mr.timestamp,
    }


def _serialise_state(state: GameState) -> dict[str, object]:
    return {
        "version": _SAVE_VERSION,
        "phase": state.phase.value,
        "active_player": state.active_player.value,
        "turn_number": state.turn_number,
        "winner": state.winner.value if state.winner is not None else None,
        "board": _serialise_board(state.board),
        "players": [_serialise_player(p) for p in state.players],
        "move_history": [_serialise_move_record(mr) for mr in state.move_history],
    }


# ---------------------------------------------------------------------------
# Deserialisation helpers
# ---------------------------------------------------------------------------


def _deserialise_position(d: dict[str, Any]) -> Position:
    return Position(row=int(d["row"]), col=int(d["col"]))


def _deserialise_piece(d: dict[str, Any]) -> Piece:
    return Piece(
        rank=Rank[d["rank"]],
        owner=PlayerSide(d["owner"]),
        revealed=bool(d["revealed"]),
        has_moved=bool(d["has_moved"]),
        position=_deserialise_position(d["position"]),
    )


def _deserialise_board(d: dict[str, Any]) -> Board:
    from src.domain.board import Square

    squares: dict[tuple[int, int], Square] = {}
    for sq_data in d["squares"]:
        row = int(sq_data["row"])
        col = int(sq_data["col"])
        terrain = TerrainType(sq_data["terrain"])
        piece: Piece | None = None
        if sq_data["piece"] is not None:
            piece = _deserialise_piece(sq_data["piece"])
        squares[(row, col)] = Square(
            position=Position(row, col),
            terrain=terrain,
            piece=piece,
        )
    return Board(squares=squares)


def _deserialise_player(d: dict[str, Any]) -> Player:
    pieces = tuple(_deserialise_piece(p) for p in d["pieces_remaining"])
    flag_pos: Position | None = None
    if d.get("flag_position") is not None:
        flag_pos = _deserialise_position(d["flag_position"])
    return Player(
        side=PlayerSide(d["side"]),
        player_type=PlayerType(d["player_type"]),
        pieces_remaining=pieces,
        flag_position=flag_pos,
    )


def _deserialise_combat_record(d: dict[str, Any] | None) -> CombatRecord | None:
    if d is None:
        return None
    return CombatRecord(
        attacker_rank=str(d["attacker_rank"]),
        defender_rank=str(d["defender_rank"]),
        outcome=str(d["outcome"]),
    )


def _deserialise_move_record(d: dict[str, Any]) -> MoveRecord:
    from_pos = tuple(d["from_pos"])
    to_pos = tuple(d["to_pos"])
    return MoveRecord(
        turn_number=int(d["turn_number"]),
        from_pos=(int(from_pos[0]), int(from_pos[1])),
        to_pos=(int(to_pos[0]), int(to_pos[1])),
        move_type=str(d["move_type"]),
        combat_result=_deserialise_combat_record(d.get("combat_result")),
        timestamp=float(d.get("timestamp", 0.0)),
    )


def _deserialise_state(data: dict[str, Any]) -> GameState:
    board = _deserialise_board(data["board"])
    players_raw: list[dict[str, Any]] = data["players"]
    players = (
        _deserialise_player(players_raw[0]),
        _deserialise_player(players_raw[1]),
    )
    winner: PlayerSide | None = None
    if data.get("winner") is not None:
        winner = PlayerSide(data["winner"])
    history = tuple(
        _deserialise_move_record(mr) for mr in data.get("move_history", [])
    )
    return GameState(
        board=board,
        players=players,
        active_player=PlayerSide(data["active_player"]),
        phase=GamePhase(data["phase"]),
        turn_number=int(data["turn_number"]),
        move_history=history,
        winner=winner,
    )


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class JsonRepository:
    """Persists :class:`~src.domain.game_state.GameState` objects as JSON files.

    Args:
        save_dir: Directory where save files are read from and written to.
    """

    def __init__(self, save_dir: Path) -> None:
        """Initialise the repository with *save_dir*."""
        self._save_dir = save_dir
        self._save_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, state: GameState, filename: str) -> Path:
        """Serialise *state* and write it to *filename* inside the save directory.

        Args:
            state: The game state to persist.
            filename: File name (not a full path) for the save file.

        Returns:
            The :class:`~pathlib.Path` of the written file.
        """
        data = _serialise_state(state)
        path = self._save_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def load(self, filename: str) -> GameState:
        """Load a :class:`~src.domain.game_state.GameState` from *filename*.

        Args:
            filename: File name (not a full path) inside the save directory.

        Returns:
            The deserialised :class:`~src.domain.game_state.GameState`.

        Raises:
            SaveFileCorruptError: If the file is not valid JSON or is
                structurally incomplete.
            UnsupportedSaveVersionError: If the file's ``"version"`` value is
                not in :data:`_SUPPORTED_VERSIONS`.
        """
        path = self._save_dir / filename
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SaveFileCorruptError(f"Cannot read save file '{filename}': {exc}") from exc

        if not raw.strip():
            raise SaveFileCorruptError(f"Save file '{filename}' is empty.")

        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SaveFileCorruptError(
                f"Save file '{filename}' contains invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise SaveFileCorruptError(f"Save file '{filename}' is not a JSON object.")

        version = data.get("version")
        if version is None:
            raise UnsupportedSaveVersionError(
                f"Save file '{filename}' has no 'version' field."
            )
        if version not in _SUPPORTED_VERSIONS:
            raise UnsupportedSaveVersionError(
                f"Save file '{filename}' has unsupported version '{version}'."
            )

        try:
            return _deserialise_state(data)
        except (KeyError, ValueError, TypeError) as exc:
            raise SaveFileCorruptError(
                f"Save file '{filename}' is structurally invalid: {exc}"
            ) from exc

    def get_most_recent_save(self) -> Path | None:
        """Return the path of the most recently written save file, or ``None``.

        Returns:
            The :class:`~pathlib.Path` of the most recently modified
            ``*.json`` file in the save directory, or ``None`` if no save
            files exist.
        """
        candidates = sorted(
            self._save_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

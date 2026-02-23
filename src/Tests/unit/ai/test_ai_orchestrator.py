"""
test_ai_orchestrator.py — Unit tests for src/ai/ai_orchestrator.py

Epic: EPIC-5 | User Story: US-503
Covers acceptance criteria:
  AC-1: Easy → depth 2
  AC-2: Medium → depth 4
  AC-3: Hard → depth 6
  AC-4: Retry logic on invalid move; AIMoveFailed after 3 failures
  AC-5: Time limit respected — best-so-far returned within budget
  AC-6: Endgame boost: < 10 pieces per side → depth +2
Specification: ai_strategy.md §8
"""
from __future__ import annotations

import pytest

try:
    from src.ai.ai_orchestrator import DIFFICULTY_DEPTH, AIMoveFailed, AIOrchestrator
    _ORCHESTRATOR_AVAILABLE = True
except ImportError:
    _ORCHESTRATOR_AVAILABLE = False
    AIMoveFailed = Exception  # type: ignore[assignment,misc]
    AIOrchestrator = None  # type: ignore[assignment]
    DIFFICULTY_DEPTH = None  # type: ignore[assignment]

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.piece import Piece, Position
from src.domain.player import Player

pytestmark = pytest.mark.xfail(
    not _ORCHESTRATOR_AVAILABLE,
    reason="src/ai/ai_orchestrator.py not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_piece(
    rank: Rank,
    owner: PlayerSide,
    row: int,
    col: int,
    *,
    revealed: bool = False,
    has_moved: bool = False,
) -> Piece:
    return Piece(
        rank=rank, owner=owner, revealed=revealed, has_moved=has_moved, position=Position(row, col)
    )


def _make_player(
    side: PlayerSide,
    pieces: tuple[Piece, ...],
    player_type: PlayerType = PlayerType.HUMAN,
) -> Player:
    flag_pos = next((p.position for p in pieces if p.rank == Rank.FLAG), None)
    return Player(
        side=side,
        player_type=player_type,
        pieces_remaining=pieces,
        flag_position=flag_pos,
    )


def _make_state(
    red_pieces: list[Piece],
    blue_pieces: list[Piece],
    phase: GamePhase = GamePhase.PLAYING,
) -> GameState:
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)
    red_player = _make_player(PlayerSide.RED, tuple(red_pieces))
    blue_player = _make_player(PlayerSide.BLUE, tuple(blue_pieces))
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=phase,
        turn_number=1,
    )


def _make_valid_move(state: GameState) -> Move:
    """Return a concrete valid Move from the given state (RED Scout moves one step)."""
    for player in state.players:
        if player.side == PlayerSide.RED:
            for piece in player.pieces_remaining:
                if piece.rank == Rank.SCOUT:
                    from_pos = piece.position
                    candidates = [
                        Position(from_pos.row - 1, from_pos.col),
                        Position(from_pos.row + 1, from_pos.col),
                        Position(from_pos.row, from_pos.col - 1),
                        Position(from_pos.row, from_pos.col + 1),
                    ]
                    for to_pos in candidates:
                        if to_pos.is_valid() and not state.board.is_lake(to_pos):
                            dest = state.board.get_square(to_pos)
                            if dest.piece is None:
                                return Move(piece=piece, from_pos=from_pos, to_pos=to_pos)
    raise ValueError("No valid Scout move found in state.")


@pytest.fixture
def standard_mid_game_state() -> GameState:
    """A PLAYING state with enough pieces for a realistic mid-game."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.BOMB, PlayerSide.RED, 8, 0),
        _make_piece(Rank.MARSHAL, PlayerSide.RED, 7, 0, has_moved=True),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 6, 0, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.RED, 6, 1, has_moved=True),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 9),
        _make_piece(Rank.BOMB, PlayerSide.BLUE, 1, 9),
        _make_piece(Rank.MARSHAL, PlayerSide.BLUE, 2, 9, has_moved=True),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 3, 9, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.BLUE, 3, 8, has_moved=True),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def endgame_state() -> GameState:
    """State with fewer than 10 pieces per side (triggers depth boost)."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.RED, 7, 0, has_moved=True),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 9),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 9, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.BLUE, 2, 9, has_moved=True),
    ]
    return _make_state(red_pieces, blue_pieces)


# ---------------------------------------------------------------------------
# US-503 AC-1 through AC-3: Difficulty-to-depth mapping
# ---------------------------------------------------------------------------


class TestDifficultyDepthMapping:
    """DIFFICULTY_DEPTH must map each difficulty to the correct search depth."""

    def test_easy_maps_to_depth_2(self) -> None:
        """AC-1: AI_EASY → depth 2."""
        assert DIFFICULTY_DEPTH[PlayerType.AI_EASY] == 2

    def test_medium_maps_to_depth_4(self) -> None:
        """AC-2: AI_MEDIUM → depth 4."""
        assert DIFFICULTY_DEPTH[PlayerType.AI_MEDIUM] == 4

    def test_hard_maps_to_depth_6(self) -> None:
        """AC-3: AI_HARD → depth 6."""
        assert DIFFICULTY_DEPTH[PlayerType.AI_HARD] == 6

    @pytest.mark.parametrize(
        "player_type, expected_depth",
        [
            (PlayerType.AI_EASY, 2),
            (PlayerType.AI_MEDIUM, 4),
            (PlayerType.AI_HARD, 6),
        ],
        ids=["easy", "medium", "hard"],
    )
    def test_request_move_uses_correct_depth(
        self,
        player_type: PlayerType,
        expected_depth: int,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """AC-1/2/3: request_move() calls minimax at the correct depth for each difficulty."""
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = _make_valid_move(standard_mid_game_state)

        orchestrator = AIOrchestrator()
        orchestrator.request_move(standard_mid_game_state, player_type)

        call_kwargs = mock_best_move.call_args
        called_depth = call_kwargs[1].get("max_depth") or call_kwargs[0][1]
        assert called_depth == expected_depth


# ---------------------------------------------------------------------------
# US-503 AC-6: Endgame depth boost
# ---------------------------------------------------------------------------


class TestEndgameDepthBoost:
    """AC-6: When fewer than 10 pieces per side, depth is increased by 2."""

    @pytest.mark.parametrize(
        "player_type, base_depth, expected_depth",
        [
            (PlayerType.AI_EASY, 2, 4),
            (PlayerType.AI_MEDIUM, 4, 6),
            (PlayerType.AI_HARD, 6, 8),
        ],
        ids=["easy_endgame", "medium_endgame", "hard_endgame"],
    )
    def test_endgame_boost_increases_depth_by_two(
        self,
        player_type: PlayerType,
        base_depth: int,
        expected_depth: int,
        endgame_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """AC-6: With < 10 pieces per side, depth = base_depth + 2."""
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = _make_valid_move(endgame_state)

        orchestrator = AIOrchestrator()
        orchestrator.request_move(endgame_state, player_type)

        call_kwargs = mock_best_move.call_args
        called_depth = call_kwargs[1].get("max_depth") or call_kwargs[0][1]
        assert called_depth == expected_depth

    def test_endgame_boost_not_applied_in_mid_game(
        self,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """Mid-game (≥ 10 pieces) uses the base depth without boost."""
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = _make_valid_move(standard_mid_game_state)

        orchestrator = AIOrchestrator()
        orchestrator.request_move(standard_mid_game_state, PlayerType.AI_HARD)

        call_kwargs = mock_best_move.call_args
        called_depth = call_kwargs[1].get("max_depth") or call_kwargs[0][1]
        assert called_depth == 6  # Hard base depth, no boost


# ---------------------------------------------------------------------------
# US-503 AC-4: Retry logic and AIMoveFailed
# ---------------------------------------------------------------------------


class TestRetryLogic:
    """AC-4: On invalid move, orchestrator retries up to 3 times then raises AIMoveFailed."""

    def test_retry_triggered_on_invalid_move(
        self,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """AC-4: If best_move returns an invalid move, the orchestrator retries."""
        # First call returns an invalid move; second call returns a valid one.
        valid_move = _make_valid_move(standard_mid_game_state)
        invalid_piece = _make_piece(Rank.BOMB, PlayerSide.RED, 9, 0)  # BOMB can't move
        invalid_move = Move(
            piece=invalid_piece,
            from_pos=Position(9, 0),
            to_pos=Position(9, 1),
        )
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.side_effect = [invalid_move, valid_move]

        orchestrator = AIOrchestrator()
        result = orchestrator.request_move(standard_mid_game_state, PlayerType.AI_MEDIUM)

        assert mock_best_move.call_count == 2
        assert result == valid_move

    def test_ai_move_failed_raised_after_three_invalid_moves(
        self,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """AC-4: After 3 consecutive invalid moves, AIMoveFailed is raised."""
        invalid_piece = _make_piece(Rank.BOMB, PlayerSide.RED, 9, 0)
        invalid_move = Move(
            piece=invalid_piece,
            from_pos=Position(9, 0),
            to_pos=Position(9, 1),
        )
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = invalid_move

        orchestrator = AIOrchestrator()
        with pytest.raises(AIMoveFailed):
            orchestrator.request_move(standard_mid_game_state, PlayerType.AI_MEDIUM)

        assert mock_best_move.call_count == 3

    def test_first_valid_move_returned_without_retry(
        self,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """No retry when first returned move is already valid."""
        valid_move = _make_valid_move(standard_mid_game_state)
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = valid_move

        orchestrator = AIOrchestrator()
        result = orchestrator.request_move(standard_mid_game_state, PlayerType.AI_EASY)

        assert mock_best_move.call_count == 1
        assert result == valid_move


# ---------------------------------------------------------------------------
# US-503 AC-5: Time limit respected
# ---------------------------------------------------------------------------


class TestTimeLimitRespected:
    """AC-5: request_move() respects the time_limit_ms parameter."""

    def test_request_move_passes_deadline_to_best_move(
        self,
        standard_mid_game_state: GameState,
        mocker: pytest.FixtureRequest,
    ) -> None:
        """AC-5: The orchestrator passes a deadline derived from time_limit_ms."""
        import time
        valid_move = _make_valid_move(standard_mid_game_state)
        mock_best_move = mocker.patch("src.ai.ai_orchestrator.best_move")
        mock_best_move.return_value = valid_move

        before = time.monotonic()
        orchestrator = AIOrchestrator()
        orchestrator.request_move(standard_mid_game_state, PlayerType.AI_HARD, time_limit_ms=950)
        after = time.monotonic()

        call_kwargs = mock_best_move.call_args
        deadline = call_kwargs[1].get("deadline") or call_kwargs[0][2]
        # Deadline should be within the expected range
        assert before + 0.9 <= deadline <= after + 1.0

"""
test_minimax.py — Unit tests for src/ai/minimax.py

Epic: EPIC-5 | User Story: US-502
Covers acceptance criteria:
  AC-1: Legal move always returned for non-terminal state
  AC-2: Forced win-in-1 detected at depth 2
  AC-3: Depth-6 search completes in < 950 ms
  AC-4: Move ordering reduces node count vs. unordered
  AC-5: None returned when no legal moves exist (game over)
Specification: ai_strategy.md §4.2, §7
"""
from __future__ import annotations

import time

import pytest

try:
    from src.ai.minimax import best_move, minimax
    _MINIMAX_AVAILABLE = True
except ImportError:
    _MINIMAX_AVAILABLE = False
    minimax = None  # type: ignore[assignment]
    best_move = None  # type: ignore[assignment]

from src.domain.board import Board
from src.domain.enums import GamePhase, MoveType, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.piece import Piece, Position
from src.domain.player import Player
from src.domain.rules_engine import ValidationResult, validate_move

pytestmark = pytest.mark.xfail(
    not _MINIMAX_AVAILABLE,
    reason="src/ai/minimax.py not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

_DEADLINE_GENEROUS = 30.0  # seconds – generous for unit test correctness checks


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


def _make_player(side: PlayerSide, pieces: tuple[Piece, ...]) -> Player:
    flag_pos = next((p.position for p in pieces if p.rank == Rank.FLAG), None)
    return Player(
        side=side,
        player_type=PlayerType.HUMAN,
        pieces_remaining=pieces,
        flag_position=flag_pos,
    )


def _make_state(
    red_pieces: list[Piece],
    blue_pieces: list[Piece],
    phase: GamePhase = GamePhase.PLAYING,
    winner: PlayerSide | None = None,
    active_player: PlayerSide = PlayerSide.RED,
) -> GameState:
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)
    red_player = _make_player(PlayerSide.RED, tuple(red_pieces))
    blue_player = _make_player(PlayerSide.BLUE, tuple(blue_pieces))
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=active_player,
        phase=phase,
        turn_number=1,
        winner=winner,
    )


@pytest.fixture
def mid_game_state() -> GameState:
    """A mid-game state with several pieces per side – suitable for search tests."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.BOMB, PlayerSide.RED, 8, 0),
        _make_piece(Rank.MARSHAL, PlayerSide.RED, 7, 0, has_moved=True),
        _make_piece(Rank.GENERAL, PlayerSide.RED, 7, 1, has_moved=True),
        _make_piece(Rank.COLONEL, PlayerSide.RED, 6, 0, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.RED, 6, 1, has_moved=True),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 6, 9, has_moved=True),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 9),
        _make_piece(Rank.BOMB, PlayerSide.BLUE, 1, 9),
        _make_piece(Rank.MARSHAL, PlayerSide.BLUE, 2, 9, has_moved=True),
        _make_piece(Rank.GENERAL, PlayerSide.BLUE, 2, 8, has_moved=True),
        _make_piece(Rank.COLONEL, PlayerSide.BLUE, 3, 9, has_moved=True),
        _make_piece(Rank.MINER, PlayerSide.BLUE, 3, 8, has_moved=True),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 3, 0, has_moved=True),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def win_in_one_state() -> GameState:
    """State where RED can capture the BLUE Flag in one move.

    RED's Scout is at (2, 0) and BLUE's Flag is at (2, 9) — clear path in same row.
    """
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 2, 0, has_moved=True),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 2, 9),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def game_over_state() -> GameState:
    """GAME_OVER state — no legal moves for any side."""
    red_pieces: list[Piece] = []
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
    ]
    return _make_state(red_pieces, blue_pieces, phase=GamePhase.GAME_OVER, winner=PlayerSide.BLUE)


# ---------------------------------------------------------------------------
# US-502 AC-1: Legal move returned
# ---------------------------------------------------------------------------


class TestMinimaxReturnsLegalMove:
    """AC-1: Every move returned by minimax/best_move must be legal."""

    def test_minimax_returns_legal_move_at_depth_2(self, mid_game_state: GameState) -> None:
        """AC-1: minimax() at depth 2 returns a legal move."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        move = minimax(mid_game_state, depth=2, ai_side=PlayerSide.RED, deadline=deadline)
        assert move is not None
        assert validate_move(mid_game_state, move) == ValidationResult.OK

    def test_best_move_returns_legal_move(self, mid_game_state: GameState) -> None:
        """AC-1: best_move() returns a legal move."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        move = best_move(mid_game_state, max_depth=2, deadline=deadline)
        assert move is not None
        assert validate_move(mid_game_state, move) == ValidationResult.OK


# ---------------------------------------------------------------------------
# US-502 AC-2: Forced win-in-1 detection
# ---------------------------------------------------------------------------


class TestForcedWinDetection:
    """AC-2: Minimax must find the flag-capture move in a win-in-1 scenario."""

    def test_minimax_finds_flag_capture_at_depth_2(self, win_in_one_state: GameState) -> None:
        """AC-2: A forced win-in-1 is detected at depth 2."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        move = minimax(win_in_one_state, depth=2, ai_side=PlayerSide.RED, deadline=deadline)
        assert move is not None
        # The winning move must capture the Blue Flag at (2, 9)
        assert move.to_pos == Position(2, 9)
        assert move.move_type == MoveType.ATTACK

    def test_best_move_finds_flag_capture(self, win_in_one_state: GameState) -> None:
        """AC-2: best_move() also finds the forced win."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        move = best_move(win_in_one_state, max_depth=4, deadline=deadline)
        assert move is not None
        assert move.to_pos == Position(2, 9)


# ---------------------------------------------------------------------------
# US-502 AC-3: Depth-6 time budget
# ---------------------------------------------------------------------------


class TestMinimaxTimeBudget:
    """AC-3: Depth-6 search must complete within 950 ms."""

    @pytest.mark.slow
    def test_depth_6_completes_within_time_budget(self, mid_game_state: GameState) -> None:
        """AC-3: best_move at depth 6 returns within 950 ms."""
        time_limit_ms = 950
        deadline = time.monotonic() + (time_limit_ms / 1000)
        start = time.monotonic()
        move = best_move(mid_game_state, max_depth=6, deadline=deadline)
        elapsed_ms = (time.monotonic() - start) * 1000

        # Either the search finished early or the time limit triggered iterative deepening
        assert elapsed_ms < time_limit_ms + 50  # 50 ms grace for overhead
        assert move is not None  # must return something within budget

    def test_deadline_respected_returns_best_so_far(self, mid_game_state: GameState) -> None:
        """AC-3: When deadline is hit, best move found so far is returned (not None)."""
        # Very tight deadline – forces early exit
        deadline = time.monotonic() + 0.001  # 1 ms
        move = best_move(mid_game_state, max_depth=6, deadline=deadline)
        # Should return the best move found so far (depth 1 at minimum), not None
        assert move is not None


# ---------------------------------------------------------------------------
# US-502 AC-4: Move ordering reduces node count
# ---------------------------------------------------------------------------


class TestMoveOrderingReducesNodes:
    """AC-4: With move ordering, fewer nodes are evaluated than without."""

    def test_ordered_search_evaluates_fewer_nodes_than_unordered(
        self, mid_game_state: GameState
    ) -> None:
        """AC-4: Ordered search visits fewer nodes than unordered at the same depth."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS

        # Run with ordering (default)
        move_ordered = minimax(
            mid_game_state, depth=4, ai_side=PlayerSide.RED, deadline=deadline
        )
        node_count_ordered = minimax.node_count  # type: ignore[attr-defined]

        # Run without ordering
        move_unordered = minimax(
            mid_game_state,
            depth=4,
            ai_side=PlayerSide.RED,
            deadline=deadline,
            use_move_ordering=False,  # type: ignore[call-arg]
        )
        node_count_unordered = minimax.node_count  # type: ignore[attr-defined]

        assert node_count_ordered < node_count_unordered
        assert move_ordered is not None
        assert move_unordered is not None


# ---------------------------------------------------------------------------
# US-502 AC-5: No legal moves
# ---------------------------------------------------------------------------


class TestMinimaxNoLegalMoves:
    """AC-5: minimax returns None (or raises NoLegalMovesError) when no moves exist."""

    def test_minimax_returns_none_for_game_over_state(
        self, game_over_state: GameState
    ) -> None:
        """AC-5: minimax returns None when the game is already over."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        result = minimax(game_over_state, depth=2, ai_side=PlayerSide.RED, deadline=deadline)
        assert result is None

    def test_best_move_returns_none_for_game_over_state(
        self, game_over_state: GameState
    ) -> None:
        """AC-5: best_move returns None when there are no legal moves."""
        deadline = time.monotonic() + _DEADLINE_GENEROUS
        result = best_move(game_over_state, max_depth=4, deadline=deadline)
        assert result is None

"""
test_rules_engine.py — Unit tests for src/domain/rules_engine.py

Epic: EPIC-2 | User Stories: US-202, US-203, US-205, US-206
Covers acceptance criteria:
  - US-202 AC-1 through AC-7: Normal piece movement validation
  - US-203 AC-1 through AC-6: Scout movement
  - US-205 AC-1 through AC-4: Win condition detection
  - US-206 AC-1 through AC-5: Setup phase validation

Specification:
  game_components.md §4 (Movement), §6 (Win Conditions), §7 (Setup)
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.domain.board import Board
from src.domain.enums import GamePhase, MoveType, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState, MoveRecord
from src.domain.move import Move
from src.domain.piece import Piece, Position
from src.domain.player import Player
from src.domain.rules_engine import (
    MAX_TURNS,
    RulesViolationError,
    ValidationResult,
    apply_move,
    apply_placement,
    check_win_condition,
    is_setup_complete,
    validate_move,
    validate_placement,
)
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_minimal_playing_state,
    make_red_piece,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state_with_pieces(
    red_pieces: list[Piece],
    blue_pieces: list[Piece],
    active: PlayerSide = PlayerSide.RED,
    turn: int = 1,
    history: tuple[MoveRecord, ...] = (),
) -> GameState:
    """Build a minimal PLAYING GameState from a list of pieces."""
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)

    red_player = Player(
        side=PlayerSide.RED,
        player_type=PlayerType.HUMAN,
        pieces_remaining=tuple(red_pieces),
    )
    blue_player = Player(
        side=PlayerSide.BLUE,
        player_type=PlayerType.HUMAN,
        pieces_remaining=tuple(blue_pieces),
    )

    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=active,
        phase=GamePhase.PLAYING,
        turn_number=turn,
        move_history=history,
    )


# ---------------------------------------------------------------------------
# US-202: Normal piece movement validation
# ---------------------------------------------------------------------------


class TestNormalPieceMovement:
    """AC-1 through AC-7: Movement rules for normal (non-Scout) pieces."""

    def test_ac1_valid_one_square_move(self) -> None:
        """AC-1: Sergeant moves one square right → OK.

        Note: the user story uses (5,5)→(5,6) but (5,6) is a lake square
        (game_components.md §2.2). Using (7,5)→(7,6) which is equivalent but
        in a clear area of the board.
        """
        sergeant = make_red_piece(Rank.SERGEANT, 7, 5)
        state = _make_state_with_pieces(
            [sergeant, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=sergeant, from_pos=Position(7, 5), to_pos=Position(7, 6))
        assert validate_move(state, move) == ValidationResult.OK

    def test_ac2_two_square_move_invalid(self) -> None:
        """AC-2: Sergeant moves 2 squares (not a Scout) → INVALID."""
        sergeant = make_red_piece(Rank.SERGEANT, 7, 5)
        state = _make_state_with_pieces(
            [sergeant, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=sergeant, from_pos=Position(7, 5), to_pos=Position(7, 7))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac3_diagonal_move_invalid(self) -> None:
        """AC-3: Diagonal move is always invalid."""
        sergeant = make_red_piece(Rank.SERGEANT, 7, 5)
        state = _make_state_with_pieces(
            [sergeant, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=sergeant, from_pos=Position(7, 5), to_pos=Position(8, 6))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac4_move_to_lake_invalid(self) -> None:
        """AC-4: Moving onto a lake square is invalid."""
        captain = make_red_piece(Rank.CAPTAIN, 4, 1)
        state = _make_state_with_pieces(
            [captain, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=captain, from_pos=Position(4, 1), to_pos=Position(4, 2))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac5_bomb_move_raises_rules_violation(self) -> None:
        """AC-5: Attempting to move a Bomb raises RulesViolationError with 'immovable'."""
        bomb = make_red_piece(Rank.BOMB, 9, 9)
        state = _make_state_with_pieces(
            [bomb, make_red_piece(Rank.FLAG, 9, 0)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=bomb, from_pos=Position(9, 9), to_pos=Position(9, 8))
        with pytest.raises(RulesViolationError, match="immovable"):
            validate_move(state, move)

    def test_ac6_flag_move_raises_rules_violation(self) -> None:
        """AC-6: Attempting to move a Flag raises RulesViolationError."""
        flag = make_red_piece(Rank.FLAG, 9, 0)
        state = _make_state_with_pieces(
            [flag, make_red_piece(Rank.SCOUT, 8, 0)],
            [make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=flag, from_pos=Position(9, 0), to_pos=Position(9, 1))
        with pytest.raises(RulesViolationError):
            validate_move(state, move)

    def test_ac7_two_square_rule_violation(self) -> None:
        """AC-7: Two-square rule — piece cannot shuttle back-and-forth more than twice."""
        captain = make_red_piece(Rank.CAPTAIN, 7, 5)
        state = _make_state_with_pieces(
            [captain, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        # Simulate two prior back-and-forth moves for this piece.
        history: tuple[MoveRecord, ...] = (
            MoveRecord(
                turn_number=1,
                from_pos=(7, 6),
                to_pos=(7, 5),
                move_type=MoveType.MOVE.value,
            ),
            MoveRecord(
                turn_number=2,
                from_pos=(7, 5),
                to_pos=(7, 6),
                move_type=MoveType.MOVE.value,
            ),
        )
        state_with_history = replace(state, move_history=history)
        # Third time back to (7,5) from (7,6) — violates two-square rule.
        move = Move(
            piece=replace(captain, position=Position(7, 6)),
            from_pos=Position(7, 6),
            to_pos=Position(7, 5),
        )
        assert validate_move(state_with_history, move) == ValidationResult.INVALID

    def test_move_to_off_board_position_invalid(self) -> None:
        """Moving to a position outside the board returns INVALID."""
        sergeant = make_red_piece(Rank.SERGEANT, 0, 0)
        state = _make_state_with_pieces(
            [sergeant, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=sergeant, from_pos=Position(0, 0), to_pos=Position(-1, 0))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_two_square_rule_triggers_via_repeated_move_pattern(self) -> None:
        """Two-square rule fires when history shows B→A then A→B and current move is A→B again."""
        captain = make_red_piece(Rank.CAPTAIN, 7, 5)
        state = _make_state_with_pieces(
            [captain, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        # History: second_last (7,6)→(7,5), last (7,5)→(7,6).
        # Proposed move: (7,5)→(7,6) — same as last entry → two-square rule triggers.
        history: tuple[MoveRecord, ...] = (
            MoveRecord(
                turn_number=1,
                from_pos=(7, 6),
                to_pos=(7, 5),
                move_type=MoveType.MOVE.value,
            ),
            MoveRecord(
                turn_number=2,
                from_pos=(7, 5),
                to_pos=(7, 6),
                move_type=MoveType.MOVE.value,
            ),
        )
        state_with_history = replace(state, move_history=history)
        # Captain is at (7,5); (7,6) is empty; propose (7,5)→(7,6) again.
        move = Move(
            piece=captain,
            from_pos=Position(7, 5),
            to_pos=Position(7, 6),
        )
        assert validate_move(state_with_history, move) == ValidationResult.INVALID

    def test_two_square_rule_no_violation_with_different_destination(self) -> None:
        """Two-square rule does not fire when the move destination differs from the pattern."""
        captain = make_red_piece(Rank.CAPTAIN, 7, 5)
        state = _make_state_with_pieces(
            [captain, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        # History has 2 entries, but the current move is in a new direction — no violation.
        history: tuple[MoveRecord, ...] = (
            MoveRecord(
                turn_number=1,
                from_pos=(7, 6),
                to_pos=(7, 5),
                move_type=MoveType.MOVE.value,
            ),
            MoveRecord(
                turn_number=2,
                from_pos=(7, 5),
                to_pos=(7, 6),
                move_type=MoveType.MOVE.value,
            ),
        )
        state_with_history = replace(state, move_history=history)
        # Move in a completely different direction — not a repeat of the pattern.
        move = Move(
            piece=captain,
            from_pos=Position(7, 5),
            to_pos=Position(8, 5),
        )
        assert validate_move(state_with_history, move) == ValidationResult.OK


# ---------------------------------------------------------------------------
# US-203: Scout movement validation
# ---------------------------------------------------------------------------


class TestScoutMovement:
    """AC-1 through AC-6: Scout long-range orthogonal movement rules."""

    def _clear_column(self) -> tuple[Piece, GameState]:
        """Helper: Scout at (6,4), clear column above to (2,4)."""
        scout = make_red_piece(Rank.SCOUT, 6, 4)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        return scout, state

    def test_ac1_scout_long_range_move_clear_column(self) -> None:
        """AC-1: Scout moves from (6,4) to (2,4) on a clear column → OK."""
        scout, state = self._clear_column()
        move = Move(piece=scout, from_pos=Position(6, 4), to_pos=Position(2, 4))
        assert validate_move(state, move) == ValidationResult.OK

    def test_ac2_scout_blocked_by_friendly_piece(self) -> None:
        """AC-2: Scout blocked by a friendly piece at (4,4) — cannot reach (3,4)."""
        scout = make_red_piece(Rank.SCOUT, 6, 4)
        friendly = make_red_piece(Rank.SERGEANT, 4, 4)
        state = _make_state_with_pieces(
            [scout, friendly, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        move = Move(piece=scout, from_pos=Position(6, 4), to_pos=Position(3, 4))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac3_scout_can_attack_enemy_in_path(self) -> None:
        """AC-3: Scout at (6,4) with enemy at (4,4) — can attack (4,4) → OK."""
        scout = make_red_piece(Rank.SCOUT, 6, 4)
        enemy = make_blue_piece(Rank.SERGEANT, 4, 4)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [enemy, make_blue_piece(Rank.FLAG, 0, 9)],
        )
        move = Move(
            piece=scout,
            from_pos=Position(6, 4),
            to_pos=Position(4, 4),
            move_type=MoveType.ATTACK,
        )
        assert validate_move(state, move) == ValidationResult.OK

    def test_ac4_scout_cannot_jump_over_enemy(self) -> None:
        """AC-4: Scout cannot move through an enemy piece."""
        scout = make_red_piece(Rank.SCOUT, 6, 4)
        enemy = make_blue_piece(Rank.SERGEANT, 4, 4)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [enemy, make_blue_piece(Rank.FLAG, 0, 9)],
        )
        move = Move(piece=scout, from_pos=Position(6, 4), to_pos=Position(3, 4))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac5_scout_diagonal_move_invalid(self) -> None:
        """AC-5: Scout cannot move diagonally."""
        scout = make_red_piece(Rank.SCOUT, 5, 5)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        move = Move(piece=scout, from_pos=Position(5, 5), to_pos=Position(3, 3))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_ac6_scout_cannot_cross_lake(self) -> None:
        """AC-6: Scout path is blocked when it includes a lake square."""
        # Place Scout at (3,2); trying to reach (6,2) requires crossing lake at (4,2).
        scout = make_red_piece(Rank.SCOUT, 3, 2)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        move = Move(piece=scout, from_pos=Position(3, 2), to_pos=Position(6, 2))
        assert validate_move(state, move) == ValidationResult.INVALID

    def test_scout_stay_in_place_invalid(self) -> None:
        """Scout attempting to stay in place (from_pos == to_pos) is invalid."""
        scout = make_red_piece(Rank.SCOUT, 5, 5)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        move = Move(piece=scout, from_pos=Position(5, 5), to_pos=Position(5, 5))
        assert validate_move(state, move) == ValidationResult.INVALID

    @pytest.mark.parametrize(
        "from_row,from_col,to_row,to_col,expected",
        [
            # Row 8 is fully clear — Scout can move right from col 0 to col 5.
            (8, 0, 8, 5, ValidationResult.OK),
            # Row 8: Scout at col 9 can move left to col 4.
            (8, 9, 8, 4, ValidationResult.OK),
        ],
        ids=["scout_move_right_in_clear_row", "scout_move_left_in_clear_row"],
    )
    def test_scout_horizontal_long_range(
        self,
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        expected: ValidationResult,
    ) -> None:
        """Scout can move multiple squares horizontally when the path is clear."""
        scout = make_red_piece(Rank.SCOUT, from_row, from_col)
        state = _make_state_with_pieces(
            [scout, make_red_piece(Rank.FLAG, 9, 9)],
            [make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.MINER, 1, 0)],
        )
        move = Move(
            piece=scout,
            from_pos=Position(from_row, from_col),
            to_pos=Position(to_row, to_col),
        )
        assert validate_move(state, move) == expected


# ---------------------------------------------------------------------------
# US-205: Win condition detection
# ---------------------------------------------------------------------------


class TestWinConditions:
    """AC-1 through AC-4: Win detection via check_win_condition()."""

    def test_ac1_flag_capture_red_wins(self) -> None:
        """AC-1: Blue's Flag is missing from remaining pieces → RED wins."""
        red_pieces = [make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)]
        # Blue has no flag (it was captured).
        blue_pieces = [make_blue_piece(Rank.SCOUT, 1, 0)]

        board = Board.create_empty()
        for p in red_pieces + blue_pieces:
            board = board.place_piece(p)

        red_player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(red_pieces),
        )
        blue_player = Player(
            side=PlayerSide.BLUE,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(blue_pieces),  # No flag!
        )

        state = GameState(
            board=board,
            players=(red_player, blue_player),
            active_player=PlayerSide.RED,
            phase=GamePhase.PLAYING,
            turn_number=5,
        )

        result = check_win_condition(state)
        assert result.phase == GamePhase.GAME_OVER
        assert result.winner == PlayerSide.RED

    def test_ac2_no_legal_moves_red_wins(self) -> None:
        """AC-2: Blue has only Bombs and Flag → RED wins (Blue has no moveable pieces)."""
        red_pieces = [
            make_red_piece(Rank.FLAG, 9, 0),
            make_red_piece(Rank.SCOUT, 8, 0),
        ]
        blue_pieces = [
            make_blue_piece(Rank.FLAG, 0, 0),
            make_blue_piece(Rank.BOMB, 0, 1),
            make_blue_piece(Rank.BOMB, 0, 2),
        ]

        board = Board.create_empty()
        for p in red_pieces + blue_pieces:
            board = board.place_piece(p)

        red_player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(red_pieces),
        )
        blue_player = Player(
            side=PlayerSide.BLUE,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(blue_pieces),
        )

        # It's RED's turn (active), so the check should find BLUE has no moves.
        state = GameState(
            board=board,
            players=(red_player, blue_player),
            active_player=PlayerSide.RED,
            phase=GamePhase.PLAYING,
            turn_number=10,
        )

        result = check_win_condition(state)
        assert result.phase == GamePhase.GAME_OVER
        assert result.winner == PlayerSide.RED

    def test_ac3_turn_limit_results_in_draw(self) -> None:
        """AC-3: turn_number >= MAX_TURNS → GAME_OVER with winner=None (draw)."""
        state = make_minimal_playing_state()
        state_at_limit = replace(state, turn_number=MAX_TURNS)
        result = check_win_condition(state_at_limit)
        assert result.phase == GamePhase.GAME_OVER
        assert result.winner is None

    def test_ac4_normal_game_no_false_positive(self) -> None:
        """AC-4: Normal mid-game state must not trigger GAME_OVER."""
        state = make_minimal_playing_state()
        result = check_win_condition(state)
        assert result.phase == GamePhase.PLAYING
        assert result.winner is None

    def test_already_game_over_state_unchanged(self) -> None:
        """check_win_condition is a no-op when the game is already over."""
        state = make_minimal_playing_state()
        game_over = replace(state, phase=GamePhase.GAME_OVER, winner=PlayerSide.BLUE)
        result = check_win_condition(game_over)
        # State unchanged — still GAME_OVER with same winner.
        assert result.phase == GamePhase.GAME_OVER
        assert result.winner == PlayerSide.BLUE


# ---------------------------------------------------------------------------
# US-206: Setup phase validation
# ---------------------------------------------------------------------------


class TestSetupPhaseValidation:
    """AC-1 through AC-5: Piece placement rules during setup."""

    def test_ac1_red_cannot_place_in_blue_zone(self, empty_setup_state: GameState) -> None:
        """AC-1: RED cannot place a piece at Position(3,5) (Blue's zone, rows 0–3)."""
        red_piece = make_red_piece(Rank.SCOUT, 3, 5)
        result = validate_placement(empty_setup_state, red_piece, Position(3, 5))
        assert result == ValidationResult.INVALID

    def test_ac2_red_can_place_in_own_zone(self, empty_setup_state: GameState) -> None:
        """AC-2: RED can place at Position(6,0) (row 6 is valid for RED)."""
        red_piece = make_red_piece(Rank.SCOUT, 6, 0)
        result = validate_placement(empty_setup_state, red_piece, Position(6, 0))
        assert result == ValidationResult.OK

    def test_ac3_placement_on_lake_invalid(self, empty_setup_state: GameState) -> None:
        """AC-3: Placing on a lake square (4,2) is invalid."""
        red_piece = make_red_piece(Rank.MINER, 4, 2)
        result = validate_placement(empty_setup_state, red_piece, Position(4, 2))
        assert result == ValidationResult.INVALID

    def test_ac4_setup_complete_when_both_players_have_40_pieces(self) -> None:
        """AC-4: is_setup_complete() returns True when both players have 40 pieces."""
        # Build a state where each player has 40 pieces.
        red_pieces = _build_40_pieces(PlayerSide.RED)
        blue_pieces = _build_40_pieces(PlayerSide.BLUE)

        red_player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(red_pieces),
        )
        blue_player = Player(
            side=PlayerSide.BLUE,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(blue_pieces),
        )
        board = Board.create_empty()
        state = GameState(
            board=board,
            players=(red_player, blue_player),
            active_player=PlayerSide.RED,
            phase=GamePhase.SETUP,
            turn_number=0,
        )
        assert is_setup_complete(state) is True

    def test_ac5_setup_incomplete_when_player_has_39_pieces(
        self, empty_setup_state: GameState
    ) -> None:
        """AC-5: is_setup_complete() returns False when RED has only 39 pieces."""
        red_pieces = _build_40_pieces(PlayerSide.RED)[:39]  # One short.
        blue_pieces = _build_40_pieces(PlayerSide.BLUE)

        red_player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(red_pieces),
        )
        blue_player = Player(
            side=PlayerSide.BLUE,
            player_type=PlayerType.HUMAN,
            pieces_remaining=tuple(blue_pieces),
        )

        state = replace(
            empty_setup_state,
            players=(red_player, blue_player),
        )
        assert is_setup_complete(state) is False

    def test_blue_cannot_place_in_red_zone(self, empty_setup_state: GameState) -> None:
        """BLUE cannot place in rows 6–9 (RED's zone)."""
        blue_piece = make_blue_piece(Rank.CAPTAIN, 9, 5)
        result = validate_placement(empty_setup_state, blue_piece, Position(9, 5))
        assert result == ValidationResult.INVALID

    def test_blue_can_place_in_own_zone(self, empty_setup_state: GameState) -> None:
        """BLUE can place in rows 0–3."""
        blue_piece = make_blue_piece(Rank.CAPTAIN, 2, 0)
        result = validate_placement(empty_setup_state, blue_piece, Position(2, 0))
        assert result == ValidationResult.OK

    def test_placement_on_occupied_square_invalid(
        self, empty_setup_state: GameState
    ) -> None:
        """A square already occupied cannot receive another piece."""
        red_piece = make_red_piece(Rank.SCOUT, 6, 0)
        board = empty_setup_state.board.place_piece(red_piece)
        occupied_state = replace(empty_setup_state, board=board)

        new_piece = make_red_piece(Rank.MINER, 6, 0)
        result = validate_placement(occupied_state, new_piece, Position(6, 0))
        assert result == ValidationResult.INVALID


# ---------------------------------------------------------------------------
# Helpers for setup tests
# ---------------------------------------------------------------------------


def _build_40_pieces(side: PlayerSide) -> list[Piece]:
    """Build a list of exactly 40 pieces for *side*, matching the official inventory.

    Distribution per game_components.md §3.1:
    Marshal×1, General×1, Colonel×2, Major×3, Captain×4, Lieutenant×4,
    Sergeant×4, Miner×5, Scout×8, Spy×1, Bomb×6, Flag×1 = 40
    """
    row_start = 6 if side == PlayerSide.RED else 0
    pieces: list[Piece] = []
    inventory = [
        (Rank.MARSHAL, 1),
        (Rank.GENERAL, 1),
        (Rank.COLONEL, 2),
        (Rank.MAJOR, 3),
        (Rank.CAPTAIN, 4),
        (Rank.LIEUTENANT, 4),
        (Rank.SERGEANT, 4),
        (Rank.MINER, 5),
        (Rank.SCOUT, 8),
        (Rank.SPY, 1),
        (Rank.BOMB, 6),
        (Rank.FLAG, 1),
    ]
    col = 0
    row = row_start
    for rank, count in inventory:
        for _ in range(count):
            pieces.append(
                Piece(
                    rank=rank, owner=side, revealed=False,
                    has_moved=False, position=Position(row, col),
                )
            )
            col += 1
            if col >= 10:
                col = 0
                row += 1
    return pieces


# ---------------------------------------------------------------------------
# apply_placement() — TASK-202 step 6
# ---------------------------------------------------------------------------


class TestApplyPlacement:
    """apply_placement() correctly places a piece and updates state."""

    def test_places_piece_on_board(self, empty_setup_state: GameState) -> None:
        """apply_placement() adds the piece to the board at the given position."""
        piece = make_red_piece(Rank.SCOUT, 9, 0)
        pos = piece.position
        new_state = apply_placement(empty_setup_state, piece, pos)
        sq = new_state.board.get_square(pos)
        assert sq.piece is not None
        assert sq.piece.rank == Rank.SCOUT

    def test_updates_player_pieces_remaining(self, empty_setup_state: GameState) -> None:
        """apply_placement() adds piece to the placing player's pieces_remaining."""
        piece = make_red_piece(Rank.FLAG, 9, 9)
        pos = piece.position
        new_state = apply_placement(empty_setup_state, piece, pos)
        red = next(p for p in new_state.players if p.side == PlayerSide.RED)
        assert any(p.rank == Rank.FLAG for p in red.pieces_remaining)

    def test_raises_for_invalid_placement(self, empty_setup_state: GameState) -> None:
        """apply_placement() raises RulesViolationError for a Blue-zone placement by RED."""
        piece = make_red_piece(Rank.SCOUT, 0, 0)
        with pytest.raises(RulesViolationError):
            apply_placement(empty_setup_state, piece, piece.position)

    def test_raises_for_lake_placement(self, empty_setup_state: GameState) -> None:
        """apply_placement() raises RulesViolationError when target is a lake square."""
        piece = make_red_piece(Rank.MINER, 4, 2)
        with pytest.raises(RulesViolationError):
            apply_placement(empty_setup_state, piece, piece.position)

    def test_updates_flag_position(self, empty_setup_state: GameState) -> None:
        """apply_placement() sets flag_position on the player when a FLAG is placed."""
        piece = make_red_piece(Rank.FLAG, 9, 5)
        pos = piece.position
        new_state = apply_placement(empty_setup_state, piece, pos)
        red = next(p for p in new_state.players if p.side == PlayerSide.RED)
        assert red.flag_position == pos


# ---------------------------------------------------------------------------
# apply_move() — TASK-203 step 2, TASK-206 step 1–3
# ---------------------------------------------------------------------------


class TestApplyMove:
    """apply_move() executes a legal move and returns the updated GameState."""

    def test_simple_move_updates_board(self) -> None:
        """A normal move relocates the piece on the board."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=scout, from_pos=scout.position, to_pos=Position(7, 0))
        new_state = apply_move(state, move)
        assert new_state.board.get_square(Position(7, 0)).piece is not None
        assert new_state.board.get_square(Position(8, 0)).piece is None

    def test_simple_move_advances_turn(self) -> None:
        """apply_move() increments turn_number by 1."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=scout, from_pos=scout.position, to_pos=Position(7, 0))
        new_state = apply_move(state, move)
        assert new_state.turn_number == state.turn_number + 1

    def test_simple_move_alternates_active_player(self) -> None:
        """apply_move() switches active_player from RED to BLUE."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=scout, from_pos=scout.position, to_pos=Position(7, 0))
        new_state = apply_move(state, move)
        assert new_state.active_player == PlayerSide.BLUE

    def test_simple_move_appends_to_history(self) -> None:
        """apply_move() adds one MoveRecord to move_history."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        move = Move(piece=scout, from_pos=scout.position, to_pos=Position(7, 0))
        new_state = apply_move(state, move)
        assert len(new_state.move_history) == 1

    def test_attack_attacker_wins_removes_defender(self) -> None:
        """When attacker wins (Marshal vs Scout), defender is removed from board."""
        marshal = make_red_piece(Rank.MARSHAL, 8, 0)
        blue_scout = make_blue_piece(Rank.SCOUT, 7, 0)
        state = _make_state_with_pieces(
            red_pieces=[marshal, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[blue_scout, make_blue_piece(Rank.FLAG, 0, 9)],
        )
        move = Move(
            piece=marshal, from_pos=marshal.position,
            to_pos=blue_scout.position, move_type=MoveType.ATTACK,
        )
        new_state = apply_move(state, move)
        sq = new_state.board.get_square(blue_scout.position)
        assert sq.piece is not None
        assert sq.piece.owner == PlayerSide.RED

    def test_attack_defender_wins_removes_attacker(self) -> None:
        """When defender wins (Scout vs Marshal), attacker is removed."""
        blue_marshal = make_blue_piece(Rank.MARSHAL, 7, 0)
        red_scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[blue_marshal, make_blue_piece(Rank.FLAG, 0, 9)],
        )
        move = Move(
            piece=red_scout, from_pos=red_scout.position,
            to_pos=blue_marshal.position, move_type=MoveType.ATTACK,
        )
        new_state = apply_move(state, move)
        assert new_state.board.get_square(red_scout.position).piece is None
        defender_sq = new_state.board.get_square(blue_marshal.position)
        assert defender_sq.piece is not None
        assert defender_sq.piece.owner == PlayerSide.BLUE

    def test_attack_draw_removes_both(self) -> None:
        """When equal ranks fight (Scout vs Scout), both are removed."""
        red_scout = make_red_piece(Rank.SCOUT, 8, 0)
        blue_scout = make_blue_piece(Rank.SCOUT, 7, 0)
        state = _make_state_with_pieces(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[blue_scout, make_blue_piece(Rank.FLAG, 0, 9)],
        )
        move = Move(
            piece=red_scout, from_pos=red_scout.position,
            to_pos=blue_scout.position, move_type=MoveType.ATTACK,
        )
        new_state = apply_move(state, move)
        assert new_state.board.get_square(red_scout.position).piece is None
        assert new_state.board.get_square(blue_scout.position).piece is None

    def test_apply_move_raises_for_invalid_move(self) -> None:
        """apply_move() raises RulesViolationError for a diagonal (invalid) move."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = _make_state_with_pieces(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        diagonal_move = Move(piece=scout, from_pos=scout.position, to_pos=Position(7, 1))
        with pytest.raises(RulesViolationError):
            apply_move(state, diagonal_move)

    def test_flag_capture_triggers_game_over(self) -> None:
        """Capturing the opponent's Flag sets phase=GAME_OVER."""
        red_marshal = make_red_piece(Rank.MARSHAL, 1, 0)
        blue_flag = make_blue_piece(Rank.FLAG, 0, 0)
        state = _make_state_with_pieces(
            red_pieces=[red_marshal, make_red_piece(Rank.FLAG, 9, 9)],
            blue_pieces=[blue_flag],
        )
        move = Move(
            piece=red_marshal, from_pos=red_marshal.position,
            to_pos=blue_flag.position, move_type=MoveType.ATTACK,
        )
        new_state = apply_move(state, move)
        assert new_state.phase == GamePhase.GAME_OVER
        assert new_state.winner == PlayerSide.RED

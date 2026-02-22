"""
test_commands.py — Unit tests for src/application/commands.py

Epic: EPIC-3 | User Story: US-301
Covers acceptance criteria: AC-1, AC-2, AC-3
Specification: system_design.md §2.2
"""
from __future__ import annotations

import pytest

from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Piece, Position

# ---------------------------------------------------------------------------
# Optional import — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.commands import MovePiece, PlacePiece
except ImportError:
    PlacePiece = None  # type: ignore[assignment, misc]
    MovePiece = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    PlacePiece is None,
    reason="src.application.commands not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_piece(rank: Rank = Rank.SCOUT, owner: PlayerSide = PlayerSide.RED) -> Piece:
    """Return a minimal Piece for test purposes."""
    return Piece(rank=rank, owner=owner, revealed=False, has_moved=False, position=Position(8, 0))


# ---------------------------------------------------------------------------
# US-301 AC-1: Immutability
# ---------------------------------------------------------------------------


class TestPlacePieceImmutability:
    """AC-1: PlacePiece must be a frozen dataclass."""

    def test_place_piece_mutation_raises_frozen_instance_error(self) -> None:
        """Assigning to any field of PlacePiece must raise FrozenInstanceError."""
        from dataclasses import FrozenInstanceError  # Python 3.11+

        scout = make_piece()
        cmd = PlacePiece(piece=scout, pos=Position(8, 0))
        with pytest.raises(FrozenInstanceError):
            cmd.pos = Position(7, 0)  # type: ignore[misc]

    def test_place_piece_piece_field_immutable(self) -> None:
        """The piece field of PlacePiece is also immutable."""
        from dataclasses import FrozenInstanceError

        scout = make_piece()
        cmd = PlacePiece(piece=scout, pos=Position(8, 0))
        with pytest.raises(FrozenInstanceError):
            cmd.piece = make_piece(Rank.FLAG)  # type: ignore[misc]


class TestMovePieceImmutability:
    """AC-1: MovePiece must be a frozen dataclass."""

    def test_move_piece_from_pos_mutation_raises_frozen_instance_error(self) -> None:
        """Assigning to from_pos must raise FrozenInstanceError."""
        from dataclasses import FrozenInstanceError

        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        with pytest.raises(FrozenInstanceError):
            cmd.from_pos = Position(9, 9)  # type: ignore[misc]

    def test_move_piece_to_pos_mutation_raises_frozen_instance_error(self) -> None:
        """Assigning to to_pos must raise FrozenInstanceError."""
        from dataclasses import FrozenInstanceError

        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        with pytest.raises(FrozenInstanceError):
            cmd.to_pos = Position(0, 0)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# US-301 AC-2: Equality
# ---------------------------------------------------------------------------


class TestCommandEquality:
    """AC-2: Two command instances with identical fields must be equal."""

    def test_move_piece_equality_identical_instances(self) -> None:
        """Two MovePiece instances with same fields compare equal."""
        cmd_a = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        cmd_b = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        assert cmd_a == cmd_b

    def test_place_piece_equality_identical_instances(self) -> None:
        """Two PlacePiece instances with same fields compare equal."""
        scout = make_piece()
        cmd_a = PlacePiece(piece=scout, pos=Position(8, 0))
        cmd_b = PlacePiece(piece=scout, pos=Position(8, 0))
        assert cmd_a == cmd_b

    def test_move_piece_inequality_different_positions(self) -> None:
        """MovePiece instances with different fields are not equal."""
        cmd_a = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        cmd_b = MovePiece(from_pos=Position(6, 4), to_pos=Position(4, 4))
        assert cmd_a != cmd_b

    def test_place_piece_inequality_different_positions(self) -> None:
        """PlacePiece instances with different positions are not equal."""
        scout = make_piece()
        cmd_a = PlacePiece(piece=scout, pos=Position(8, 0))
        cmd_b = PlacePiece(piece=scout, pos=Position(9, 0))
        assert cmd_a != cmd_b


# ---------------------------------------------------------------------------
# US-301 AC-3: repr
# ---------------------------------------------------------------------------


class TestCommandRepr:
    """AC-3: repr(cmd) must include all field names and values."""

    def test_move_piece_repr_includes_from_pos(self) -> None:
        """repr of MovePiece includes from_pos field."""
        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        assert "from_pos" in repr(cmd)

    def test_move_piece_repr_includes_to_pos(self) -> None:
        """repr of MovePiece includes to_pos field."""
        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        assert "to_pos" in repr(cmd)

    def test_place_piece_repr_includes_pos(self) -> None:
        """repr of PlacePiece includes pos field."""
        scout = make_piece()
        cmd = PlacePiece(piece=scout, pos=Position(8, 0))
        assert "pos" in repr(cmd)

    def test_place_piece_repr_includes_piece(self) -> None:
        """repr of PlacePiece includes piece field."""
        scout = make_piece()
        cmd = PlacePiece(piece=scout, pos=Position(8, 0))
        assert "piece" in repr(cmd)


# ---------------------------------------------------------------------------
# US-301: User story example
# ---------------------------------------------------------------------------


class TestCommandUserStoryExample:
    """Verbatim example from US-301."""

    def test_user_story_move_piece_from_pos_readable(self) -> None:
        """cmd.from_pos returns the original position."""
        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        assert cmd.from_pos == Position(6, 4)

    def test_user_story_move_piece_to_pos_readable(self) -> None:
        """cmd.to_pos returns the destination position."""
        cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
        assert cmd.to_pos == Position(5, 4)

    def test_user_story_place_piece_fields_readable(self) -> None:
        """PlacePiece fields are accessible after construction."""
        scout = make_piece()
        cmd = PlacePiece(piece=scout, pos=Position(8, 0))
        assert cmd.piece == scout
        assert cmd.pos == Position(8, 0)

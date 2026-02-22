"""Board position value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """An (row, col) coordinate on the 10×10 Stratego board."""

    row: int
    col: int

    def is_valid(self) -> bool:
        """Return True when this position lies within the 10×10 grid."""
        return 0 <= self.row <= 9 and 0 <= self.col <= 9

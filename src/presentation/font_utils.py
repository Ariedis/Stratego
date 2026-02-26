"""
src/presentation/font_utils.py

Font loading utilities for the presentation layer.

Provides a ``load_font`` helper that selects a system font with broad
Unicode coverage so that symbols such as ⚙ (\u2699), ✕ (\u2715),
✓ (\u2713), ← (\u2190) and → (\u2192) render as intended glyphs
rather than placeholder rectangles on all supported platforms.
"""
from __future__ import annotations

from typing import Any

# Fonts listed in priority order.
# DejaVu Sans — available on most Linux distributions, full Unicode BMP coverage.
# Segoe UI    — Windows Vista+, excellent Unicode coverage.
# Apple SD Gothic Neo / Helvetica Neue — macOS system fonts with good coverage.
# FreeSans    — GNU FreeFont package, Linux.
# Ubuntu      — Ubuntu Linux default UI font.
# Arial       — last-resort fallback; covers most basic Latin + common symbols
#               on Windows but may lack miscellaneous/extended blocks.
_UNICODE_FONT_PRIORITY = (
    "dejavusans",
    "segoeui",
    "applegothic",
    "helveticaneue",
    "freesans",
    "ubuntu",
    "arial",
)

# Comma-separated string accepted by pygame.font.SysFont as a fallback chain.
_FONT_FAMILY = ",".join(_UNICODE_FONT_PRIORITY)


def load_font(pygame_font_module: Any, size: int, bold: bool = False) -> Any:
    """Return a ``pygame.font.Font`` with Unicode symbol support.

    Tries each font in ``_UNICODE_FONT_PRIORITY`` in turn, using the first
    one that resolves to a real file on the current system.  Falls back to
    the pygame default font if none of the named fonts are found.

    Args:
        pygame_font_module: The ``pygame.font`` module (passed in to keep this
            module free of direct pygame imports, supporting headless tests).
        size: Desired point size.
        bold: Whether to request the bold variant.

    Returns:
        A ``pygame.font.Font`` instance.
    """
    return pygame_font_module.SysFont(_FONT_FAMILY, size, bold=bold)

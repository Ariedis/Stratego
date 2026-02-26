"""
src/presentation/font_utils.py

Font loading utilities for the presentation layer.

Provides a ``load_font`` helper that selects a system font with broad
Unicode coverage so that symbols such as ⚙ (\u2699), ✕ (\u2715),
✓ (\u2713), ← (\u2190) and → (\u2192) render as intended glyphs
rather than placeholder rectangles on all supported platforms.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Direct font file paths tried in priority order on each OS.
# Segoe UI Symbol (seguisym.ttf) covers Miscellaneous Technical (U+2600–U+26FF)
# and Dingbats (U+2700–U+27BF), which contain ⚙ ✓ ✕ etc.
# Segoe UI (segoeui.ttf) covers Arrows (U+2190–U+21FF) and general Latin.
_WINDOWS_FONT_DIR = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
_DIRECT_FONT_PATHS: tuple[Path, ...] = (
    # Segoe UI Symbol — must come before Segoe UI; only this file has ⚙/✓/✕
    _WINDOWS_FONT_DIR / "seguisym.ttf",
    # Segoe UI — arrows, general Latin
    _WINDOWS_FONT_DIR / "segoeui.ttf",
    # Arial Unicode MS (broad BMP coverage, present when Office is installed)
    _WINDOWS_FONT_DIR / "ARIALUNI.TTF",
    # macOS / Linux well-known paths
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    Path("/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"),
)

# pygame match_font name list — fallback when direct paths don't resolve.
_UNICODE_FONT_PRIORITY = (
    "segoeuisymbol",    # Windows 7+ — covers ⚙ ✓ ✕ and all BMP symbols
    "segoeui",          # Windows Vista+ — arrows, general Latin/Cyrillic
    "calibri",          # Windows (Office) — broad Latin + BMP
    "dejavusans",       # Linux — broad BMP coverage
    "notosans",         # Linux / cross-platform Google Noto
    "freesans",         # GNU FreeFont, Linux
    "ubuntu",           # Ubuntu Linux default
    "applegothic",      # macOS Korean / misc symbols
    "helveticaneue",    # macOS
    "arial",            # Last-resort fallback
)


def load_font(pygame_font_module: Any, size: int, bold: bool = False) -> Any:
    """Return a ``pygame.font.Font`` with Unicode symbol support.

    Strategy (in order):
    1. Try each path in ``_DIRECT_FONT_PATHS`` — this reliably locates
       fonts like Segoe UI Symbol whose exact glyph set is required.
    2. Try ``pygame.font.match_font`` for each name in
       ``_UNICODE_FONT_PRIORITY`` and load the resolved path with
       ``pygame.font.Font``.
    3. Fall back to ``pygame.font.SysFont`` with the full priority list.
    4. Last resort: ``pygame.font.Font(None, size)`` (built-in bitmap font,
       no Unicode symbols).

    Args:
        pygame_font_module: The ``pygame.font`` module (passed in to keep this
            module free of direct pygame imports, supporting headless tests).
        size: Desired point size.
        bold: Whether to request the bold variant.

    Returns:
        A ``pygame.font.Font`` instance.
    """
    font_cls = getattr(pygame_font_module, "Font", None)

    # 1. Direct path probing — most reliable on Windows for symbol fonts.
    if font_cls is not None:
        for font_path in _DIRECT_FONT_PATHS:
            if font_path.exists():
                try:
                    return font_cls(str(font_path), size)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("load_font: direct load failed for %s: %s", font_path, exc)

    # 2. pygame match_font resolution.
    match_font = getattr(pygame_font_module, "match_font", None)
    if match_font is not None and font_cls is not None:
        for name in _UNICODE_FONT_PRIORITY:
            path = match_font(name, bold=bold)
            if path:
                try:
                    return font_cls(path, size)
                except Exception as exc:  # noqa: BLE001
                    logger.debug(
                        "load_font: match_font load failed for '%s' (%s): %s",
                        name, path, exc,
                    )

    # 3. SysFont fallback.
    sys_font = getattr(pygame_font_module, "SysFont", None)
    if sys_font is not None:
        return sys_font(",".join(_UNICODE_FONT_PRIORITY), size, bold=bold)

    # 4. Built-in bitmap font (no Unicode symbols).
    if font_cls is not None:
        return font_cls(None, size)

    class _FallbackFont:  # pragma: no cover
        """Minimal stub used in fully headless test environments."""

        def render(self, text: str, antialias: bool, colour: Any) -> Any:  # noqa: ARG002
            return None

        def get_height(self) -> int:
            return size

    return _FallbackFont()

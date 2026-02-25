#!/usr/bin/env python3
"""
generate_assets.py

One-time development utility — generates all PNG image assets required by
``SpriteManager`` for piece sprites and board tiles.

Run once from the repository root after installing project dependencies::

    python generate_assets.py

This creates the full ``assets/`` directory tree and populates it with
64 × 64 px RGBA PNG files.  The generated images are neutral-coloured (not
team-tinted) so both RED and BLUE players share the same sprite until
``SpriteManager.get_surface()`` gains tinting logic.

Output structure::

    assets/
    ├── board/
    │   ├── cell_dark.png
    │   ├── cell_hidden.png
    │   ├── cell_lake.png
    │   └── cell_light.png
    └── pieces/
        ├── bomb/bomb.png
        ├── captain/captain.png
        ├── colonel/colonel.png
        ├── flag/flag.png
        ├── general/general.png
        ├── lieutenant/lieutenant.png
        ├── major/major.png
        ├── marshal/marshal.png
        ├── miner/miner.png
        ├── scout/scout.png
        ├── sergeant/sergeant.png
        └── spy/spy.png
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Headless SDL — must be set before pygame is imported
# ---------------------------------------------------------------------------
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
    import pygame.draw
    import pygame.font
    import pygame.image
except ImportError:
    print("ERROR: pygame-ce is required.  Install with:  pip install pygame-ce", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
SIZE = 64          # canvas size in pixels
CX = SIZE // 2     # centre x
CY = SIZE // 2     # centre y
RADIUS = SIZE // 2 - 3   # outer circle radius

# ---------------------------------------------------------------------------
# Piece definitions
#   (rank_name, label_text, badge_bg_colour)
#   Colours are muted/neutral so pieces are distinguishable without team tint.
# ---------------------------------------------------------------------------
_PIECES: list[tuple[str, str, tuple[int, int, int]]] = [
    ("flag",       "F",  (190, 155,  20)),   # gold
    ("spy",        "1",  (110,  20, 130)),   # purple
    ("scout",      "2",  ( 20,  85, 200)),   # blue
    ("miner",      "3",  (115,  75,  25)),   # brown
    ("sergeant",   "4",  ( 55, 105, 155)),   # steel-blue
    ("lieutenant", "5",  ( 35, 145,  75)),   # sea-green
    ("captain",    "6",  (200, 120,  15)),   # amber-orange
    ("major",      "7",  (185,  25,  45)),   # crimson
    ("colonel",    "8",  ( 75,  75,  75)),   # dark-grey
    ("general",    "9",  ( 15,  15, 165)),   # medium-blue
    ("marshal",    "10", ( 25,  25,  25)),   # near-black
    ("bomb",       "B",  ( 45,  45,  45)),   # charcoal
]

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

Color = tuple[int, int, int]


def _darken(c: Color, f: float = 0.55) -> Color:
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def _lighten(c: Color, f: float = 1.45) -> Color:
    return (min(255, int(c[0] * f)), min(255, int(c[1] * f)), min(255, int(c[2] * f)))


# ---------------------------------------------------------------------------
# Piece icon drawing helpers (pygame draw primitives — no emoji / Unicode)
# ---------------------------------------------------------------------------

def _icon_flag(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Small pennant: vertical pole + triangular flag."""
    pygame.draw.line(surf, (255, 255, 255, 200), (cx - 5, cy - 1), (cx - 5, cy + 8), 2)
    pygame.draw.polygon(surf, (255, 255, 255, 200), [
        (cx - 5, cy - 1), (cx + 5, cy + 2), (cx - 5, cy + 5),
    ])


def _icon_spy(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Eye / lens shape."""
    pygame.draw.ellipse(surf, (255, 255, 255, 200),
                        (cx - 7, cy, 14, 9), 2)
    pygame.draw.circle(surf, (255, 255, 255, 200), (cx, cy + 4), 3)


def _icon_scout(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Right-pointing arrow."""
    pygame.draw.polygon(surf, (255, 255, 255, 200), [
        (cx - 6, cy + 1), (cx + 1, cy + 1), (cx + 1, cy - 2),
        (cx + 7, cy + 3), (cx + 1, cy + 8), (cx + 1, cy + 5), (cx - 6, cy + 5),
    ])


def _icon_miner(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Crossed pickaxe handles — X shape."""
    pygame.draw.line(surf, (255, 255, 255, 200), (cx - 6, cy), (cx + 6, cy + 8), 2)
    pygame.draw.line(surf, (255, 255, 255, 200), (cx + 6, cy), (cx - 6, cy + 8), 2)


def _icon_sergeant(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Single chevron stripe."""
    pygame.draw.lines(surf, (255, 255, 255, 200), False, [
        (cx - 6, cy + 1), (cx, cy + 6), (cx + 6, cy + 1),
    ], 2)


def _icon_lieutenant(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Single horizontal rank bar."""
    pygame.draw.rect(surf, (255, 255, 255, 200), (cx - 7, cy + 3, 14, 3))


def _icon_captain(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Two horizontal rank bars."""
    pygame.draw.rect(surf, (255, 255, 255, 200), (cx - 7, cy + 1, 14, 2))
    pygame.draw.rect(surf, (255, 255, 255, 200), (cx - 7, cy + 5, 14, 2))


def _icon_major(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Diamond / rhombus."""
    pygame.draw.polygon(surf, (255, 255, 255, 200), [
        (cx, cy + 1), (cx + 5, cy + 5), (cx, cy + 9), (cx - 5, cy + 5),
    ])


def _icon_colonel(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Solid filled circle."""
    pygame.draw.circle(surf, (255, 255, 255, 200), (cx, cy + 5), 4)


def _icon_general(surf: pygame.Surface, cx: int, cy: int) -> None:
    """5-pointed star."""
    pts = []
    for i in range(5):
        outer_a = math.radians(-90 + i * 72)
        inner_a = math.radians(-90 + i * 72 + 36)
        pts.append((cx + 6 * math.cos(outer_a), cy + 5 + 6 * math.sin(outer_a)))
        pts.append((cx + 3 * math.cos(inner_a), cy + 5 + 3 * math.sin(inner_a)))
    pygame.draw.polygon(surf, (255, 255, 255, 200), pts)


def _icon_marshal(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Crown: three peaks."""
    pygame.draw.polygon(surf, (255, 255, 255, 200), [
        (cx - 7, cy + 8),
        (cx - 7, cy + 2),
        (cx - 4, cy + 5),
        (cx,     cy + 1),
        (cx + 4, cy + 5),
        (cx + 7, cy + 2),
        (cx + 7, cy + 8),
    ])


def _icon_bomb(surf: pygame.Surface, cx: int, cy: int) -> None:
    """Explosion burst — radiating lines."""
    pygame.draw.circle(surf, (255, 255, 255, 200), (cx, cy + 4), 4)
    for angle_deg in range(0, 360, 45):
        a = math.radians(angle_deg)
        x1 = cx + int(5 * math.cos(a))
        y1 = (cy + 4) + int(5 * math.sin(a))
        x2 = cx + int(9 * math.cos(a))
        y2 = (cy + 4) + int(9 * math.sin(a))
        pygame.draw.line(surf, (255, 255, 255, 200), (x1, y1), (x2, y2), 1)


_ICON_DRAW: dict[str, object] = {
    "flag":       _icon_flag,
    "spy":        _icon_spy,
    "scout":      _icon_scout,
    "miner":      _icon_miner,
    "sergeant":   _icon_sergeant,
    "lieutenant": _icon_lieutenant,
    "captain":    _icon_captain,
    "major":      _icon_major,
    "colonel":    _icon_colonel,
    "general":    _icon_general,
    "marshal":    _icon_marshal,
    "bomb":       _icon_bomb,
}

# ---------------------------------------------------------------------------
# Piece surface generator
# ---------------------------------------------------------------------------

def _make_piece(name: str, label: str, bg: Color) -> pygame.Surface:
    """Return a 64×64 RGBA surface for one piece rank."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    border_col = _darken(bg, 0.5)
    highlight_col = _lighten(bg, 1.4)

    # --- drop shadow (1 px offset) ---
    pygame.draw.circle(surf, (*border_col, 160), (CX + 1, CY + 1), RADIUS)

    # --- main badge circle ---
    pygame.draw.circle(surf, (*bg, 255), (CX, CY), RADIUS)

    # --- simulated top-light gradient: lighter arc across the top half ---
    for r in range(RADIUS - 1, RADIUS - 6, -1):
        alpha = int(80 * (RADIUS - r) / 5)
        pygame.draw.circle(surf, (*highlight_col, alpha), (CX, CY - 3), r, 1)

    # --- border ring ---
    pygame.draw.circle(surf, (*border_col, 255), (CX, CY), RADIUS, 2)

    # --- rank label (number or letter), centred in upper half ---
    font_size = 20 if len(label) <= 1 else 16
    font = pygame.font.SysFont("arial", font_size, bold=True)
    text_surf = font.render(label, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(CX, CY - 7))
    surf.blit(text_surf, text_rect)

    # --- thin separator line ---
    pygame.draw.line(surf, (255, 255, 255, 150),
                     (CX - 9, CY + 2), (CX + 9, CY + 2), 1)

    # --- rank-specific icon in the lower half ---
    draw_fn = _ICON_DRAW.get(name)
    if draw_fn is not None:
        draw_fn(surf, CX, CY + 4)  # type: ignore[operator]

    return surf


# ---------------------------------------------------------------------------
# Board tile generators
# ---------------------------------------------------------------------------

def _make_cell_light() -> pygame.Surface:
    """Light board cell — warm tan."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((195, 160, 100, 255))
    # subtle inner shadow on right/bottom edges
    pygame.draw.line(surf, (170, 135, 80, 255), (SIZE - 1, 0), (SIZE - 1, SIZE - 1), 1)
    pygame.draw.line(surf, (170, 135, 80, 255), (0, SIZE - 1), (SIZE - 1, SIZE - 1), 1)
    return surf


def _make_cell_dark() -> pygame.Surface:
    """Dark board cell — deeper tan."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((160, 120, 70, 255))
    pygame.draw.line(surf, (130, 95, 50, 255), (SIZE - 1, 0), (SIZE - 1, SIZE - 1), 1)
    pygame.draw.line(surf, (130, 95, 50, 255), (0, SIZE - 1), (SIZE - 1, SIZE - 1), 1)
    return surf


def _make_cell_lake() -> pygame.Surface:
    """Lake cell — deep blue with wave lines."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((30, 80, 140, 255))
    # three wave arcs
    for row_y in (14, 30, 46):
        pygame.draw.arc(surf, (60, 130, 200, 200),
                        (6, row_y - 4, 22, 10), 0, math.pi, 2)
        pygame.draw.arc(surf, (60, 130, 200, 200),
                        (30, row_y - 4, 22, 10), 0, math.pi, 2)
    # border
    pygame.draw.rect(surf, (20, 55, 110, 255), (0, 0, SIZE, SIZE), 1)
    return surf


def _make_cell_hidden() -> pygame.Surface:
    """Fog-of-war tile — dark navy with a centred '?' mark."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((28, 38, 56, 255))
    font = pygame.font.SysFont("arial", 30, bold=True)
    text_surf = font.render("?", True, (100, 120, 150))
    text_rect = text_surf.get_rect(center=(CX, CY))
    surf.blit(text_surf, text_rect)
    # subtle border
    pygame.draw.rect(surf, (50, 65, 95, 255), (0, 0, SIZE, SIZE), 2)
    return surf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.font.init()

    repo_root = Path(__file__).parent
    assets_dir = repo_root / "assets"

    print("Generating Stratego game assets …\n")

    # ---- Piece images --------------------------------------------------------
    for rank_name, label, bg_colour in _PIECES:
        out_dir = assets_dir / "pieces" / rank_name
        out_dir.mkdir(parents=True, exist_ok=True)
        surface = _make_piece(rank_name, label, bg_colour)
        out_path = out_dir / f"{rank_name}.png"
        pygame.image.save(surface, str(out_path))
        print(f"  ✓  {out_path.relative_to(repo_root)}")

    # ---- Board tiles ----------------------------------------------------------
    board_dir = assets_dir / "board"
    board_dir.mkdir(parents=True, exist_ok=True)

    tiles: list[tuple[str, pygame.Surface]] = [
        ("cell_light.png",  _make_cell_light()),
        ("cell_dark.png",   _make_cell_dark()),
        ("cell_lake.png",   _make_cell_lake()),
        ("cell_hidden.png", _make_cell_hidden()),
    ]
    for filename, surface in tiles:
        out_path = board_dir / filename
        pygame.image.save(surface, str(out_path))
        print(f"  ✓  {out_path.relative_to(repo_root)}")

    pygame.quit()

    total = len(_PIECES) + len(tiles)
    print(f"\n{total} assets written to: {assets_dir.relative_to(repo_root)}/")
    print("\nNext steps:")
    print("  1. Review the generated images (assets/pieces/ and assets/board/)")
    print("  2. Replace any image with a higher-quality hand-drawn version if desired")
    print("  3. Commit the assets/  directory:  git add assets/ && git commit")


if __name__ == "__main__":
    main()

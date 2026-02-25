#!/usr/bin/env python3
"""
generate_assets.py

Downloads real Stratego piece images from Wikimedia Commons (CC BY-SA 4.0,
author Mliu92) and generates board tile images using pygame-ce.

Run once from the repository root after installing project dependencies::

    pip install pygame-ce
    python generate_assets.py

Output structure::

    assets/
    ├── board/
    │   ├── cell_dark.png        ← dark board cell (alternating)
    │   ├── cell_hidden.png      ← fog-of-war tile for opponent pieces
    │   ├── cell_lake.png        ← impassable lake cell
    │   └── cell_light.png       ← light board cell (alternating)
    └── pieces/
        ├── <rank>/
        │   ├── <rank>.png       ← default (Red) piece image
        │   ├── red/<rank>.png   ← Red player piece
        │   └── blue/<rank>.png  ← Blue player piece
        └── …  (12 rank directories)

Image sources
-------------
Piece images: Wikimedia Commons, CC BY-SA 4.0
  https://commons.wikimedia.org/wiki/Category:Stratego
  Author: Mliu92  (https://commons.wikimedia.org/wiki/User:Mliu92)

Board tiles: generated with pygame-ce using the project colour palette.
"""
from __future__ import annotations

import math
import os
import sys
import urllib.error
import urllib.request
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
# Wikimedia Commons piece image URLs
#
# Thumbnail PNG URLs derived from the Wikimedia API — CC BY-SA 4.0
# (https://creativecommons.org/licenses/by-sa/4.0/)
# Author: Mliu92 — https://commons.wikimedia.org/wiki/User:Mliu92
#
# URL pattern:
#   https://upload.wikimedia.org/wikipedia/commons/thumb/{h1}/{h12}/{file}/64px-{file}.png
# where h1/h12 are the Wikimedia content-hash directory prefixes.
# ---------------------------------------------------------------------------

_BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb"

# Mapping: rank_name → (red_thumb_url, blue_thumb_url)
_PIECE_URLS: dict[str, tuple[str, str]] = {
    "flag": (
        f"{_BASE}/2/21/Stratego_RF.svg/64px-Stratego_RF.svg.png",
        f"{_BASE}/5/5d/Stratego_BF.svg/64px-Stratego_BF.svg.png",
    ),
    "spy": (
        f"{_BASE}/4/4e/Stratego_RS.svg/64px-Stratego_RS.svg.png",
        f"{_BASE}/7/7d/Stratego_BS.svg/64px-Stratego_BS.svg.png",
    ),
    "scout": (
        f"{_BASE}/6/63/Stratego_R02.svg/64px-Stratego_R02.svg.png",
        f"{_BASE}/0/04/Stratego_B02.svg/64px-Stratego_B02.svg.png",
    ),
    "miner": (
        f"{_BASE}/e/e9/Stratego_R03.svg/64px-Stratego_R03.svg.png",
        f"{_BASE}/2/2d/Stratego_B03.svg/64px-Stratego_B03.svg.png",
    ),
    "sergeant": (
        f"{_BASE}/c/cc/Stratego_R04.svg/64px-Stratego_R04.svg.png",
        f"{_BASE}/a/a2/Stratego_B04.svg/64px-Stratego_B04.svg.png",
    ),
    "lieutenant": (
        f"{_BASE}/c/cf/Stratego_R05.svg/64px-Stratego_R05.svg.png",
        f"{_BASE}/4/44/Stratego_B05.svg/64px-Stratego_B05.svg.png",
    ),
    "captain": (
        f"{_BASE}/5/55/Stratego_R06.svg/64px-Stratego_R06.svg.png",
        f"{_BASE}/2/22/Stratego_B06.svg/64px-Stratego_B06.svg.png",
    ),
    "major": (
        f"{_BASE}/a/a5/Stratego_R07.svg/64px-Stratego_R07.svg.png",
        f"{_BASE}/7/76/Stratego_B07.svg/64px-Stratego_B07.svg.png",
    ),
    "colonel": (
        f"{_BASE}/2/2b/Stratego_R08.svg/64px-Stratego_R08.svg.png",
        f"{_BASE}/b/bb/Stratego_B08.svg/64px-Stratego_B08.svg.png",
    ),
    "general": (
        f"{_BASE}/6/65/Stratego_R09.svg/64px-Stratego_R09.svg.png",
        f"{_BASE}/c/c1/Stratego_B09.svg/64px-Stratego_B09.svg.png",
    ),
    "marshal": (
        f"{_BASE}/2/27/Stratego_R10.svg/64px-Stratego_R10.svg.png",
        f"{_BASE}/8/8c/Stratego_B10.svg/64px-Stratego_B10.svg.png",
    ),
    "bomb": (
        f"{_BASE}/3/31/Stratego_RB.svg/64px-Stratego_RB.svg.png",
        f"{_BASE}/3/36/Stratego_BB.svg/64px-Stratego_BB.svg.png",
    ),
}

# Ranks in display order (matches Rank enum in src/domain/enums.py)
_RANK_ORDER: list[str] = [
    "flag", "spy", "scout", "miner", "sergeant", "lieutenant",
    "captain", "major", "colonel", "general", "marshal", "bomb",
]

# Board tile size
SIZE = 64


# ---------------------------------------------------------------------------
# Wikimedia download helper
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path) -> bool:
    """Download *url* to *dest*; return True on success, False on failure."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "StrategoGameAssetBot/1.0 "
                "(https://github.com/Ariedis/Stratego; "
                "downloading CC-BY-SA 4.0 Stratego piece images)"
            )
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, OSError) as exc:
        print(f"    ✗  download failed: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Board tile generators (pygame — no external download required)
# ---------------------------------------------------------------------------

def _make_cell_light() -> pygame.Surface:
    """Light board cell — warm tan (`COLOUR_BOARD_LIGHT` from style guide)."""
    surf = pygame.Surface((SIZE, SIZE))
    surf.fill((195, 160, 100))
    pygame.draw.line(surf, (170, 135, 80), (SIZE - 1, 0), (SIZE - 1, SIZE - 1), 1)
    pygame.draw.line(surf, (170, 135, 80), (0, SIZE - 1), (SIZE - 1, SIZE - 1), 1)
    return surf


def _make_cell_dark() -> pygame.Surface:
    """Dark board cell — deeper tan (`COLOUR_BOARD_DARK` from style guide)."""
    surf = pygame.Surface((SIZE, SIZE))
    surf.fill((160, 120, 70))
    pygame.draw.line(surf, (130, 95, 50), (SIZE - 1, 0), (SIZE - 1, SIZE - 1), 1)
    pygame.draw.line(surf, (130, 95, 50), (0, SIZE - 1), (SIZE - 1, SIZE - 1), 1)
    return surf


def _make_cell_lake() -> pygame.Surface:
    """Lake cell — deep blue with wave arcs (`COLOUR_LAKE` from style guide)."""
    surf = pygame.Surface((SIZE, SIZE))
    surf.fill((30, 80, 140))
    for row_y in (14, 30, 46):
        pygame.draw.arc(surf, (60, 130, 200),
                        (6, row_y - 4, 22, 10), 0, math.pi, 2)
        pygame.draw.arc(surf, (60, 130, 200),
                        (30, row_y - 4, 22, 10), 0, math.pi, 2)
    pygame.draw.rect(surf, (20, 55, 110), (0, 0, SIZE, SIZE), 1)
    return surf


def _make_cell_hidden() -> pygame.Surface:
    """Fog-of-war tile — dark navy with a centred '?' (`COLOUR_BG_BOARD`)."""
    surf = pygame.Surface((SIZE, SIZE))
    surf.fill((28, 38, 56))
    cx, cy = SIZE // 2, SIZE // 2
    # Use pygame's built-in font (no system font required)
    font = pygame.font.Font(None, 36)
    text_surf = font.render("?", True, (100, 120, 150))
    text_rect = text_surf.get_rect(center=(cx, cy))
    surf.blit(text_surf, text_rect)
    pygame.draw.rect(surf, (50, 65, 95), (0, 0, SIZE, SIZE), 2)
    return surf


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: C901
    pygame.init()
    pygame.font.init()

    repo_root = Path(__file__).parent
    assets_dir = repo_root / "assets"

    print("Downloading Stratego piece images from Wikimedia Commons …")
    print("  Source: https://commons.wikimedia.org/wiki/Category:Stratego")
    print("  Licence: CC BY-SA 4.0 — Author: Mliu92\n")

    ok_count = 0
    fail_count = 0

    # ---- Piece images — downloaded from Wikimedia ----------------------------
    for rank_name in _RANK_ORDER:
        red_url, blue_url = _PIECE_URLS[rank_name]

        red_dir = assets_dir / "pieces" / rank_name / "red"
        blue_dir = assets_dir / "pieces" / rank_name / "blue"
        default_dir = assets_dir / "pieces" / rank_name
        red_dir.mkdir(parents=True, exist_ok=True)
        blue_dir.mkdir(parents=True, exist_ok=True)

        # Red piece
        red_dest = red_dir / f"{rank_name}.png"
        print(f"  ↓  {rank_name}/red/{rank_name}.png", end="  ", flush=True)
        if _download(red_url, red_dest):
            # Also copy to default path so SpriteManager works without changes
            (default_dir / f"{rank_name}.png").write_bytes(red_dest.read_bytes())
            print("✓")
            ok_count += 1
        else:
            fail_count += 1

        # Blue piece
        blue_dest = blue_dir / f"{rank_name}.png"
        print(f"  ↓  {rank_name}/blue/{rank_name}.png", end="  ", flush=True)
        if _download(blue_url, blue_dest):
            print("✓")
            ok_count += 1
        else:
            fail_count += 1

    # ---- Board tiles — generated with pygame ---------------------------------
    print(f"\nGenerating board tiles …\n")
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
        print(f"  ✓  board/{filename}")
        ok_count += 1

    pygame.quit()

    # ---- Summary -------------------------------------------------------------
    total = ok_count + fail_count
    print(f"\n{ok_count}/{total} assets written to {assets_dir.relative_to(repo_root)}/")
    if fail_count:
        print(
            f"\nWARNING: {fail_count} piece image(s) failed to download.  "
            "The game will fall back to solid-colour placeholder tiles for "
            "those pieces.  Re-run this script when network access is restored.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate_assets.py

Downloads real Stratego piece images from Wikimedia Commons (CC BY-SA 4.0,
author Mliu92) and generates board tile images using Python's built-in
libraries only (no external dependencies needed for board tiles).

Run once from the repository root after installing project dependencies::

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

Board tiles: generated with Python's built-in struct/zlib (no pygame needed).
"""
from __future__ import annotations

import struct
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Wikimedia Commons piece image URLs
#
# 120 px thumbnail PNG URLs — CC BY-SA 4.0
# (https://creativecommons.org/licenses/by-sa/4.0/)
# Author: Mliu92 — https://commons.wikimedia.org/wiki/User:Mliu92
#
# Using 120 px thumbnails rather than 64 px because Wikimedia's CDN
# pre-generates the 120 px size (visible on category pages) so it is always
# available without on-the-fly rendering.  The downloaded images are
# 120×120 px; SpriteManager will render them scaled to fit the board cell.
# ---------------------------------------------------------------------------

_BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb"

# Mapping: rank_name → (red_thumb_url, blue_thumb_url)
_PIECE_URLS: dict[str, tuple[str, str]] = {
    "flag": (
        f"{_BASE}/2/21/Stratego_RF.svg/120px-Stratego_RF.svg.png",
        f"{_BASE}/5/5d/Stratego_BF.svg/120px-Stratego_BF.svg.png",
    ),
    "spy": (
        f"{_BASE}/4/4e/Stratego_RS.svg/120px-Stratego_RS.svg.png",
        f"{_BASE}/7/7d/Stratego_BS.svg/120px-Stratego_BS.svg.png",
    ),
    "scout": (
        f"{_BASE}/6/63/Stratego_R02.svg/120px-Stratego_R02.svg.png",
        f"{_BASE}/0/04/Stratego_B02.svg/120px-Stratego_B02.svg.png",
    ),
    "miner": (
        f"{_BASE}/e/e9/Stratego_R03.svg/120px-Stratego_R03.svg.png",
        f"{_BASE}/2/2d/Stratego_B03.svg/120px-Stratego_B03.svg.png",
    ),
    "sergeant": (
        f"{_BASE}/c/cc/Stratego_R04.svg/120px-Stratego_R04.svg.png",
        f"{_BASE}/a/a2/Stratego_B04.svg/120px-Stratego_B04.svg.png",
    ),
    "lieutenant": (
        f"{_BASE}/c/cf/Stratego_R05.svg/120px-Stratego_R05.svg.png",
        f"{_BASE}/4/44/Stratego_B05.svg/120px-Stratego_B05.svg.png",
    ),
    "captain": (
        f"{_BASE}/5/55/Stratego_R06.svg/120px-Stratego_R06.svg.png",
        f"{_BASE}/2/22/Stratego_B06.svg/120px-Stratego_B06.svg.png",
    ),
    "major": (
        f"{_BASE}/a/a5/Stratego_R07.svg/120px-Stratego_R07.svg.png",
        f"{_BASE}/7/76/Stratego_B07.svg/120px-Stratego_B07.svg.png",
    ),
    "colonel": (
        f"{_BASE}/2/2b/Stratego_R08.svg/120px-Stratego_R08.svg.png",
        f"{_BASE}/b/bb/Stratego_B08.svg/120px-Stratego_B08.svg.png",
    ),
    "general": (
        f"{_BASE}/6/65/Stratego_R09.svg/120px-Stratego_R09.svg.png",
        f"{_BASE}/c/c1/Stratego_B09.svg/120px-Stratego_B09.svg.png",
    ),
    "marshal": (
        f"{_BASE}/2/27/Stratego_R10.svg/120px-Stratego_R10.svg.png",
        f"{_BASE}/8/8c/Stratego_B10.svg/120px-Stratego_B10.svg.png",
    ),
    "bomb": (
        f"{_BASE}/3/31/Stratego_RB.svg/120px-Stratego_RB.svg.png",
        f"{_BASE}/3/36/Stratego_BB.svg/120px-Stratego_BB.svg.png",
    ),
}

# Ranks in display order (matches Rank enum in src/domain/enums.py)
_RANK_ORDER: list[str] = [
    "flag", "spy", "scout", "miner", "sergeant", "lieutenant",
    "captain", "major", "colonel", "general", "marshal", "bomb",
]

# ---------------------------------------------------------------------------
# Download helper with retry
# ---------------------------------------------------------------------------

# Use a browser-like User-Agent so Wikimedia's CDN serves the images correctly.
_USER_AGENT = (
    "Mozilla/5.0 (compatible; StrategoAssetDownloader/1.0; "
    "+https://github.com/Ariedis/Stratego)"
)
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0  # seconds between retries


def _download(url: str, dest: Path) -> bool:
    """Download *url* to *dest*; return True on success, False on failure.

    Retries up to ``_MAX_RETRIES`` times on transient errors (5xx, timeouts).
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                data = resp.read()
            if len(data) < 100:  # sanity-check: a valid PNG is never this small
                print(
                    f"    ✗  received {len(data)} bytes (expected a PNG image)",
                    file=sys.stderr,
                )
                return False
            dest.write_bytes(data)
            return True
        except urllib.error.HTTPError as exc:
            print(
                f"    ✗  HTTP {exc.code} {exc.reason} (attempt {attempt}/{_MAX_RETRIES})",
                file=sys.stderr,
            )
            if exc.code < 500:  # 4xx errors will not recover on retry
                return False
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(
                f"    ✗  {type(exc).__name__}: {exc} (attempt {attempt}/{_MAX_RETRIES})",
                file=sys.stderr,
            )
        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_DELAY)
    return False


# ---------------------------------------------------------------------------
# Pure-Python PNG writer — no external dependencies required
#
# Supports 64×64 RGB (24-bit) PNG files.  Used for board tile generation so
# that the script works headlessly without pygame or any other library.
# ---------------------------------------------------------------------------

def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _write_png(path: Path, pixels: list[list[tuple[int, int, int]]]) -> None:
    """Write *pixels* (list of rows, each a list of (R,G,B) tuples) as a PNG."""
    height = len(pixels)
    width = len(pixels[0]) if height else 0

    # Serialise rows with filter-type byte 0 (None) prepended to each row.
    raw = b"".join(
        b"\x00" + bytes(channel for r, g, b in row for channel in (r, g, b))
        for row in pixels
    )
    compressed = zlib.compress(raw, 9)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


# ---------------------------------------------------------------------------
# Board tile pixel generators — 64×64 RGB
# ---------------------------------------------------------------------------

_SIZE = 64
_DARK_EDGE_AMOUNT = 25  # how much to darken edge pixels


def _darken(r: int, g: int, b: int, amt: int) -> tuple[int, int, int]:
    return (max(0, r - amt), max(0, g - amt), max(0, b - amt))


def _make_cell_pixels(
    base: tuple[int, int, int],
    *,
    dark_edges: bool = True,
) -> list[list[tuple[int, int, int]]]:
    """Return a 64×64 pixel grid filled with *base* colour and optional edge darkening."""
    r, g, b = base
    edge = _darken(r, g, b, _DARK_EDGE_AMOUNT)
    rows: list[list[tuple[int, int, int]]] = []
    for y in range(_SIZE):
        row: list[tuple[int, int, int]] = []
        for x in range(_SIZE):
            if dark_edges and (x == _SIZE - 1 or y == _SIZE - 1):
                row.append(edge)
            else:
                row.append((r, g, b))
        rows.append(row)
    return rows


def _make_cell_lake_pixels() -> list[list[tuple[int, int, int]]]:
    """64×64 deep-blue lake tile with simple horizontal wave stripes."""
    base = (30, 80, 140)
    wave = (60, 130, 200)
    border = (20, 55, 110)
    rows = _make_cell_pixels(base, dark_edges=False)
    # Horizontal wave stripes at y = 14, 30, 46
    for wave_y in (14, 30, 46):
        for x in range(6, 54):
            rows[wave_y][x] = wave
    # 1-px border
    for i in range(_SIZE):
        rows[0][i] = border
        rows[_SIZE - 1][i] = border
        rows[i][0] = border
        rows[i][_SIZE - 1] = border
    return rows


def _make_cell_hidden_pixels() -> list[list[tuple[int, int, int]]]:
    """64×64 dark-navy fog-of-war tile with a 2-px border."""
    base = (28, 38, 56)
    border = (50, 65, 95)
    rows = _make_cell_pixels(base, dark_edges=False)
    # 2-px border
    for i in range(_SIZE):
        for b_off in (0, 1):
            rows[b_off][i] = border
            rows[_SIZE - 1 - b_off][i] = border
            rows[i][b_off] = border
            rows[i][_SIZE - 1 - b_off] = border
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).parent
    assets_dir = repo_root / "assets"

    print("Downloading Stratego piece images from Wikimedia Commons ...")
    print("  Source: https://commons.wikimedia.org/wiki/Category:Stratego")
    print("  Licence: CC BY-SA 4.0 -- Author: Mliu92")
    print()

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
        print(f"  -> {rank_name}/red/{rank_name}.png", end="  ", flush=True)
        if _download(red_url, red_dest):
            # Copy to default path so SpriteManager works without extra changes
            (default_dir / f"{rank_name}.png").write_bytes(red_dest.read_bytes())
            print("OK")
            ok_count += 1
        else:
            fail_count += 1

        # Blue piece
        blue_dest = blue_dir / f"{rank_name}.png"
        print(f"  -> {rank_name}/blue/{rank_name}.png", end="  ", flush=True)
        if _download(blue_url, blue_dest):
            print("OK")
            ok_count += 1
        else:
            fail_count += 1

    # ---- Board tiles — generated with pure Python (no pygame required) -------
    print()
    print("Generating board tiles ...")
    print()
    board_dir = assets_dir / "board"
    board_dir.mkdir(parents=True, exist_ok=True)

    board_tiles: list[tuple[str, list[list[tuple[int, int, int]]]]] = [
        ("cell_light.png",  _make_cell_pixels((195, 160, 100))),
        ("cell_dark.png",   _make_cell_pixels((160, 120, 70))),
        ("cell_lake.png",   _make_cell_lake_pixels()),
        ("cell_hidden.png", _make_cell_hidden_pixels()),
    ]
    for filename, pixels in board_tiles:
        out_path = board_dir / filename
        _write_png(out_path, pixels)
        print(f"  OK  board/{filename}")
        ok_count += 1

    # ---- Summary -------------------------------------------------------------
    total = ok_count + fail_count
    print()
    print(f"{ok_count}/{total} assets written to {assets_dir.relative_to(repo_root)}/")
    if fail_count:
        print(
            f"\nWARNING: {fail_count} piece image(s) failed to download. "
            "The game will fall back to solid-colour placeholder tiles for "
            "those pieces. Re-run this script when network access is restored.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

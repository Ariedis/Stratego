# Asset Inventory & Sourcing Guide: Game Images

**Version:** v0.1 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-25  
**Status:** Draft – ready for developer implementation  
**Specification refs:**
- [`system_design.md §2.4`](../specifications/system_design.md) — `SpriteManager` described
- [`game_components.md §3`](../specifications/game_components.md) — piece inventory
- [`ux-visual-style-guide.md`](./ux-visual-style-guide.md) — colour palette

---

## 1. Purpose

This document is the authoritative asset specification for all game images
required by *Conqueror's Quest*. It exists because the current `SpriteManager`
(`src/presentation/sprite_manager.py`) falls back to **solid-colour placeholder
rectangles** whenever a real image file is not found. Providing proper artwork
replaces every placeholder with polished game art.

The document covers:

1. **Asset inventory** — every image file that must exist, with its exact path
2. **Sizing & format requirements** for each image category
3. **Visual design brief** for each piece, so images are legible and on-brand
4. **Recommended sources** where compliant images can be found or derived
5. **Placement instructions** for the developer who fetches/creates the files

---

## 2. Directory Structure Expected by the Code

`SpriteManager._load_rank_surface()` constructs image paths using the pattern:

```
assets/pieces/<rank_lower>/<rank_lower>.png
```

where `<rank_lower>` is the rank name in lowercase (e.g. `marshal`, `bomb`).
The `assets/` root is resolved from the repository root at runtime:

```python
asset_dir = Path(__file__).parent.parent / "assets"
#  resolves to:  <repo_root>/assets/
```

The full expected directory tree is therefore:

```
<repo_root>/
└── assets/
    ├── board/
    │   ├── cell_light.png     ← light board cell tile (empty normal square)
    │   ├── cell_dark.png      ← dark board cell tile  (empty normal square, alternating)
    │   ├── cell_lake.png      ← lake / water cell tile (impassable)
    │   └── cell_hidden.png    ← fog-of-war tile for face-down opponent pieces
    └── pieces/
        ├── flag/
        │   └── flag.png
        ├── spy/
        │   └── spy.png
        ├── scout/
        │   └── scout.png
        ├── miner/
        │   └── miner.png
        ├── sergeant/
        │   └── sergeant.png
        ├── lieutenant/
        │   └── lieutenant.png
        ├── captain/
        │   └── captain.png
        ├── major/
        │   └── major.png
        ├── colonel/
        │   └── colonel.png
        ├── general/
        │   └── general.png
        ├── marshal/
        │   └── marshal.png
        └── bomb/
            └── bomb.png
```

> **Important:** Sub-directory names and file names must use the **lowercase
> rank name** exactly as it appears in `Rank(IntEnum)` in
> `src/domain/enums.py`. All file names must end in `.png`.

---

## 3. Complete Asset Inventory

### 3.1 Piece Images (12 files required)

| Rank | Rank value | File path | Placeholder colour (current fallback) |
|---|---|---|---|
| Flag | 0 | `assets/pieces/flag/flag.png` | Gold `rgb(255, 215, 0)` / `#FFD700` |
| Spy | 1 | `assets/pieces/spy/spy.png` | Purple `rgb(128, 0, 128)` / `#800080` |
| Scout | 2 | `assets/pieces/scout/scout.png` | Dodger blue `rgb(0, 128, 255)` / `#0080FF` |
| Miner | 3 | `assets/pieces/miner/miner.png` | Brown `rgb(139, 90, 43)` / `#8B5A2B` |
| Sergeant | 4 | `assets/pieces/sergeant/sergeant.png` | Steel blue `rgb(70, 130, 180)` / `#4682B4` |
| Lieutenant | 5 | `assets/pieces/lieutenant/lieutenant.png` | Medium sea-green `rgb(60, 179, 113)` / `#3CB371` |
| Captain | 6 | `assets/pieces/captain/captain.png` | Orange `rgb(255, 165, 0)` / `#FFA500` |
| Major | 7 | `assets/pieces/major/major.png` | Crimson `rgb(220, 20, 60)` / `#DC143C` |
| Colonel | 8 | `assets/pieces/colonel/colonel.png` | Dim grey `rgb(105, 105, 105)` / `#696969` |
| General | 9 | `assets/pieces/general/general.png` | Medium blue `rgb(0, 0, 205)` / `#0000CD` |
| Marshal | 10 | `assets/pieces/marshal/marshal.png` | Black `rgb(0, 0, 0)` / `#000000` |
| Bomb | 99 | `assets/pieces/bomb/bomb.png` | Near-black `rgb(50, 50, 50)` / `#323232` |

### 3.2 Board / Tile Images (4 files — board enhancement)

The `SpriteManager` currently creates these as solid-colour surfaces.
Providing real image files at the paths below allows the renderer to
be updated to display proper board textures.

| Surface | File path | Placeholder colour (current) |
|---|---|---|
| Fog-of-war / hidden enemy piece | `assets/board/cell_hidden.png` | Dark grey `rgb(40, 40, 40)` / `#282828` |
| Lake / impassable cell | `assets/board/cell_lake.png` | Blue `rgb(0, 100, 200)` / `#0064C8` |
| Empty normal cell (light) | `assets/board/cell_light.png` | Forest green `rgb(34, 139, 34)` / `#228B22` |
| Empty normal cell (dark) | `assets/board/cell_dark.png` | Darker forest green `rgb(27, 112, 27)` / `#1B701B` |

---

## 4. Image Format & Sizing Requirements

| Property | Requirement | Rationale |
|---|---|---|
| **Format** | PNG with alpha channel (RGBA 32-bit) | Allows transparent corners so pieces look circular/shaped on any background |
| **Canvas size** | **64 × 64 pixels** | `SpriteManager._make_placeholder` uses 64×64 as the canonical size; pygame renders at this size by default |
| **Content area** | Central 56 × 56 px (4 px transparent padding on all sides) | Avoids hard clipping at the tile boundary on the rendered board |
| **DPI** | 72 dpi (screen only) | pygame renders at screen resolution; higher DPI adds file size with no visual benefit |
| **Colour space** | sRGB | All pygame surfaces use sRGB |
| **Alpha** | Straight (non-premultiplied) alpha | Compatible with `pygame.image.load` default behaviour |
| **Filename** | All lowercase, `.png` extension | Required by the path-construction logic in `SpriteManager._load_rank_surface()` |

---

## 5. Visual Design Brief for Each Piece

Each piece image must communicate **rank identity at a glance** from a typical
viewing distance across a laptop or desktop monitor. The design language
follows the medieval/military theme of classic Stratego.

### 5.1 Common Piece Layout (Neutral / Grayscale Master)

All pieces should be produced as a **neutral grayscale badge**. Team colour
(Red `#C83C3C` or Blue `#3C6ED2` from the Visual Style Guide) is then applied
by tinting at render time — or by providing separate `red/` and `blue/`
sub-directories if tinting is not yet implemented in code (see §8 Open
Questions).

```
+──────────────────────────────+
│          (4 px pad)          │
│   ╭──────────────────────╮   │
│   │   RANK NUMBER        │   │  ← bold, centred, white
│   │   ─────────────      │   │
│   │   RANK ICON          │   │  ← thematic icon, 20–24 px
│   ╰──────────────────────╯   │
│          (4 px pad)          │
+──────────────────────────────+

Circle fill:   mid-grey   #808080  (neutral; tinted at runtime)
Circle border: 2 px ring  #404040
Rank number:   white      #FFFFFF, bold, 22–26 px sans-serif
```

### 5.2 Per-Rank Icon Brief

| Rank | Text shown | Thematic icon suggestion | Special rule to reinforce visually |
|---|---|---|---|
| Flag | `F` or `⚑` | Waving pennant / banner | Game-ending capture target |
| Spy | `1` | Eye or dagger silhouette | Unique: defeats Marshal if attacking |
| Scout | `2` | Running figure or binoculars | Unique: unlimited straight-line movement |
| Miner | `3` | Pickaxe or crossed tools | Unique: defuses Bombs |
| Sergeant | `4` | Single chevron stripe | Standard combat rank |
| Lieutenant | `5` | Single horizontal bar | Standard combat rank |
| Captain | `6` | Double horizontal bars | Standard combat rank |
| Major | `7` | Gold oak leaf | Standard combat rank |
| Colonel | `8` | Silver eagle | Standard combat rank |
| General | `9` | Single five-pointed star | Near-top rank |
| Marshal | `10` | Crossed batons or crown | Highest rank; defeated only by Spy |
| Bomb | `B` | Explosion burst or shell | Immovable; defeats all except Miner |

### 5.3 Hidden (Fog-of-War) Piece Tile

Used for any opponent piece whose rank has not yet been revealed through
combat. Requirements:

- Dark navy background circle: `#1C2638` (matches `COLOUR_BG_BOARD`)
- Subtle 1 px border: `#32415F`
- Large centred `?` character, grey `#808080`, bold, 28 px
- No rank number or icon visible

### 5.4 Board Cell Tiles

| Tile | Visual design | Colour reference |
|---|---|---|
| Light cell | Wood-grain or parchment texture | `#C3A064` (`COLOUR_BOARD_LIGHT` from style guide) |
| Dark cell | Darker wood grain | `#A07846` (`COLOUR_BOARD_DARK` from style guide) |
| Lake cell | Water / ripple texture | `#1E508C` (`COLOUR_LAKE` from style guide) |
| Hidden piece tile | Dark badge with `?` | `#1C2638` background, `#32415F` border |

---

## 6. Recommended Image Sources

Because this project is not distributed for sale (confirmed in the issue
description), copyright is not a blocking concern. The following sources are
recommended in priority order.

### 6.1 Wikimedia Commons — Public Domain & Creative Commons

Search for Stratego-related artwork:

- `https://commons.wikimedia.org/wiki/Category:Stratego`
- `https://commons.wikimedia.org/w/index.php?search=stratego+piece`

Individual piece illustrations are available under CC BY-SA or are in the
public domain. SVG format is preferred (scalable to any resolution); export to
64×64 RGBA PNG.

### 6.2 OpenGameArt.org — Open Licence Game Art

OpenGameArt hosts free game art under GPL, CC, or public-domain licences:

- `https://opengameart.org/art-search?keys=stratego`
- `https://opengameart.org/art-search?keys=board+game+pieces`
- `https://opengameart.org/art-search?keys=military+tokens`

A set of 12+ circular military rank badge sprites serves as an ideal starting
point for the piece design.

### 6.3 The Noun Project — Thematic SVG Icons

The Noun Project offers extensive military and thematic icon libraries usable
as rank symbols (composite onto the circular badge):

- `https://thenounproject.com/search/?q=military+rank`
- `https://thenounproject.com/search/?q=bomb+icon`
- `https://thenounproject.com/search/?q=flag+icon`
- `https://thenounproject.com/search/?q=pickaxe+icon`

Download as SVG, composite over the neutral badge circle, export at 64×64 PNG.

### 6.4 BoardGameGeek — Scanned Classic Stratego Artwork

The original Hasbro/Jumbo Stratego piece artwork is documented by the
collector community:

- `https://boardgamegeek.com/boardgame/1/stratego/images`
- Image galleries and forum threads on BGG frequently include high-resolution
  scans of classic Stratego piece cards.

Crop individual pieces to 64×64, adjust contrast, and export as RGBA PNG.

### 6.5 AI Image Generation (Last Resort)

If no suitable existing asset is found, AI image generation tools
(Midjourney, DALL-E, Stable Diffusion) can produce consistent badge art.

Suggested prompt template (adjust `[RANK NAME]` and `[ICON DESCRIPTION]`):

> *"Circular military rank badge, medieval fantasy theme, [RANK NAME] text
> centred at top, [ICON DESCRIPTION] symbol below, isolated on transparent
> background, 64×64 pixel game token, clean flat icon style, neutral grey
> base colour, no other colours"*

Generate all 12 pieces in a single session with the same prompt structure to
ensure a consistent visual style.

---

## 7. Developer Placement Instructions

Follow these steps to source and place images:

1. **Create the directory structure**:
   ```
   mkdir -p assets/pieces/flag assets/pieces/spy assets/pieces/scout \
            assets/pieces/miner assets/pieces/sergeant assets/pieces/lieutenant \
            assets/pieces/captain assets/pieces/major assets/pieces/colonel \
            assets/pieces/general assets/pieces/marshal assets/pieces/bomb \
            assets/board
   ```

2. **Download or generate images** using one of the sources in §6; one PNG
   per rank subdirectory, named `<rank>.png` (all lowercase).

3. **Verify dimensions** — confirm every piece PNG is 64×64 px:
   ```
   python -c "
   from PIL import Image
   from pathlib import Path
   for p in Path('assets/pieces').rglob('*.png'):
       img = Image.open(p)
       assert img.size == (64, 64), f'{p}: {img.size}'
       print(f'{p}: OK')
   "
   ```

4. **Verify alpha channel** — open each image; confirm the area outside the
   circular badge is transparent (not white or solid-colour).

5. **Smoke-test in-game** — run `python -m src` and start a game; every piece
   should display its artwork rather than a solid-colour rectangle. Debug
   messages from `SpriteManager` appear in the log when files are missing.

6. **Team colour variants** (if tinting is not implemented in code): place
   both colour variants at:
   - `assets/pieces/<rank>/red/<rank>.png`
   - `assets/pieces/<rank>/blue/<rank>.png`

   > **Note:** `SpriteManager.get_surface()` currently ignores the `owner`
   > (`PlayerSide`) parameter. A future sprint should implement tinting or
   > dual-path logic so the same neutral image is colourised per team.

---

## 8. Open Questions

- [ ] **Team colour strategy:** Should a single neutral image per rank be
  provided and team colour applied via tinting in `SpriteManager.get_surface()`
  (requires a code change), or should two image variants be provided per rank
  in `red/` and `blue/` sub-directories (no code change required)?
- [ ] **Board cell style:** Should cell tiles be a single 64×64 repeating tile
  (simple implementation) or a full 640×640 pre-rendered board texture (higher
  fidelity but requires renderer change)?
- [ ] **Combat-revealed badge:** Should pieces that have been revealed through
  combat display a distinct visual treatment (e.g. a glowing or pulsing border)
  to communicate their revealed state?
- [ ] **Immovable piece distinction:** Should Bomb and Flag pieces look
  visually different from moveable pieces on the owning player's side (e.g.
  square corners vs. rounded) to help the player track them during setup?
- [ ] **Rank abbreviations on pieces:** Classic Stratego uses rank numbers
  (1–10, B, F). Should this game retain that convention or use rank-name
  abbreviations (e.g. "Sp", "Sc", "Mi") for accessibility?

---

## 9. UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Images sourced from different sources creating a visually inconsistent set | High | Medium | Use a single source or create a base badge template and apply consistent styling to all 12 pieces before exporting |
| Rank number not legible at 64×64 on a 1280×720 display | Medium | High | Preview all pieces at 100 % zoom on target display before finalising; minimum 22 px bold font |
| Transparent alpha not preserved on export | Medium | Medium | Always save as PNG-32 (RGBA) not PNG-8 or JPEG; verify in image editor before committing |
| Team colour ambiguity because `SpriteManager` does not yet tint by `PlayerSide` | High | High | Either provide separate red/blue variants, or implement tinting sprint before v1.0 release |
| Missing files cause silent fallback to placeholder colours in production | Low | Low | `SpriteManager` already logs `DEBUG` warnings; add a startup asset-check that prints a warning for each missing file |

---

## 10. Related Documents

| Document | Relevance |
|---|---|
| [`planning/ux-visual-style-guide.md`](./ux-visual-style-guide.md) | Colour palette, typography — piece images must be consistent |
| [`planning/ux-wireframe-playing.md`](./ux-wireframe-playing.md) | Shows how pieces appear at full size on the Playing Screen |
| [`planning/ux-wireframe-setup.md`](./ux-wireframe-setup.md) | Shows piece tray and board during the setup phase |
| [`src/presentation/sprite_manager.py`](../src/presentation/sprite_manager.py) | Implementation that loads these assets; defines expected file paths |
| [`specifications/game_components.md §3`](../specifications/game_components.md) | Authoritative piece inventory (ranks, counts, special abilities) |

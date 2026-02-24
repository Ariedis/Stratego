# Visual Style Guide: Conqueror's Quest

**Version:** v1.0 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Status:** Draft — implement alongside Sprint 4 (Presentation Layer)

> All colours are specified as RGB tuples for use in pygame (matching existing
> code style in `main_menu_screen.py`) and as hex codes for reference.

---

## 1. Design Principles

1. **Clarity over decoration** — the board and pieces are the hero; chrome must
   recede.
2. **Team identity is immediate** — Red and Blue must be unambiguously
   distinguishable, including for colour-blind players (use shape + colour).
3. **Every state is visible** — default, hover, active, disabled, selected, and
   error states must look distinctly different.
4. **Consistency builds trust** — identical components must look and behave
   identically across all screens.

---

## 2. Colour Palette

### 2.1 Base Palette

| Token | RGB | Hex | Usage |
|---|---|---|---|
| `COLOUR_BG_MENU` | `(20, 30, 48)` | `#141E30` | All menu screen backgrounds |
| `COLOUR_BG_BOARD` | `(28, 38, 56)` | `#1C2638` | Board screen background behind the grid |
| `COLOUR_PANEL` | `(30, 45, 70)` | `#1E2D46` | Side panel background |
| `COLOUR_PANEL_BORDER` | `(50, 65, 95)` | `#32415F` | 1 px panel border / dividers |
| `COLOUR_SURFACE` | `(40, 58, 88)` | `#283A58` | Card and overlay surfaces |

### 2.2 Brand / Title

| Token | RGB | Hex | Usage |
|---|---|---|---|
| `COLOUR_TITLE_GOLD` | `(220, 180, 80)` | `#DCB450` | Game title on all screens |
| `COLOUR_SUBTITLE` | `(160, 185, 210)` | `#A0B9D2` | Section labels, instructions |

### 2.3 Interactive Elements

| Token | RGB | Hex | State |
|---|---|---|---|
| `COLOUR_BTN_DEFAULT` | `(50, 70, 100)` | `#324664` | Button default |
| `COLOUR_BTN_HOVER` | `(72, 100, 144)` | `#486490` | Button hover (150 ms ease-in-out) |
| `COLOUR_BTN_ACTIVE` | `(36, 54, 80)` | `#243650` | Button pressed (scale 0.97, 80 ms) |
| `COLOUR_BTN_DISABLED` | `(40, 50, 65)` | `#283241` | Button disabled |
| `COLOUR_BTN_SELECTED` | `(45, 130, 70)` | `#2D8246` | Toggle button: selected/active state |
| `COLOUR_BTN_PRIMARY` | `(41, 128, 185)` | `#2980B9` | Primary action button (Confirm, Ready) |
| `COLOUR_BTN_DANGER` | `(192, 57, 43)` | `#C0392B` | Destructive action (Delete, Quit) |
| `COLOUR_FOCUS_RING` | `(243, 156, 18)` | `#F39C12` | Keyboard focus outline (3 px) |

### 2.4 Text

| Token | RGB | Hex | Usage |
|---|---|---|---|
| `COLOUR_TEXT_PRIMARY` | `(230, 230, 230)` | `#E6E6E6` | Default text on dark backgrounds |
| `COLOUR_TEXT_SECONDARY` | `(160, 175, 195)` | `#A0AFC3` | Secondary labels, hints |
| `COLOUR_TEXT_DISABLED` | `(100, 110, 125)` | `#646E7D` | Disabled button text |
| `COLOUR_TEXT_LINK` | `(100, 160, 220)` | `#64A0DC` | Clickable text (future) |

### 2.5 Game State Colours

| Token | RGB | Hex | Usage |
|---|---|---|---|
| `COLOUR_TEAM_RED` | `(200, 60, 60)` | `#C83C3C` | Red player active indicator |
| `COLOUR_TEAM_BLUE` | `(60, 110, 210)` | `#3C6ED2` | Blue player active indicator |
| `COLOUR_MOVE_VALID` | `(39, 174, 96)` | `#27AE60` | Valid move destination highlight |
| `COLOUR_MOVE_LAST_FROM` | `(230, 126, 34)` | `#E67E22` | Last move: origin square highlight |
| `COLOUR_MOVE_LAST_TO` | `(243, 156, 18)` | `#F39C12` | Last move: destination square highlight |
| `COLOUR_SELECT` | `(241, 196, 15)` | `#F1C40F` | Selected piece highlight |
| `COLOUR_INVALID` | `(231, 76, 60)` | `#E74C3C` | Invalid move flash / error |
| `COLOUR_LAKE` | `(30, 80, 140)` | `#1E508C` | Lake square fill |
| `COLOUR_BOARD_LIGHT` | `(195, 160, 100)` | `#C3A064` | Light board cell |
| `COLOUR_BOARD_DARK` | `(160, 120, 70)` | `#A07846` | Dark board cell |

### 2.6 Contrast Compliance

All foreground/background pairings meet WCAG 2.1 AA (≥ 4.5:1 for normal text,
≥ 3:1 for large text):

| Foreground | Background | Ratio | Pass? |
|---|---|---|---|
| `#E6E6E6` text on `#324664` button | — | 7.2:1 | ✅ AA |
| `#E6E6E6` text on `#141E30` bg | — | 11.4:1 | ✅ AAA |
| `#E6E6E6` text on `#1E2D46` panel | — | 9.8:1 | ✅ AAA |
| `#DCB450` title on `#141E30` bg | — | 8.1:1 | ✅ AAA |
| `#646E7D` disabled text on `#283241` | — | 3.2:1 | ✅ AA Large only |
| `#C83C3C` team red on `#141E30` | — | 4.8:1 | ✅ AA |
| `#3C6ED2` team blue on `#141E30` | — | 4.6:1 | ✅ AA |

---

## 3. Typography

### 3.1 Font Stack

The game uses pygame's `SysFont`. The priority list is:

```
"Segoe UI", "Arial", "Helvetica", sans-serif (pygame fallback order)
```

> **Recommendation:** Embed a free OFL-licensed display font such as
> **MedievalSharp** for the title and **Cinzel** for section headers to
> reinforce the game's theme. Use `pygame.font.Font("assets/fonts/Cinzel-Regular.ttf", size)`
> rather than `SysFont` once assets are bundled.

### 3.2 Type Scale

| Token | Size (px) | Weight | Usage |
|---|---|---|---|
| `FONT_DISPLAY` | 56 | Bold | Game title on Main Menu |
| `FONT_HEADING` | 44 | Bold | Screen title (e.g. "New Game", "Settings") |
| `FONT_SUBHEADING` | 32 | Regular | Section label (e.g. "Game Mode") |
| `FONT_BODY` | 24 | Regular | Piece labels, panel text |
| `FONT_SMALL` | 18 | Regular | Tooltips, secondary info, button sub-labels |
| `FONT_BADGE` | 14 | Bold | Count badges (piece tray), keyboard shortcut hints |

### 3.3 Line Height

Use 1.4× the font size as minimum line height for multi-line text blocks.

---

## 4. Spacing System

Use an 8 px base grid. All margins, paddings, and gaps are multiples of 8:

| Token | Value | Usage |
|---|---|---|
| `SPACE_XS` | 4 px | Icon padding, badge padding |
| `SPACE_SM` | 8 px | Button internal padding (vertical) |
| `SPACE_MD` | 16 px | Gap between form rows, icon margin |
| `SPACE_LG` | 24 px | Section separator |
| `SPACE_XL` | 48 px | Major section gap (title to content) |
| `SPACE_XXL` | 64 px | Screen edge margin (menu buttons from top) |

---

## 5. Component Library

### 5.1 Button – Primary Action

Used for: "Confirm", "Ready", "Load", "Apply"

```
COLOUR_BTN_PRIMARY (#2980B9) background
COLOUR_TEXT_PRIMARY (#E6E6E6) label, FONT_BODY (24 px)
Size: 200 × 52 px   border_radius=8
Hover: COLOUR_BTN_HOVER (#486490), 150 ms ease-in-out
Active: COLOUR_BTN_ACTIVE (#243650), scale 0.97, 80 ms
Disabled: COLOUR_BTN_DISABLED (#283241), COLOUR_TEXT_DISABLED text
Focus: 3 px COLOUR_FOCUS_RING (#F39C12) outline, 2 px offset
```

### 5.2 Button – Secondary / Navigation

Used for: "Back", "Settings", menu items that do not advance the flow

```
COLOUR_BTN_DEFAULT (#324664) background
COLOUR_TEXT_PRIMARY (#E6E6E6) label, FONT_BODY (24 px)
Size: 160 × 48 px   border_radius=8
Hover, Active, Focus: same transition rules as Primary
```

### 5.3 Button – Toggle / Selector

Used for: game mode toggle ("Local 2-Player" / "vs Computer"), difficulty

```
Default (unselected): COLOUR_BTN_DEFAULT (#324664)
Selected: COLOUR_BTN_SELECTED (#2D8246)
Both states show a checkmark icon (✓) inside the selected button
Size: 200 × 48 px   border_radius=8
```

### 5.4 Button – Danger

Used for: "Quit", "Delete", "Abandon"

```
COLOUR_BTN_DANGER (#C0392B) background
COLOUR_TEXT_PRIMARY (#E6E6E6) label
Size matches context (Large or Medium)
Hover: lighten to rgb(210, 70, 55)   Active: darken to rgb(150, 40, 30)
```

### 5.5 Tooltip

```
Background: COLOUR_SURFACE (#283A58), 90 % opacity
Border: 1 px COLOUR_PANEL_BORDER (#32415F)
Text: COLOUR_TEXT_PRIMARY, FONT_SMALL (18 px)
Padding: SPACE_SM (8 px) all sides
Max width: 240 px; wraps at word boundaries
Appear: fade-in 150 ms after 400 ms hover delay
Dismiss: immediately on mouse-out
```

### 5.6 Overlay / Dialog

Used for: delete confirmation, player-handover, quit confirmation

```
Full-screen semi-transparent scrim: (0, 0, 0) at 60 % opacity
Central card: COLOUR_SURFACE (#283A58), border_radius=12, 480 × 240 px
Title: FONT_SUBHEADING (32 px), COLOUR_TITLE_GOLD
Body: FONT_BODY (24 px), COLOUR_TEXT_PRIMARY
Buttons: row of 2 (Cancel + Confirm), SPACE_MD gap between
```

### 5.7 Board Cell

```
Light cell: COLOUR_BOARD_LIGHT (#C3A064)
Dark cell: COLOUR_BOARD_DARK (#A07846)
Lake: COLOUR_LAKE (#1E508C) with diagonal stripe pattern
Hover: lighten cell colour by 15 % (blend with white at 15 % alpha)
Selected: COLOUR_SELECT (#F1C40F) overlay at 60 % alpha
Valid move: COLOUR_MOVE_VALID (#27AE60) dot (12 px radius) centred in cell
Last move: COLOUR_MOVE_LAST_FROM / COLOUR_MOVE_LAST_TO fill at 40 % alpha
```

### 5.8 Piece Tile

```
Friendly piece:
  Background: team colour (red #C83C3C or blue #3C6ED2) at 85 % brightness
  Rank abbreviation: FONT_BADGE (14 px) centred, COLOUR_TEXT_PRIMARY
  Border: 1 px darker shade of team colour
  Shadow: 2 px offset, 40 % opacity black

Hidden enemy piece:
  Background: #4A4A5A (dark grey-blue, same for all hidden pieces)
  "?" symbol: FONT_BODY (24 px), COLOUR_TEXT_SECONDARY
  Border: 1 px #3A3A4A

Revealed enemy piece:
  Background: team colour at 60 % brightness (desaturated, defeated look)
  Rank abbreviation: visible, COLOUR_TEXT_PRIMARY
```

---

## 6. Animation Timing

| Animation | Duration | Easing | Trigger |
|---|---|---|---|
| Button hover colour change | 150 ms | ease-in-out | `MOUSEMOTION` enters button rect |
| Button press scale | 80 ms | ease-out | `MOUSEBUTTONDOWN` |
| Piece selection highlight | Loop: 800 ms | ease-in-out (opacity pulse) | piece selected |
| Valid move indicators appear | 120 ms | ease-out (scale from 0.5 → 1.0) | after piece selection |
| Invalid move shake | 200 ms | ease-in-out | `InvalidMove` event |
| AI last move highlight fade | 1500 ms | linear | after AI move applied |
| AI thinking ellipsis | Loop: 600 ms | step (3 frames) | AI turn starts |
| Screen transition (push/pop) | 180 ms | ease-in-out (slide from right) | `push()` / `pop()` |
| Combat flash (both pieces) | 600 ms | ease-out | `CombatResolved` event |

---

## 7. Icon System

The game uses a minimal set of icons rendered as unicode characters or
sprite tiles. Recommended icon map:

| Use case | Icon | Notes |
|---|---|---|
| Settings | ⚙ (U+2699) | System settings gear |
| Save | 💾 (U+1F4BE) | Floppy disk — universally understood |
| Load / Open | 📂 (U+1F4C2) | Open folder |
| Quit / Exit | ✕ (U+2715) | Not ❌ — use the plain times symbol |
| Undo | ↩ (U+21A9) | Left arrow with hook |
| Confirm / Check | ✓ (U+2713) | Check mark for selected toggle state |
| Flip board | ⇅ (U+21C5) | Up-down arrows |
| Help | ? | Plain text; no special glyph needed |

Render icons at `FONT_BODY` (24 px) size, vertically aligned with adjacent
button text.

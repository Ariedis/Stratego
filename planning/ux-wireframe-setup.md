# Wireframe: Board Setup Screen

**Version:** v1.0 Draft  
**Screen class:** `SetupScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.6`](../specifications/screen_flow.md)

---

## Layout (1280 × 720 reference)

```
+──────────────────────────────────────────────────┬───────────+
│                                                  │  SETUP    │  ← Panel title, FONT_BODY
│  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐  ← Blue's rows 0-3       │  Player 1  │  ← Current player label, COLOUR_TEAM_RED
│  │▪│▪│▪│▪│▪│▪│▪│▪│▪│▪│  (greyed out / locked)    │  Red Army  │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │           │
│  │▪│▪│▪│▪│▪│▪│▪│▪│▪│▪│                           │  Pieces   │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │  left: 40 │
│  │▪│▪│▪│▪│▪│▪│▪│▪│▪│▪│                           │           │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │  ┌──────┐ │
│  │▒│▒│██│██│▒│▒│██│██│▒│  ← Lakes (rows 4-5)      │  │ Ma 1 │ │  ← Piece tray
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │  │ Ge 1 │ │
│  │▒│▒│██│██│▒│▒│██│██│▒│                           │  │ Co 2 │ │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │  │ Mj 3 │ │
│  │░│░│░│░│░│░│░│░│░│░│  ← Setup zone rows 6-9    │  │ Ca 4 │ │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤  (highlighted)            │  │ Li 4 │ │
│  │░│░│░│░│░│░│░│░│░│░│                           │  │ …    │ │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │  └──────┘ │
│  │░│░│░│░│░│░│░│░│░│░│                           │           │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                           │ [Auto [A]]│
│  │░│░│░│░│░│░│░│░│░│░│                           │ [Clear[C]]│
│  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘                           │ [Abandon] │  ← NOW VISIBLE
│  ↑ Setup zone highlighted with a soft gold border │ [Ready[R]]│  ← disabled until all placed
│                                                  │           │
+──────────────────────────────────────────────────┴───────────+

Legend:
  ▪ = opponent rows (greyed out, click disabled)
  ▒ = neutral rows (rows 4-5, not setup zone)
  ██ = lake squares (blue fill)
  ░ = setup zone (soft highlight, gold border around zone)
```

---

## Player Handover Overlay (2-Player Mode)

When Player 1 clicks "Ready", **before** transitioning to Player 2's setup,
display a full-screen handover overlay:

```
+────────────────────────────────────────────────────────────────+
│                                                                │
│                                                                │
│  ╔══════════════════════════════════════════════════════════╗  │
│  ║                                                          ║  │
│  ║    Player 1 has finished army setup.                     ║  │  ← FONT_HEADING
│  ║                                                          ║  │
│  ║    Please pass the device to Player 2.                   ║  │  ← FONT_BODY
│  ║                                                          ║  │
│  ║    Player 2: press any key or click to continue.         ║  │  ← FONT_SMALL, animated hint
│  ║                                                          ║  │
│  ╚══════════════════════════════════════════════════════════╝  │
│                                                                │
│                                                                │
+────────────────────────────────────────────────────────────────+
Scrim: black at 90% opacity (board not visible through the scrim)
Card: COLOUR_SURFACE (#283A58), border_radius=12
```

This overlay must be **fully opaque** (no board visible behind it) to prevent
Player 1's arrangement from being seen.

---

## Piece Tray (Side Panel)

The piece tray shows remaining pieces to be placed, grouped by rank:

```
┌────────────────────┐
│  Remaining Pieces  │  ← FONT_SMALL header
│                    │
│  Marshal     (1)   │  ← count badge
│  General     (1)   │
│  Colonel     (2)   │
│  Major       (3)   │
│  Captain     (4)   │
│  Lieutenant  (4)   │
│  Sergeant    (4)   │
│  Miner       (5)   │
│  Scout       (8)   │
│  Spy         (1)   │
│  Bomb        (6)   │
│  Flag        (1)   │
└────────────────────┘
```

- Next piece to be placed (top of queue) is highlighted with `COLOUR_SELECT`.
- Click a row in the tray to select that piece type as the "next to place".
- Count badge turns `COLOUR_INVALID` when count reaches 0.

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Board grid | Interactive grid | cell-hover, setup-zone-highlight | 10×10 cells |
| Setup zone highlight | Decoration | always visible | Soft gold border around rows 6–9 (Red) or 0–3 (Blue) |
| Opponent rows | Decoration | greyed, click-disabled | Rows outside setup zone |
| Lake cells | Decoration | non-interactive | Blue fill, no hover |
| Side panel title | Text | static | `"Setup"` |
| Player label | Text | static | `"Player 1 — Red Army"` / `"Player 2 — Blue Army"` |
| Pieces left counter | Text | updates on placement | `"Pieces left: 40"` |
| Piece tray | Scrollable list | row-selected, row-depleted | Rank name + count |
| Auto-arrange button | Button (Secondary) | default, hover | `"Auto [A]"` |
| Clear button | Button (Secondary) | default, hover | `"Clear [C]"` |
| Abandon button | Button (Danger) | default, hover | `"Abandon [Q]"` |
| Ready button | Button (Primary) | default (disabled), enabled, hover | `"Ready [R]"` |
| Handover overlay | Overlay | shown when Player 1 ready | Full-screen scrim + card |

---

## Interaction Model

### Click-to-Place (Current Implementation)

1. Click a tray row to select a piece type.
2. Click a valid cell in the setup zone to place it.
3. If the cell is invalid (outside zone, lake, occupied), flash the cell
   `COLOUR_INVALID` and show `"Place pieces in your setup zone"` label.

### Drag-and-Drop (Target Implementation)

1. Press and hold on a tray row → piece "lifts" (scale 1.1×, drop shadow).
2. Drag onto the board → piece follows the cursor.
3. Release on a valid cell → piece placed with a subtle drop animation.
4. Release on an invalid cell → piece returns to tray with a shake animation.
5. Press and hold on an already-placed board piece → pick it back up for
   repositioning.

> **Note:** Drag-and-drop is a Should Have for v1.0; click-to-place is
> the Must Have minimum.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `A` | Auto-arrange remaining pieces |
| `C` | Clear all placed pieces |
| `R` | Confirm ready (only when all pieces placed) |
| `Q` | Abandon setup and return to previous screen |
| `Tab` | Cycle tray selection to next piece type |
| `↑` / `↓` | Navigate tray rows |
| `Enter` | Place selected tray piece on the currently focused board cell |
| `Arrow keys` | Move board focus cell within the setup zone |

---

## Annotations

1. **Abandon button is currently missing from the render.** The current
   implementation (`setup_screen.py:200`) renders only Auto, Clear, and Ready.
   The `Q` keyboard shortcut works but the visual button is absent — add it
   between Clear and Ready in the panel.

2. **Setup zone visual guide:** Highlight rows 6–9 (or 0–3 for Blue) with a
   subtle gold `#DCB450` border at the zone boundary to make placement areas
   unmistakable for first-time players.

3. **"Pieces left" breakdown:** Replace the plain `"Pieces left: 40"` counter
   with the rank-grouped tray so players know which specific pieces remain.

4. **Board cell click outside zone:** Currently silently fails. Add a 0.5 s
   `COLOUR_INVALID` flash on the clicked cell.

5. **Player label:** In 2-player mode, the side panel currently shows no
   player identity. Add `"Player 1 — Red Army"` / `"Player 2 — Blue Army"`
   as a subtitle in the panel to reduce confusion after handover.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player 1's arrangement visible during handover | High | Critical | Full-screen opaque handover overlay (described above) |
| Player places pieces outside setup zone by mistake | High (novices) | Medium | Zone highlight + invalid cell flash + error label |
| 40-piece placement is tedious | High | Medium | Auto-arrange button; drag-and-drop in future sprint |
| Ready button confused with Clear button (proximity) | Low | Low | Colour-code: Ready=Primary blue, Clear=Secondary, Abandon=Danger red |

---

## Open Questions

- [ ] Should the handover overlay be triggered by a button press or any key/click?
- [ ] Is drag-and-drop required at v1.0 or only click-to-place?
- [ ] Should players be able to rearrange already-placed pieces before clicking Ready?

# Wireframe: Playing Screen

**Version:** v1.0 Draft  
**Screen class:** `PlayingScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.7`](../specifications/screen_flow.md)

---

## Layout (1280 × 720 reference, 80% board / 20% panel split)

```
+──────────────────────────────────────────────┬──────────────+
│                                              │ RED ARMY     │  ← player label, COLOUR_TEAM_RED
│  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐                      │ ● Your turn  │  ← active player indicator
│  │?│?│?│?│?│?│?│?│?│?│  ← hidden Blue pieces │ Turn 42      │  ← turn counter
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │              │
│  │?│?│?│?│?│?│?│?│?│?│                      │──────────────│
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │ Last move:   │  ← last move summary
│  │?│?│?│?│?│?│?│?│?│?│                      │ RED E4→E5   │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │              │
│  │?│?│██│██│?│?│██│██│?│?│  ← lakes            │──────────────│
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │ Captured     │  ← captured pieces section
│  │?│?│██│██│?│?│██│██│?│?│                      │ ♦ Ma Ge Co  │  ← Red captured from Blue
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │ ♠ Ca Li Se  │  ← Blue captured from Red
│  │R│R│R│R│R│R│R│R│R│R│  ← friendly Red pieces │              │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │──────────────│
│  │R│R│R│R│R│R│R│R│R│R│  (rank labels visible) │ [💾 Save ]   │  ← Save Game button
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │ [↩ Undo ]   │  ← if undo_enabled
│  │R│R│R│R│R│R│R│R│R│R│                      │              │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤                      │ [Quit ✕ ]   │  ← Quit to Menu
│  │R│R│R│R│R│R│R│R│R│R│                      │              │
│  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘                      │              │
│                                              │              │
+──────────────────────────────────────────────┴──────────────+

Selected piece + valid moves shown:
│  │R│  ← selected (COLOUR_SELECT pulsing border)
│  │●│  ← valid move destination (COLOUR_MOVE_VALID dot)
│  │✕│  ← invalid destination (shown only on attempted move, 0.5s flash)
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Board grid | Interactive | cell-hover, piece-selected, valid-move, last-move, invalid-flash | 10×10 cells |
| Hidden enemy pieces | Non-interactive display | default, revealed | `"?"` / rank abbreviation |
| Friendly pieces | Interactive | default, hover, selected | Rank abbreviation |
| Lake cells | Non-interactive | static | Blue fill |
| **Side Panel** | | | |
| Player label + indicator | Text | active player highlighted | `"RED ARMY"` / `"BLUE ARMY"` |
| Turn counter | Text | updates | `"Turn 42"` |
| Status message | Text | updates | e.g. `"Your move"`, `"AI thinking…"` |
| Last move summary | Text | updates after each move | `"RED E4→E5"` |
| Captured pieces tray | Text list | updates after combat | Rank abbreviations grouped by side |
| Save Game button | Button (Secondary) | default, hover | `"💾 Save"` |
| Undo button | Button (Secondary) | default, hover, disabled | `"↩ Undo"` (visible only if undo enabled) |
| Quit to Menu button | Button (Danger) | default, hover | `"Quit ✕"` |

---

## Interaction States

### Board Cell — Piece Selection

**Step 1 — Select friendly piece:**
- Click on a friendly (Red) piece
- Selected cell: pulsing 2 px `#F1C40F` border (800 ms loop, alpha 1.0 → 0.6)
- All legal destination cells: `#27AE60` semi-transparent fill (alpha=80) with a
  centred dot (●, 12 px radius)
- All lake cells and non-empty cells: no change (clicking them will be invalid)

**Step 2 — Move or Deselect:**
- Click a highlighted (valid) cell → `MovePiece` command submitted
- Click the same cell → deselect
- Right-click anywhere → deselect
- Click an invalid cell → 0.5 s `#E74C3C` flash + error message in status area

### Post-Move Feedback

After any move (player or AI):
1. Origin cell: `#E67E22` fill at 40 % alpha, persists for 1.5 s then fades
2. Destination cell: `#F39C12` fill at 40 % alpha, persists for 1.5 s then fades
3. Side panel "Last move" summary updates immediately

### Combat Resolution

After `CombatResolved` event fires:
1. Both involved cells play a 600 ms "flash" animation alternating between
   their piece colour and `#F1C40F`
2. If a piece is removed, it disappears with a 200 ms scale-to-zero animation
3. Status message updates: e.g. `"Red Marshal defeats Blue Scout!"`
4. Captured piece appears in the captured pieces tray with a fade-in

### AI Thinking Indicator

When it is the AI's turn:
- Status message: `"AI is thinking…"` with an animated ellipsis (dots appear
  sequentially: `.` → `..` → `...` → ` ` on a 600 ms step cycle)
- The board should be non-interactive (piece clicks disabled) during this time
- A subtle overlay can be added: cursor changes to `WAIT` cursor

### Invalid Move

On `InvalidMove` event:
- Flash the `_selected_pos` cell `#E74C3C` for 0.5 s
- Show human-readable message in the status area (see error message map in
  [ux-heuristics-evaluation.md §H9](./ux-heuristics-evaluation.md))
- Do not deselect the piece — player can immediately try another destination

---

## Error Message Map

| Domain reason code | Displayed message |
|---|---|
| `piece_blocked` | `"That path is blocked"` |
| `wrong_turn` | `"It is not your turn"` |
| `immovable_piece` | `"Bombs and Flags cannot move"` |
| `two_square_rule` | `"Cannot move back and forth (two-square rule)"` |
| `lake_square` | `"Pieces cannot enter lakes"` |
| `friendly_occupied` | `"A friendly piece is already there"` |
| (default) | `"Invalid move"` |

---

## Side Panel — Board Fraction Adjustment

**Current implementation:** `_BOARD_FRACTION = 0.75` → panel is 25 % of window  
**Recommended:** `_BOARD_FRACTION = 0.80` → panel is 20 % of window

At 1280 px width:
- Current: board = 960 px, panel = 320 px (very wide for the content shown)
- Recommended: board = 1024 px, panel = 256 px (still sufficient for all panel elements)

The extra 64 px added to the board improves the piece size and board readability.

---

## Panel Layout (detailed)

```
SIDE PANEL (256 px wide)
│ ┌──────────────────────────┐
│ │  ♦ RED ARMY              │  ← FONT_BODY, COLOUR_TEAM_RED
│ │  ● Your turn             │  ← 10px dot in team colour
│ │  Turn 42                 │  ← FONT_SMALL, COLOUR_TEXT_SECONDARY
│ ├──────────────────────────┤  ← 1px COLOUR_PANEL_BORDER
│ │  "Sergeant moves D7→D6"  │  ← status message, FONT_SMALL
│ ├──────────────────────────┤
│ │  Captured by RED:        │  ← FONT_SMALL header
│ │  Ma Ge Co Li Se Sc       │  ← rank abbrevs, wrap as needed
│ │  Captured by BLUE:       │
│ │  Ca Se Sc Sc             │
│ ├──────────────────────────┤
│ │  [ 💾 Save     ]         │
│ │  [ ↩ Undo      ]         │  ← hidden if undo disabled
│ ├──────────────────────────┤
│ │  [ Quit ✕      ]         │  ← Danger, bottom of panel
│ └──────────────────────────┘
```

---

## Quit to Menu Confirmation

Clicking "Quit ✕" shows a confirmation dialog:

```
+─────────────────────────────────────────────+
│  Quit to Menu?                              │
│                                             │
│  Your current game will be auto-saved.      │
│  You can resume it from the Main Menu.      │
│                                             │
│  [ Stay in Game ]       [ Quit & Save ]     │
+─────────────────────────────────────────────+
```

After confirmation, auto-save is triggered (write to `JsonRepository`) and
then `screen_manager.replace(MainMenuScreen(...))` is called to clear the stack.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Arrow keys` | Move board focus cell |
| `Enter` / `Space` | Select / move focused cell |
| `Escape` | Deselect current piece |
| `S` | Save game |
| `U` | Undo last move (if enabled) |
| `F` | Flip board perspective |
| `Q` | Quit to menu (with confirmation) |
| `?` / `F1` | Show keyboard shortcut overlay |

---

## Annotations

1. **Board fraction change:** Adjust `_BOARD_FRACTION` from 0.75 to 0.80 to
   give the board more space. Update both `playing_screen.py` and
   `setup_screen.py` constants simultaneously.

2. **Save Game button is missing:** The spec lists "Save Game" in the controls
   bar; `_render_panel()` does not render it. Add between the status area and
   the Quit button.

3. **Quit clears the screen stack incorrectly:** The current `_on_quit_to_menu()`
   calls `pop()` once, leaving `SetupScreen` on the stack. Replace with:
   ```python
   while len(self._screen_manager.stack) > 1:
       self._screen_manager.pop()
   ```

4. **Rank abbreviation rendering:** Draw the rank abbreviation centred in each
   friendly piece cell. Use a dark text stroke if the piece background is light:
   - `Ma` = Marshal, `Ge` = General, `Co` = Colonel, `Mj` = Major
   - `Ca` = Captain, `Li` = Lieutenant, `Se` = Sergeant, `Mi` = Miner
   - `Sc` = Scout, `Sp` = Spy, `Bm` = Bomb, `Fl` = Flag

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player does not know which moves are legal | High | High | Valid-move highlighting (Must Have) |
| AI appears frozen during thinking | Medium | High | AI thinking indicator |
| Quit without confirmation loses progress | Medium | Medium | Quit confirmation dialog with auto-save |
| Board too small at recommended 80% fraction | Low | Low | Test at 1280×720; cells should be at least 72×72 px |

---

## Open Questions

- [ ] Should the Undo button be visible but disabled (greyed) when undo is off in settings, or hidden entirely?
- [ ] How many moves should the "last move summary" in the panel retain? (1 move vs last 5)
- [ ] Should the captured pieces tray show piece icons (sprites) or text abbreviations?

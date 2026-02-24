# Wireframe: Game Over Screen

**Version:** v1.0 Draft  
**Screen class:** `GameOverScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.8`](../specifications/screen_flow.md)

---

## Layout — Red Wins (1280 × 720 reference)

```
+----------------------------------------------------------------+
│                                                                │
│                                                                │
│             ★  RED ARMY WINS!  ★                              │  ← FONT_DISPLAY (56px), COLOUR_TEAM_RED
│                                                                │
│               Flag captured!                                   │  ← FONT_SUBHEADING (32px), COLOUR_TEXT_PRIMARY
│                                                                │
│                  42 turns played                               │  ← FONT_BODY (24px), COLOUR_TEXT_SECONDARY
│                                                                │
│  ─────────────────────────────────────────────────────────    │  ← divider
│                                                                │
│       [ Main Menu  ]    [ Play Again  ]    [ Quit ✕  ]        │  ← button row
│                                                                │
│                                                                │
│  ─────────────────────────────────────────────────────────    │
│                                                                │
│  Match Summary            │   Combat: 12 engagements          │  ← optional stats
│  Red pieces remaining: 28 │   Draws: 2                        │
│  Blue pieces remaining: 4 │                                   │
│                                                                │
+----------------------------------------------------------------+
```

---

## Layout — Draw

```
+----------------------------------------------------------------+
│                                                                │
│             ═══  DRAW  ═══                                     │  ← COLOUR_WIN_DRAW (#A0A0A0)
│                                                                │
│            Maximum turns reached                              │
│                                                                │
│                 3000 turns played                              │
│                                                                │
│       [ Main Menu  ]    [ Play Again  ]    [ Quit ✕  ]        │
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Winner headline | Text | win (Red), win (Blue), draw | See headline format |
| Stars / trophy decoration | Decoration | shown on win, not draw | `"★  … ★"` flanking the headline |
| Winning condition | Text | static | Human-readable condition string |
| Turn count | Text | static | `"42 turns played"` |
| Divider | Decoration | static | 1 px horizontal rule |
| Main Menu button | Button (Secondary) | default, hover, active | `"Main Menu"` |
| Play Again button | Button (Primary) | default, hover, active | `"Play Again"` |
| Quit button | Button (Danger) | default, hover, active | `"Quit ✕"` |
| Match summary panel | Text block | optional, shown if space | Piece counts, combat statistics |

---

## Interaction States

### Winner Headline

| Condition | Text | Colour |
|---|---|---|
| Red wins | `"★  RED ARMY WINS!  ★"` | `COLOUR_TEAM_RED` (`#C83C3C`) |
| Blue wins | `"★  BLUE ARMY WINS!  ★"` | `COLOUR_TEAM_BLUE` (`#3C6ED2`) |
| Draw | `"═══  DRAW  ═══"` | `#A0A0A0` |

### Winning Condition String Map

The `reason` string from the `GameOver` event must be mapped to a
human-readable sentence:

| Raw `reason` value | Displayed text |
|---|---|
| `"flag_captured"` | `"Flag captured!"` |
| `"no_legal_moves"` | `"Opponent has no legal moves!"` |
| `"max_turns_reached"` | `"Maximum turns reached"` |
| (any other) | Display as-is |

**Current bug:** The `reason` string is rendered directly without mapping —
raw domain strings like `"flag_captured"` appear on-screen.

### Play Again Button — Navigation Bug Fix

**Current (broken) implementation:**
```python
def _on_play_again(self) -> None:
    try:
        self._screen_manager.pop()  # returns to PlayingScreen — wrong!
    except IndexError:
        pass
```

**Required implementation:**
```python
def _on_play_again(self) -> None:
    """Navigate directly to StartGameScreen, clearing the game stack."""
    from src.presentation.screens.start_game_screen import StartGameScreen
    from src.presentation.screens.main_menu_screen import MainMenuScreen

    # Pop all screens to clear the stack, then push StartGameScreen
    # via MainMenu's standard navigation.
    # Or: use replace() directly if ScreenManager supports it:
    start_screen = StartGameScreen(
        screen_manager=self._screen_manager,
        game_context=self._game_context,
    )
    # Replace the entire stack
    while len(self._screen_manager.stack) > 0:
        try:
            self._screen_manager.pop()
        except IndexError:
            break
    self._screen_manager.push(start_screen)
```

> **Note:** `GameOverScreen` needs a reference to `game_context` to
> construct `StartGameScreen`. Add `game_context` as a constructor parameter.

### Main Menu Button — Stack Clearing

**Current implementation:** calls `pop()` 10 times with a safety limit.
**Required:** A single `screen_manager.replace(MainMenuScreen(...))` call:

```python
def _on_main_menu(self) -> None:
    from src.presentation.screens.main_menu_screen import MainMenuScreen
    main_menu = MainMenuScreen(
        screen_manager=self._screen_manager,
        game_context=self._game_context,
    )
    self._screen_manager.replace(main_menu)
```

---

## Button Order Rationale

The button order recommended is: **Main Menu** (left) → **Play Again** (centre)
→ **Quit** (right).

This follows the principle of ordering actions from least to most commitment:
- "Main Menu" is neutral — returns to a known-good state
- "Play Again" is positive but requires re-investment
- "Quit" is the most terminal action — placed rightmost

**Current implementation** has "Play Again" first, "Main Menu" second, "Quit"
third — this is a minor convention deviation. Reorder as recommended.

---

## Headline Animation

On screen entry (`on_enter()`):
1. Background fades in from black over 300 ms
2. Winner headline scales from 0.7× → 1.0× over 400 ms (ease-out)
3. Sub-text fades in over 200 ms, 200 ms after the headline

This animation sequence makes the win/loss moment feel like a celebration
or defeat rather than an abrupt state change. Skip if `reduce_motion` is enabled.

---

## Match Summary Panel (Should Have)

Below the button row, show a brief match summary using data from `final_state`:

| Stat | Source |
|---|---|
| Pieces remaining (each side) | `len(state.players[n].pieces_remaining)` |
| Total turns | `state.turn_number` |
| Combat engagements | Count of `CombatResolved` events in the game log |

This panel is optional for v1.0 (marked "Should Have"). If `final_state` is
`None`, hide the panel entirely.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Enter` | Play Again (primary action) |
| `Escape` | Main Menu |
| `Tab` / `Shift+Tab` | Cycle: Main Menu → Play Again → Quit |
| `Space` | Activate focused button |

---

## Annotations

1. **`game_context` required for Play Again fix.** The constructor signature
   must be updated to accept `game_context` alongside `screen_manager`:
   ```python
   def __init__(self, screen_manager, game_context, winner, reason, turn_count):
   ```
   Update the `PlayingScreen._on_game_over()` call site accordingly.

2. **Winning condition mapping:** Add a module-level dict in
   `game_over_screen.py`:
   ```python
   _REASON_LABELS: dict[str, str] = {
       "flag_captured": "Flag captured!",
       "no_legal_moves": "Opponent has no legal moves!",
       "max_turns_reached": "Maximum turns reached",
   }
   ```
   Then use `_REASON_LABELS.get(self._reason, self._reason)` in `render()`.

3. **Team name consistency:** Use `"RED ARMY"` / `"BLUE ARMY"` rather than
   the raw `PlayerSide.value` throughout the codebase.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| "Play Again" navigation bug sends player back to a finished game | High | High | Fix `_on_play_again()` as described |
| Raw reason string confuses players | High | Medium | Add `_REASON_LABELS` mapping |
| Button tap order mismatch with platform conventions | Low | Low | Reorder to Main Menu / Play Again / Quit |
| Empty screen — no match summary | Medium | Low | Add match summary panel (Should Have) |

---

## Open Questions

- [ ] Should "Play Again" start a game with the same settings (mode, difficulty, armies) or go to `StartGameScreen` for fresh configuration?
- [ ] Should the screen display a replay option ("Watch Replay") in a future sprint?
- [ ] Should match statistics be persisted to a local statistics file?

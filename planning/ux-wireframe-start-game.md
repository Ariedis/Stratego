# Wireframe: Start Game Screen

**Version:** v1.0 Draft  
**Screen class:** `StartGameScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.2`](../specifications/screen_flow.md)

---

## Layout (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                        New Game                                |  ← FONT_HEADING (44px), COLOUR_TITLE_GOLD
+----------------------------------------------------------------+
|                                                                |
|  Game Mode                                                     |  ← FONT_SUBHEADING (32px), COLOUR_SUBTITLE
|  ┌──────────────────────┐  ┌──────────────────────┐           |
|  │  Local 2-Player      │  │  ✓  vs Computer      │           |  ← Toggle group; selected shown in green
|  └──────────────────────┘  └──────────────────────┘           |
|                                                                |
|  ═══════════════════════════════════════════════════════════   |  ← animated divider slides in
|                                                                |
|  AI Difficulty             [only shown when vs Computer]       |  ← FONT_SUBHEADING, COLOUR_SUBTITLE
|  ┌────────────┐  ┌────────────┐  ┌────────────┐              |
|  │    Easy    │  │  ✓ Medium  │  │    Hard    │              |  ← Toggle group
|  └────────────┘  └────────────┘  └────────────┘              |
|    ↑ tooltip area (appears on hover, 400ms delay)              |
|                                                                |
|                                                                |
|    [ ← Back          ]              [ Confirm →       ]        |  ← Back=Secondary, Confirm=Primary
|                                                                |
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Screen title | Text | static | `"New Game"` |
| "Game Mode" label | Text | static | `"Game Mode"` |
| Local 2-Player toggle | Button (Toggle) | selected, unselected, hover, focused | `"Local 2-Player"` |
| vs Computer toggle | Button (Toggle) | selected, unselected, hover, focused | `"vs Computer"` |
| Animated divider | Decoration | visible (when vs Computer selected) | — |
| "AI Difficulty" label | Text | visible/hidden | `"AI Difficulty"` |
| Easy button | Button (Toggle) | selected, unselected, hover, focused | `"Easy"` |
| Medium button | Button (Toggle) | selected, unselected, hover, focused | `"Medium"` |
| Hard button | Button (Toggle) | selected, unselected, hover, focused | `"Hard"` |
| Easy tooltip | Tooltip | shown on 400ms hover | `"Makes random moves occasionally"` |
| Medium tooltip | Tooltip | shown on 400ms hover | `"Balanced challenge for most players"` |
| Hard tooltip | Tooltip | shown on 400ms hover | `"Near-optimal play — very challenging"` |
| Back button | Button (Secondary) | default, hover, active, focused | `"← Back"` |
| Confirm button | Button (Primary) | default, hover, active, focused | `"Confirm →"` |

---

## Interaction States

### Game Mode Toggle Group

The two mode buttons behave as a radio group — selecting one deselects the other:

- **Unselected:** background `#324664`, text `#E6E6E6`
- **Selected:** background `#2D8246`, text `#E6E6E6`, with `"✓"` prefix
- **Hover (unselected):** background `#486490`, 150 ms transition

### AI Difficulty Row — Visibility Animation

When the player selects `"vs Computer"`:
1. A horizontal divider slides down from the mode toggle (200 ms, ease-out)
2. The `"AI Difficulty"` label fades in (150 ms, ease-in)
3. The three difficulty buttons slide up from below into position (200 ms, ease-out, staggered by 40 ms each)

When the player selects `"Local 2-Player"`:
1. Difficulty row fades out (150 ms) and collapses (150 ms)

**Current state:** The difficulty row simply appears/disappears with no
animation — implement by interpolating `_diff_row_alpha` and `_diff_row_y`
state variables in `update()`.

### Confirm Button

Confirm always navigates to `ArmySelectScreen` (not directly to `SetupScreen`):

```python
def _on_confirm(self) -> None:
    from src.presentation.screens.army_select_screen import ArmySelectScreen
    army_screen = ArmySelectScreen(
        screen_manager=self._screen_manager,
        game_context=self._game_context,
        game_mode=self._game_mode,
        ai_difficulty=self._ai_difficulty if self._game_mode == GAME_MODE_VS_AI else None,
    )
    self._screen_manager.push(army_screen)
```

> **Bug fix required:** Current implementation calls
> `self._game_context.start_new_game(...)` which skips `ArmySelectScreen`
> entirely. This must be corrected before Sprint 4 sign-off.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | Cycle: Local 2-Player → vs Computer → (Easy → Medium → Hard) → Back → Confirm |
| `Arrow Left/Right` | Switch between mode toggle options |
| `Arrow Left/Right` | Switch between difficulty options (when row is visible) |
| `Enter` / `Space` | Activate focused button |
| `Escape` | Back (same as clicking Back button) |

---

## Annotations

1. **Label rename:** `"2 Players"` → `"Local 2-Player"` and `"vs AI"` →
   `"vs Computer"` to match user expectations (see
   [ux-competitive-analysis.md](./ux-competitive-analysis.md)).

2. **Button positioning:** The Back button should be on the left and Confirm on
   the right, matching the standard navigation convention (Back = left,
   Proceed = right). The current implementation has them correctly positioned.

3. **Section labels:** The current render has no `"Game Mode:"` section label —
   the toggle buttons appear without context. Add the section labels.

4. **Default selection:** The initial selection should be `"vs Computer"` with
   `"Medium"` pre-selected, as these are the most common first-time choices.
   Currently defaults to `"TWO_PLAYER"` — change to `GAME_MODE_VS_AI` with
   `PlayerType.AI_MEDIUM`.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player selects Hard AI without reading the tooltip | Medium | Medium | Tooltips after 400 ms hover; keep Easy as default for first-time sessions |
| Player skips Army Select by hitting Confirm quickly | Low | Low | `ArmySelectScreen` is a mandatory step; no skip path exists in corrected implementation |
| Difficulty row animation causes layout jitter | Medium | Low | Pre-calculate target positions in `on_enter()`; interpolate in `update()` |

---

## Open Questions

- [ ] Should the default game mode be `"Local 2-Player"` or `"vs Computer"`? (Product decision)
- [ ] Should `"vs Computer"` difficulty persist between sessions (written to `config.yaml`)?

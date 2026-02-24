# Wireframe: Army Select Screen

**Version:** v1.0 Draft  
**Screen class:** `ArmySelectScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.3`](../specifications/screen_flow.md)

> **Status:** This screen is **not yet implemented** in
> `src/presentation/screens/`. This wireframe defines the v1.0 implementation
> target.

---

## Layout — vs Computer Mode (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                      Choose Your Army                          |  ← FONT_HEADING (44px)
+----------------------------------------------------------------+
|                                                                |
|  Player 1 — Red Army                                           |  ← FONT_SUBHEADING, COLOUR_TEAM_RED
|  ┌─────────────────────────────────────────┐                  |
|  │  ▼  Classic Army                        │                  |  ← Dropdown
|  └─────────────────────────────────────────┘                  |
|                                                                |
|  ┌──────────────────────────────────────────────────────────┐  |
|  │  PREVIEW                                                  |  |  ← Preview panel
|  │  ┌──────┐  Classic Army                                   |  |
|  │  │  🏴  │  The original Stratego set.                     |  |
|  │  │      │  40 pieces · Standard ranks                     |  |
|  │  └──────┘                                                  |  |
|  │  Marshal(1) General(1) Colonel(2) Major(3) Captain(4)      |  |
|  │  Lieutenant(4) Sergeant(4) Miner(5) Scout(8) Spy(1)       |  |
|  │  Bomb(6) Flag(1)                                           |  |
|  └──────────────────────────────────────────────────────────┘  |
|                                                                |
|    [ ← Back          ]              [ Confirm →       ]        |
|                                                                |
+----------------------------------------------------------------+
```

---

## Layout — Local 2-Player Mode (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                      Choose Your Armies                        |
+----------------------------------------------------------------+
|                                                                |
|  ┌─────────────────────────┐  ┌─────────────────────────┐     |
|  │ Player 1 — Red Army     │  │ Player 2 — Blue Army    │     |
|  │ ▼  Classic Army         │  │ ▼  Classic Army         │     |
|  └─────────────────────────┘  └─────────────────────────┘     |
|                                                                |
|  ┌──────────────────────────────────────────────────────────┐  |
|  │  PREVIEW (shows the army for the most recently changed   |  |
|  │  dropdown)                                               |  |
|  │  [Same layout as vs-Computer mode]                       |  |
|  └──────────────────────────────────────────────────────────┘  |
|                                                                |
|    [ ← Back          ]              [ Confirm →       ]        |
|                                                                |
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Screen title | Text | static | `"Choose Your Army"` (vs Computer) or `"Choose Your Armies"` (2-player) |
| Player 1 label | Text | static | `"Player 1 — Red Army"` in `COLOUR_TEAM_RED` |
| Player 1 dropdown | Dropdown | default, open, focused | Army names from loaded `ArmyMod` list + `"Classic Army"` |
| Player 2 label | Text | visible in 2-player only | `"Player 2 — Blue Army"` in `COLOUR_TEAM_BLUE` |
| Player 2 dropdown | Dropdown | visible in 2-player only | Same list as Player 1 |
| Preview panel | Panel | updates on dropdown change | Army name, description, piece image, piece counts |
| Back button | Button (Secondary) | default, hover, active, focused | `"← Back"` |
| Confirm button | Button (Primary) | default, hover, active, focused | `"Confirm →"` |

---

## Interaction States

### Army Dropdown

```
Default (closed):
  Background: COLOUR_SURFACE (#283A58)
  Border: 1px COLOUR_PANEL_BORDER (#32415F)
  Text: COLOUR_TEXT_PRIMARY (#E6E6E6)
  Arrow: "▼" right-aligned

Open (dropdown list visible):
  List appears below the dropdown, max 5 items visible, scrollable
  Each item: 40px height, FONT_BODY (24px)
  Selected item: COLOUR_BTN_SELECTED (#2D8246) background
  Hovered item: COLOUR_BTN_HOVER (#486490) background

Focused:
  3px COLOUR_FOCUS_RING (#F39C12) outline
```

### Preview Panel

The preview panel updates immediately (no delay) when the user changes the
dropdown selection:

- **Army name:** `FONT_SUBHEADING` (32 px), `COLOUR_TITLE_GOLD`
- **Description:** `FONT_SMALL` (18 px), `COLOUR_TEXT_SECONDARY`, 2 lines max
- **Piece image:** 80 × 80 px sample piece sprite (the Marshal tile for the
  selected army)
- **Piece count grid:** A grid of `(Rank abbreviation): (count)` pairs in
  `FONT_SMALL`

When no custom armies are loaded (only `"Classic Army"` in the list), show a
hint below the dropdown:
`"Add custom armies by placing .json files in your army mod folder."`

---

## Data Requirements

Data received from `StartGameScreen` via `on_enter(data)`:

```python
data = {
    "game_mode": "TWO_PLAYER" | "VS_AI",
    "ai_difficulty": PlayerType | None,
}
```

Data passed to `SetupScreen` via `on_exit()`:

```python
return {
    "game_mode": self._game_mode,
    "ai_difficulty": self._ai_difficulty,
    "player1_army": self._player1_army,   # ArmyMod
    "player2_army": self._player2_army,   # ArmyMod (may equal player1_army)
}
```

---

## Dropdown Implementation Note

pygame-ce does not provide a native dropdown widget. Implement as follows:

1. Render the dropdown as a button that toggles an overlay list.
2. The overlay list is rendered in a separate pass at the top of the Z-order
   (after all other panel elements) so it overlaps adjacent content.
3. Clicking outside the open list closes it.
4. Arrow keys navigate the list when it is open.

---

## Annotations

1. **In vs-Computer mode** only Player 1 selects an army. Player 2 (AI) uses
   a default or randomly selected loaded army — this is an internal choice
   not shown to the player. Do not show a Player 2 dropdown in this mode.

2. **"Classic Army" must always be in the list**, even when no custom army
   mods are installed, as the fallback.

3. **Preview panel focus:** In 2-player mode the preview panel shows the army
   for whichever dropdown was changed most recently. Label the panel with
   the player name to avoid confusion: `"Player 1 Preview"` vs
   `"Player 2 Preview"`.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| No army mods installed — dropdown has only one option | High (for new installs) | Low | Show the "add custom armies" hint; Confirm still works with Classic Army |
| Preview panel shows nothing during initial load | Low | Low | Pre-populate with Classic Army data on `on_enter()` |
| 2-player both selecting same army — is this valid? | Low | None | Yes, it is valid per spec; no warning needed |

---

## Open Questions

- [ ] Should the AI's army selection be shown to the player (for transparency) or hidden?
- [ ] What is the maximum number of custom army mods supported (affects dropdown scroll height)?
- [ ] Should the preview show a visual of the full piece set layout, or just the count grid?

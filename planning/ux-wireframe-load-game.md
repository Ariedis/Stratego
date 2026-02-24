# Wireframe: Load Game Screen

**Version:** v1.0 Draft  
**Screen class:** `LoadGameScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.4`](../specifications/screen_flow.md)

> **Status:** This screen is **not yet implemented** in
> `src/presentation/screens/`. The "Load Game" button on the Main Menu is
> currently a disabled stub.

---

## Layout — With Save Files (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                        Load Game                               |  ← FONT_HEADING (44px)
+----------------------------------------------------------------+
|                                                                |
|  ┌──────────────────────────────────────────────────────────┐  |
|  │  ● 2026-02-24 18:45 · Turn 42 · vs Computer (Hard)       │  ← selected row
|  ├──────────────────────────────────────────────────────────┤  |
|  │    2026-02-23 11:12 · Turn 18 · Local 2-Player           │  |
|  ├──────────────────────────────────────────────────────────┤  |
|  │    2026-02-20 09:30 · Turn 95 · vs Computer (Medium)     │  |
|  ├──────────────────────────────────────────────────────────┤  |
|  │    2026-02-18 22:00 · Turn 7  · vs Computer (Easy)       │  |
|  └──────────────────────────────────────────────────────────┘  |
|  ▲ scrollable list, newest first                               |
|                                                                |
|  ┌──────────────────────────────────────────────────────────┐  |
|  │  Selected: 2026-02-24 18:45                               |  |  ← detail panel
|  │  Mode: vs Computer (Hard) · Turn 42                      |  |
|  │  Red army: Classic · Blue army: Classic                  |  |
|  └──────────────────────────────────────────────────────────┘  |
|                                                                |
|  [ ← Back   ]   [ 🗑 Delete   ]             [ ▶ Load   ]      |
|                                              ← Load = Primary  |
+----------------------------------------------------------------+
```

---

## Layout — Empty State (No Save Files)

```
+----------------------------------------------------------------+
|                        Load Game                               |
+----------------------------------------------------------------+
|                                                                |
|                                                                |
|                    ┌────────────────┐                          |
|                    │                │                          |
|                    │    🏰          │                          |  ← Illustrated placeholder
|                    │                │                          |
|                    └────────────────┘                          |
|                                                                |
|             No saved games found.                              |  ← FONT_SUBHEADING
|       Start a new game to create your first save.             |  ← FONT_BODY, COLOUR_TEXT_SECONDARY
|                                                                |
|                  [ Start New Game  ]                           |  ← Primary button
|                                                                |
+----------------------------------------------------------------+
|  [ ← Back   ]                                                  |
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Screen title | Text | static | `"Load Game"` |
| Save file list | Scrollable list | default, row-hover, row-selected | See row format |
| Selected file detail | Panel | shown when row selected | Date, mode, turn, armies |
| Back button | Button (Secondary) | default, hover, active, focused | `"← Back"` |
| Delete button | Button (Danger) | default, hover, active, focused, disabled | `"🗑 Delete"` |
| Load button | Button (Primary) | default, hover, active, focused, disabled | `"▶ Load"` |
| Empty-state illustration | Image | shown when list empty | Placeholder castle icon |
| Empty-state text | Text | shown when list empty | `"No saved games found."` |
| Start New Game button | Button (Primary) | shown when list empty | `"Start New Game"` |

---

## Interaction States

### Save File List Row
- **Default:** background `COLOUR_PANEL` (`#1E2D46`), 1 px bottom border `#32415F`
- **Hovered:** background `#283A58`, 150 ms transition
- **Selected:** background `#2D8246` (green tint), left border 4 px `#F39C12`
- **Row format:** `"● [date] · Turn [n] · [mode] ([difficulty if AI])"` — FONT_BODY (24 px)

### Load Button
- **Disabled** (no row selected): background `#283241`, text `#646E7D`
- **Enabled** (row selected): background `#2980B9`, text `#E6E6E6`

### Delete Button — Confirmation Dialog

When "Delete" is clicked, push a modal overlay:

```
+-------------------------------------------+
|  Delete Save File?                         |  ← FONT_SUBHEADING, COLOUR_TITLE_GOLD
|                                           |
|  2026-02-24 18:45 · Turn 42              |  ← FONT_BODY, COLOUR_TEXT_PRIMARY
|  This cannot be undone.                  |  ← FONT_SMALL, COLOUR_TEXT_SECONDARY
|                                           |
|  [ Cancel ]              [ Delete ]      |  ← Cancel=Secondary, Delete=Danger
+-------------------------------------------+
```

After deletion, the list refreshes. If the deleted save was the last one,
transition to the empty state.

### Error State — Corrupted Save File

If loading a save file raises a parse error:

```
+-------------------------------------------+
|  ⚠ Cannot Load Save File                  |
|                                           |
|  This save file appears to be corrupted  |
|  and cannot be loaded.                   |
|                                           |
|  [ Cancel ]              [ Delete ]      |
+-------------------------------------------+
```

---

## Data Requirements

Data passed to `PlayingScreen` via `on_exit()`:

```python
return {
    "game_state": loaded_game_state,  # deserialised GameState snapshot
}
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate list rows |
| `Enter` | Load selected save |
| `Delete` | Delete selected save (shows confirmation) |
| `Escape` | Back to Main Menu |
| `Tab` / `Shift+Tab` | Cycle: list → Back → Delete → Load |

---

## Annotations

1. **Sort order:** Newest-first (descending by last-saved timestamp). The spec
   confirms this at §3.4.

2. **Date format:** Use `"YYYY-MM-DD HH:MM"` (ISO 8601) for clarity and
   sortability. Avoid locale-dependent formats.

3. **Detail panel:** The detail panel below the list reduces the need to
   remember what each row represents — following the
   master-detail pattern used by Board Game Arena's game history.

4. **Load as default action:** Double-clicking a row should also load it
   (equivalent to selecting then pressing Enter).

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player deletes wrong save file | Low | High | Confirmation dialog with file details |
| Corrupt save file crashes the app | Medium | High | Wrap `JsonRepository.load()` in try/except; show error dialog |
| Long save file names overflow the list row | Low | Low | Truncate at 60 chars with ellipsis |

---

## Open Questions

- [ ] How many save slots does the game support? (Unlimited vs capped at N)
- [ ] Should saves be named by the user or auto-named (current spec: auto)?
- [ ] Should "Continue" on the Main Menu be renamed "Quick Resume" to disambiguate from "Load Game"?

# Wireframe: Main Menu Screen

**Version:** v1.0 Draft  
**Screen class:** `MainMenuScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.1`](../specifications/screen_flow.md)

---

## Layout (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                                                                |
|              CONQUEROR'S QUEST                                 |  ← FONT_DISPLAY (56px), COLOUR_TITLE_GOLD
|        A Stratego-inspired strategy game                       |  ← FONT_SMALL (18px), COLOUR_SUBTITLE
|                                                                |
|          ─────────────────────────────                         |  ← 1px COLOUR_PANEL_BORDER divider
|                                                                |
|                  [ Start Game       ]                          |  ← Primary button, 280×52
|                                                                |
|                  [ Continue         ]                          |  ← Enabled/disabled based on save file
|                                                                |
|                  [ Load Game        ]                          |
|                                                                |
|                  [ Settings     ⚙  ]                          |
|                                                                |
|                  [ Quit          ✕  ]                          |  ← COLOUR_BTN_DANGER
|                                                                |
+----------------------------------------------------------------+
|  v1.0.0                                          © 2026       |  ← FONT_SMALL, COLOUR_TEXT_SECONDARY
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Game title | Text | static | `"CONQUEROR'S QUEST"` |
| Subtitle | Text | static | `"A Stratego-inspired strategy game"` |
| Divider | Decoration | static | 1 px horizontal rule |
| Start Game | Button (Primary) | default, hover, active, focused | `"Start Game"` |
| Continue | Button (Primary) | **enabled** or **disabled** | `"Continue"` |
| Load Game | Button (Secondary) | default, hover, active, focused | `"Load Game"` |
| Settings | Button (Secondary) | default, hover, active, focused | `"Settings ⚙"` |
| Quit | Button (Danger) | default, hover, active, focused | `"Quit ✕"` |
| Version text | Text | static | `"v1.0.0"` |

---

## Interaction States

### Continue Button

**Current implementation (broken):** `disabled: True` hardcoded  
**Required implementation:**

```python
def on_enter(self, data):
    ...
    most_recent = self._game_context.repository.get_most_recent_save()
    for btn in self._buttons:
        if btn["label"] == "Continue":
            btn["disabled"] = most_recent is None
            btn["action"] = lambda: self._on_continue(most_recent)
```

- **Enabled state:** background `#2980B9`, text `#E6E6E6`
- **Disabled state:** background `#283241`, text `#646E7D`
- **Disabled tooltip (on hover):** `"No saved game — start a new game first"` (appear after 400 ms)

### Start Game Button
- **Default:** background `#324664`, text `#E6E6E6`
- **Hover:** background `#486490`, 150 ms ease-in-out transition
- **Active (pressed):** background `#243650`, scale 0.97
- **Focused (keyboard):** 3 px `#F39C12` outline at 6 px inflation

### Quit Button
- **Default:** background `#C0392B`, text `#E6E6E6`
- **Hover:** background `rgb(210, 70, 55)`, 150 ms transition
- **Active:** background `rgb(150, 40, 30)`, scale 0.97

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | Cycle button focus: Start Game → Continue → Load Game → Settings → Quit |
| `Enter` / `Space` | Activate focused button |
| `Escape` | No action (no previous screen) |
| `?` / `F1` | Show keyboard shortcut overlay |

---

## Annotations

1. **Title text fix:** The current render displays `"STRATEGO"` — the game is
   named *Conqueror's Quest*; update the title string in `main_menu_screen.py:105`.

2. **Continue button logic:** The `disabled: True` hardcode in `_build_buttons()`
   at line 185 must be replaced with a live check against the save repository.
   The button's action lambda should capture the save object rather than
   `lambda: None`.

3. **Background enrichment:** A full-screen thematic background image or subtle
   animated particle effect (falling strategic symbols) would reinforce brand
   identity. For v1.0, a subtle radial gradient from `#141E30` to `#1C2638`
   centred on the title is an achievable minimum.

4. **Footer:** A one-line footer with version number and copyright signals
   polish and helps with support triage.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player confused by always-greyed Continue button | High | Medium | Show tooltip on hover; fix the save-detection logic |
| "Load Game" click yields no feedback when stub is active | High | Medium | If not yet implemented, show a toast: `"Load Game coming soon"` rather than doing nothing |
| "Settings" click yields no feedback when stub is active | High | Low | Same as above |
| "Quit" triggers accidentally | Low | High | Require a single deliberate click (no double-click confirmation needed — it is a menu screen, not mid-game) |

---

## Open Questions

- [ ] Should the background be a static image, animated GIF, or procedural gradient? (Art direction decision)
- [ ] Should a "How to Play" button be added at v1.0 or deferred to v2.0?
- [ ] What is the exact game subtitle / tagline?

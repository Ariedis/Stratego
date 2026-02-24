# Wireframe: Settings Screen

**Version:** v1.0 Draft  
**Screen class:** `SettingsScreen`  
**Date:** 2026-02-24  
**Specification ref:** [`screen_flow.md §3.5`](../specifications/screen_flow.md)

> **Status:** This screen is **not yet implemented** in
> `src/presentation/screens/`. The "Settings" button on the Main Menu is
> currently a disabled stub.

---

## Layout (1280 × 720 reference)

```
+----------------------------------------------------------------+
|                        Settings                               |  ← FONT_HEADING (44px)
+----------------------------------------------------------------+
|                                                                |
|  ── Display ──────────────────────────────────────────────    |  ← Section header, COLOUR_SUBTITLE
|                                                                |
|  Resolution        [ ▼  1920 × 1080                    ]      |  ← Dropdown
|  Fullscreen        [  ToggleOff  ] ←→ [ ToggleOn  ]           |  ← Toggle
|  FPS Cap           ───●────────────────────  60               |  ← Slider (30–144)
|                                                                |
|  ── Audio ─────────────────────────────────────────────────   |
|                                                                |
|  Sound Effects     [ ToggleOn ] ───────●──────────── 75%      |  ← Toggle + Slider
|  Music             [ ToggleOn ] ──────────●─────────  50%     |  ← Toggle + Slider
|                                                                |
|  ── Game ──────────────────────────────────────────────────   |
|                                                                |
|  Undo               [ ToggleOff ]                             |  ← Toggle
|  Reduce Motion      [ ToggleOff ]                             |  ← Toggle (accessibility)
|  Colour Blind Mode  [ ToggleOff ]                             |  ← Toggle (accessibility)
|                                                                |
|  ── Mods ──────────────────────────────────────────────────   |
|                                                                |
|  Army Mod Folder   [ 📂 /home/user/.stratego/armies   [···] ] |  ← Folder picker
|                                                                |
|  [ Reset to Defaults ]        [ ← Back ]  [ ✓ Apply   ]      |
|                                                                |
+----------------------------------------------------------------+
```

---

## Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Screen title | Text | static | `"Settings"` |
| **Display section** | | | |
| Resolution | Dropdown | default, open, focused | Selected resolution string |
| Fullscreen | Toggle | on, off, focused | `"Fullscreen"` |
| FPS Cap | Slider | dragging, focused | Range 30–144, step 1; displays current value |
| **Audio section** | | | |
| Sound Effects toggle | Toggle | on, off, focused | `"Sound Effects"` |
| Sound Effects volume | Slider | enabled/disabled, dragging, focused | Range 0–100 %; disabled when toggle off |
| Music toggle | Toggle | on, off, focused | `"Music"` |
| Music volume | Slider | enabled/disabled, dragging, focused | Range 0–100 %; disabled when toggle off |
| **Game section** | | | |
| Undo toggle | Toggle | on, off, focused | `"Undo"` |
| Reduce Motion toggle | Toggle | on, off, focused | `"Reduce Motion"` |
| Colour Blind Mode | Toggle | on, off, focused | `"Colour Blind Mode"` |
| **Mods section** | | | |
| Army Mod Folder | Text + Button | default, focused, error | Path string + `"..."` browse button |
| **Footer** | | | |
| Reset to Defaults | Button (Danger) | default, hover, active, focused | `"Reset to Defaults"` |
| Back | Button (Secondary) | default, hover, active, focused | `"← Back"` |
| Apply | Button (Primary) | default, hover, active, focused | `"✓ Apply"` |

---

## Interaction States

### Toggle Component

```
Off state:
  Background pill: COLOUR_BTN_DEFAULT (#324664)
  Thumb: circle (20px diameter), white, positioned left
  Label: COLOUR_TEXT_SECONDARY (#A0AFC3)

On state:
  Background pill: COLOUR_BTN_SELECTED (#2D8246)
  Thumb: positioned right
  Label: COLOUR_TEXT_PRIMARY (#E6E6E6)

Transition: thumb slides left↔right over 150 ms ease-in-out

Focused: 3px COLOUR_FOCUS_RING (#F39C12) outline around pill
```

### Slider Component

```
Track: 4px height, background COLOUR_PANEL_BORDER (#32415F)
Fill (left of thumb): COLOUR_BTN_PRIMARY (#2980B9)
Thumb: circle 16px diameter, COLOUR_TEXT_PRIMARY (#E6E6E6)
Thumb hover: scale 1.2, 100ms
Dragging: thumb snaps to mouse X within track bounds
Value label: shown to the right of the track, FONT_SMALL

Disabled (when toggle is off):
  Track fill: COLOUR_BTN_DISABLED (#283241)
  Thumb: COLOUR_TEXT_DISABLED (#646E7D)
  cursor: not-allowed
```

### Folder Picker

```
Text field: background COLOUR_SURFACE (#283A58), 1px border COLOUR_PANEL_BORDER
  Read-only display of the current path
  Text: FONT_SMALL, truncated with "..." prefix if path exceeds field width

"..." Button: 40×40px, Secondary style
  Opens the OS folder-picker dialog (via tkinter.filedialog or equivalent)
  
Error state (invalid path):
  Border changes to COLOUR_INVALID (#E74C3C)
  Error label below: "Folder not found — check the path" in COLOUR_INVALID
```

### Back Button — Unsaved Changes

If the user clicks "Back" while there are unsaved changes, show a confirmation
dialog:

```
+-------------------------------------------+
|  Discard Changes?                          |
|                                           |
|  Your settings changes have not been      |
|  saved. Do you want to discard them?      |
|                                           |
|  [ Keep Editing ]        [ Discard ]      |
+-------------------------------------------+
```

### Apply Button

"Apply" writes all settings to `config.yaml` and navigates back to
`MainMenuScreen`. If resolution or fullscreen was changed, the display mode is
reconfigured immediately before navigating.

### Reset to Defaults

"Reset to Defaults" restores factory config and refreshes all controls without
navigating away. Show a brief toast: `"Settings reset to defaults"` for 2 s.

---

## Persistence

Settings are persisted to `config.yaml` via the Infrastructure Layer. The
`SettingsScreen` reads from `config.yaml` in `on_enter()` and writes in
`_on_apply()`:

```python
def on_enter(self, data):
    config = self._config_service.load()
    self._resolution = config.resolution
    self._fullscreen = config.fullscreen
    self._fps_cap = config.fps_cap
    ...
```

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Tab` / `Shift+Tab` | Cycle through all controls top-to-bottom |
| `Space` | Toggle focused toggle component |
| `←` / `→` | Adjust focused slider by 1 step |
| `Home` / `End` | Slider to minimum / maximum |
| `Enter` | Apply (when Apply button focused) |
| `Escape` | Back (with unsaved-changes confirmation if needed) |

---

## Annotations

1. **Section grouping:** Dividing settings into Display / Audio / Game / Mods
   sections matches the mental model of most desktop application settings
   screens. Avoids a wall of unlabelled controls.

2. **Audio sliders are disabled when toggle is off:** This prevents a confusing
   state where the volume slider shows 0 but sound is enabled, or the slider is
   non-zero but sound is disabled. The dependency is made explicit.

3. **Folder picker:** `tkinter.filedialog.askdirectory()` is the simplest
   cross-platform approach. It must be imported lazily to avoid importing tkinter
   at module load time (which can cause display issues on some Linux configs).

4. **FPS cap display:** Show the current value next to the slider (e.g. `"60"`).
   At the extremes, show `"30 (min)"` and `"144 (max)"`.

---

## UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Resolution change breaks layout immediately (before Apply) | Low | High | Apply display changes only on "Apply" click, not on dropdown change |
| Invalid mod folder path causes silent failure | Medium | Medium | Validate path on Apply; show error label if invalid |
| "Reset to Defaults" accidentally triggered | Low | Medium | Position it on the left (away from primary action), use Danger colour, no confirmation needed (settings can be re-applied) |

---

## Open Questions

- [ ] Should settings changes take effect immediately (live preview) or only on "Apply"?
- [ ] Which resolutions should be in the dropdown? (Depends on minimum hardware target)
- [ ] Should there be a `language` / locale setting at v1.0?

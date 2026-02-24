# Accessibility Guidelines: Conqueror's Quest

**Version:** v1.0 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Standard:** WCAG 2.1 Level AA (where feasible within a pygame desktop app)

---

## 1. Scope and Feasibility Notes

WCAG 2.1 is written for web content. A pygame desktop application cannot
satisfy all criteria (e.g. screen-reader AT APIs require OS-level accessibility
hooks that pygame-ce does not expose natively). This document identifies which
criteria **can** be met, **should** be met, and are **out of scope** for v1.0.

| Category | Feasibility in pygame | Target |
|---|---|---|
| Colour contrast | ✅ Fully controllable via palette | Must implement |
| Keyboard navigation | ✅ pygame keyboard events available | Must implement |
| Focus indicators | ✅ Drawn directly on the surface | Must implement |
| Text alternatives for icons | ⚠️ No AT API — provide tooltips instead | Should implement |
| Screen reader support | ❌ Not achievable without OS accessibility hooks | Out of scope v1.0 |
| Reflow / zoom | ⚠️ Font size can be scaled; layout must be tested | Should implement |
| Reduced motion | ✅ Can be added as a settings toggle | Could implement |

---

## 2. Colour Contrast

### 2.1 Requirements (WCAG 1.4.3, AA)

- Normal text (< 18 pt or < 14 pt bold): **≥ 4.5:1** contrast ratio
- Large text (≥ 18 pt or ≥ 14 pt bold): **≥ 3:1** contrast ratio
- Non-text UI components (button borders, focus rings): **≥ 3:1** contrast ratio

### 2.2 Current Palette Compliance

See the [Visual Style Guide](./ux-visual-style-guide.md) §2.6 for the full
compliance table. All palette tokens are WCAG AA compliant.

### 2.3 Colour-Blindness Accommodation

Conqueror's Quest has two teams identified by **Red** and **Blue**. For players
with deuteranopia or protanopia (red-green colour blindness), Red and Blue are
distinguishable (blue is unaffected). However, **do not rely on colour alone**:

| Element | Colour-only (current) | Accessible alternative |
|---|---|---|
| Active player indicator | Team colour text | Team colour text **+ player icon** (♦ for Red, ♠ for Blue) |
| Friendly vs enemy pieces | Not yet differentiated in render | Add a **border pattern**: friendly pieces have a solid border; enemy pieces have a dashed border |
| Valid move vs invalid flash | Green vs red fill | Add **shape**: valid moves show a dot (●); invalid shows an X (✕) in the cell centre |
| Selected piece | Yellow fill | Add a **pulsing border** (2 px, 800 ms) in addition to the fill |

### 2.4 Colour Mode Setting (Could Have for v1.0, Must Have for v2.0)

Add a `colour_blind_mode` toggle in `SettingsScreen` that switches to a
high-contrast palette:

- Replace `#C83C3C` (Red team) with `#D35400` (orange) — distinguishable from
  blue for all common colour-vision deficiencies
- Replace `#3C6ED2` (Blue team) with `#1A5276` (darker blue) to improve
  contrast with the orange

---

## 3. Keyboard Navigation

### 3.1 Requirements (WCAG 2.1.1, A)

All functionality must be operable via keyboard alone (no mouse required).

### 3.2 Navigation Model

Implement a `_focused_button_index: int` state variable in every screen that
contains buttons. The focus model is:

| Key | Action | Screen context |
|---|---|---|
| `Tab` | Advance focus to next interactive element | All screens |
| `Shift+Tab` | Move focus to previous interactive element | All screens |
| `Enter` / `Space` | Activate the focused button | All screens |
| `Escape` | Invoke the "Back" or "Cancel" action | All screens with Back |
| `Arrow keys` | Navigate within a button group (mode toggle, difficulty) | Start Game |
| `A` | Auto-arrange | Setup |
| `C` | Clear | Setup |
| `R` | Confirm ready | Setup |
| `Q` | Abandon | Setup |
| `F` | Flip board | Playing |
| `S` | Save game | Playing |
| `?` / `F1` | Show keyboard shortcut overlay | All screens |

### 3.3 Focus Order

Focus order must follow visual reading order (top-to-bottom, left-to-right):

- **Main Menu:** Start Game → Continue → Load Game → Settings → Quit
- **Start Game:** 2-Player/vs-Computer toggle → Difficulty (if visible) → Back → Confirm
- **Army Select:** Player 1 dropdown → Player 2 dropdown (if 2-player) → Back → Confirm
- **Setup:** Auto-arrange → Clear → Abandon → Ready
- **Playing:** Board cells (row-major order) → Save → Undo (if enabled) → Quit to Menu
- **Game Over:** Main Menu → Play Again → Quit

### 3.4 Focus Indicator

Draw a visible focus indicator around the focused element using:

```python
# Example for button focus ring
FOCUS_COLOUR = (243, 156, 18)  # #F39C12
pygame.draw.rect(surface, FOCUS_COLOUR, btn_rect.inflate(6, 6), width=3, border_radius=10)
```

The focus ring must:
- Be at least 3 px wide
- Have ≥ 3:1 contrast ratio against both the button colour and the
  background behind the button (the `#F39C12` gold satisfies this on all
  current background colours)
- Be visible even when the button is in the hover state

---

## 4. Text and Readability

### 4.1 Minimum Font Sizes

| Context | Current | Recommended | WCAG note |
|---|---|---|---|
| Main body text | 24 px | 24 px | ✅ Good |
| Small labels | 18 px | 18 px | ✅ Acceptable |
| Panel counters | 18 px | 18 px | ✅ Acceptable |
| Tooltip text | Not implemented | 18 px minimum | Implement |
| Badge/shortcut hints | Not specified | 14 px, bold | Acceptable for incidental text |

### 4.2 Text Scaling (Could Have for v1.0)

Add a `ui_scale` setting (0.75, 1.0, 1.25, 1.5) to `SettingsScreen` that
multiplies all font sizes. The layout must be designed to accommodate 1.25×
without truncation.

### 4.3 No Text in Images

All text must be rendered via `pygame.font.render()` — never baked into image
assets. This ensures text responds to the `ui_scale` setting and is legible at
high display DPI.

---

## 5. Motion and Animation

### 5.1 WCAG 2.3.3 — Animation from Interactions (AAA — aspirational)

Provide a `reduce_motion` setting in `SettingsScreen`. When enabled:
- Skip screen slide transitions (jump cut instead of 180 ms slide)
- Replace the pulsing selection highlight with a static highlight
- Remove the AI-thinking ellipsis animation (show static `"AI thinking…"`)
- Skip the piece placement stagger animation (show immediately)

This setting protects players with vestibular disorders. While AAA is not
required for AA compliance, it is a low-effort quality-of-life improvement.

Implementation: add `REDUCE_MOTION: bool` to `config.yaml` and read it in
each animation method:

```python
if not config.reduce_motion:
    self._run_placement_animation()
else:
    self._place_immediately()
```

---

## 6. Pointer Targets

### 6.1 WCAG 2.5.5 — Target Size (AA for WCAG 2.2)

Interactive targets must be **at least 24 × 24 px** (AA) or **44 × 44 px**
(AAA, recommended).

Current button sizes:
- Main Menu buttons: 280 × 52 px ✅ 
- Start Game mode buttons: 200 × 48 px ✅
- Setup panel buttons: 160 × 40 px ⚠️ (height is borderline — increase to 44 px)
- Playing "Quit to Menu" button: 160 × 40 px ⚠️ (increase to 44 px)

**Recommendation:** Set a minimum button height of 44 px across all panels.

---

## 7. Error Identification and Recovery

### 7.1 WCAG 3.3.1 — Error Identification

Error messages must:
1. Identify the field or element in error
2. Describe the error in text (not colour alone)
3. Be perceivable at WCAG AA contrast ratios

Current gaps:
- Invalid-move flash is a **colour-only** error indicator — fix by adding
  text feedback in the status panel (already partially implemented in
  `_on_invalid_move`) and an icon (`✕`) in the flashed cell.

### 7.2 Error Message Mapping

Map all domain error codes to plain-language messages. See
[ux-heuristics-evaluation.md §H9](./ux-heuristics-evaluation.md) for the
full mapping table.

---

## 8. Implementation Checklist

Use this checklist when reviewing each screen before Sprint 4 sign-off:

- [ ] All interactive elements reachable via Tab key
- [ ] Focus indicator visible on every button in focused state
- [ ] Escape key dismisses the current screen / returns to previous
- [ ] Enter/Space activates the focused button
- [ ] Colour contrast ≥ 4.5:1 for all normal text
- [ ] Colour contrast ≥ 3:1 for all interactive component borders
- [ ] No information conveyed by colour alone (error states include text/icon)
- [ ] All team/player identity shown with colour + shape/pattern
- [ ] Minimum button height 44 px on all panels
- [ ] Error messages describe the problem in plain language
- [ ] Tooltip text ≥ 18 px

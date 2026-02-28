# Wireframe: Unit Task Popup Overlay

**Version:** v0.1 Draft  
**Screen class:** `TaskPopupOverlay` (modal rendered within `PlayingScreen`)  
**Last updated:** 2026-02-28  
**Specification ref:** [`screen_flow.md §3.7`](../specifications/screen_flow.md), [`custom_armies.md §4`](../specifications/custom_armies.md)  
**Parent issue:** [#79 – Feature: unit specific task displayed on unit capture](https://github.com/Ariedis/Stratego/issues/79)

---

## 1. Feature Overview

When a custom army unit captures an enemy piece, and that capturing unit has
**tasks** configured in its army mod (`army.json`), the game pauses and
displays a full-screen modal overlay to the **captured player** (the player
whose piece was just taken). The overlay presents one task selected at random
from the capturing unit's task list. The captured player must complete the
physical task and then click the **"Complete ✓"** button to dismiss the
overlay and allow play to continue.

### 1.1 Trigger Conditions

| Condition | Popup shown? | Notes |
|---|---|---|
| Capturing unit's `UnitCustomisation` has one or more tasks | ✅ Yes | Task selected at random from the list |
| Capturing unit has no tasks (or uses Classic army) | ❌ No | `CombatResolved` event proceeds normally |
| Capturing player is the AI (vs AI mode) | ✅ Yes | Human player is the captured player; popup appears to them |
| Captured player is the AI (vs AI mode) | ❌ No | AI has no human to display the popup to; popup suppressed |
| Both players are AI (headless / simulation) | ❌ No | Popup always suppressed for non-human players |

---

## 2. Layout (1280 × 720 reference)

```
+══════════════════════════════════════════════════════════════════════+
║  SCRIM: full window, black #000000 at 75% opacity                   ║
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐   ║
║  │ HEADING ROW  bg: COLOUR_PANEL #1E2D46                        │   ║
║  │                                                              │   ║
║  │  ●  TASK ASSIGNED BY BLUE SCOUT RIDER   ← FONT_BODY 24px    │   ║
║  │  ────────────────────────────────────────────────────────    │   ║
║  │     Scout Rider captured your Miner!    ← FONT_SMALL 18px   │   ║
║  │                                                              │   ║
║  ├──────────────────────────────────────────────────────────────┤   ║
║  │ CONTENT ROW  bg: COLOUR_SURFACE #283A58                      │   ║
║  │                                                              │   ║
║  │  ┌─────────────────────┐   ┌──────────────────────────────┐ │   ║
║  │  │ IMAGE PANEL         │   │ TEXT PANEL                   │ │   ║
║  │  │ 240 × 240 px        │   │                              │ │   ║
║  │  │                     │   │  Your task:                  │ │   ║
║  │  │  ┌───────────────┐  │   │  ← FONT_SMALL #A0B9D2       │ │   ║
║  │  │  │               │  │   │                              │ │   ║
║  │  │  │  situps.gif   │  │   │  "Do 20 situps"              │ │   ║
║  │  │  │  (animating)  │  │   │  ← FONT_SUBHEADING 32px Bold │ │   ║
║  │  │  │               │  │   │    #E6E6E6                   │ │   ║
║  │  │  └───────────────┘  │   │                              │ │   ║
║  │  │                     │   │  Complete this exercise       │ │   ║
║  │  └─────────────────────┘   │  before your opponent        │ │   ║
║  │                            │  continues.                  │ │   ║
║  │                            │  ← FONT_SMALL #A0AFC3        │ │   ║
║  │                            │                              │ │   ║
║  │                            │         ┌────────────────┐   │ │   ║
║  │                            │         │  Complete ✓    │   │ │   ║
║  │                            │         │  200 × 52 px   │   │ │   ║
║  │                            │         │  #2980B9       │   │ │   ║
║  │                            │         └────────────────┘   │ │   ║
║  │                            └──────────────────────────────┘ │   ║
║  │                                                              │   ║
║  └──────────────────────────────────────────────────────────────┘   ║
║                                                                      ║
║  Card: 720 × 380 px centred, COLOUR_SURFACE #283A58,                ║
║        border_radius=12, drop-shadow 0 4px 24px rgba(0,0,0,0.5)     ║
+══════════════════════════════════════════════════════════════════════+
```

### 2.1 Dimensions and Positioning

| Element | Size | Position |
|---|---|---|
| Scrim | Full window | Covers entire `PlayingScreen`; z-index above board |
| Modal card | 720 × 380 px | Centred horizontally and vertically in window |
| Heading row | Full card width × 72 px | Top of card; `COLOUR_PANEL #1E2D46` bg |
| Image panel | 240 × 240 px | Left third of content row; 16 px padding from edge |
| Text panel | ~400 × 240 px | Right portion of content row; 16 px internal padding |
| Complete button | 200 × 52 px | Bottom-right of text panel; 16 px margin from edges |

---

## 3. Element Inventory

| Element | Type | State(s) | Label / Content |
|---|---|---|---|
| Scrim overlay | Decoration | always shown while popup visible | Black `#000000` at 75% alpha |
| Modal card | Container | shown / hidden (animated) | `COLOUR_SURFACE #283A58`, `border_radius=12` |
| Team dot | Decoration | static | 10 px filled circle; `COLOUR_TEAM_BLUE #3C6ED2` or `COLOUR_TEAM_RED #C83C3C` |
| Heading text | Text | static | `"TASK ASSIGNED BY [TEAM] [UNIT NAME]"`, `FONT_BODY 24 px`, Bold |
| Capture subtitle | Text | static | `"[Capturing unit name] captured your [Captured unit name]!"`, `FONT_SMALL 18 px`, `COLOUR_TEXT_SECONDARY` |
| Heading divider | Decoration | static | 1 px horizontal rule, `COLOUR_PANEL_BORDER #32415F` |
| Task image | Image / GIF display | static or looping animation | Content from `task.image_path`; 240 × 240 px scaled |
| No-image placeholder | Decoration | shown when no image defined | Centred "💪" at 64 px font size; `COLOUR_PANEL #1E2D46` bg |
| "Your task:" label | Text | static | `"Your task:"`, `FONT_SMALL 18 px`, `COLOUR_SUBTITLE #A0B9D2` |
| Task description | Text | static | Task wording from mod (e.g. `"Do 20 situps"`), `FONT_SUBHEADING 32 px`, Bold, `COLOUR_TEXT_PRIMARY #E6E6E6`; wraps to max 4 lines |
| Instruction text | Text | static | `"Complete this exercise before your opponent continues."`, `FONT_SMALL 18 px`, `COLOUR_TEXT_SECONDARY #A0AFC3` |
| Complete button | Button (Primary) | default, hover, active, focus | `"Complete ✓"`, `COLOUR_BTN_PRIMARY #2980B9` |

---

## 4. Interaction States

### 4.1 Popup Appearance Sequence

When `CombatResolved` fires with a winning unit that has tasks configured:

1. The `PlayingScreen` completes all existing combat animations (piece flash,
   600 ms) as normal.
2. After animations complete, the scrim fades in from `alpha=0` to `alpha=190`
   over **300 ms**.
3. The modal card simultaneously scales in from `scale=0.85` to `scale=1.0`
   with `cubic-ease-out` timing. *(Rationale: Board Game Arena uses a 200–350 ms
   card-reveal ease-out for modal dialogs; this matches player expectations for
   overlay announcements in web-based board games.)*
4. If the task image is an animated GIF, the animation begins immediately and
   loops continuously until the popup is dismissed.
5. All board input is blocked immediately at step 2.

### 4.2 Complete Button States

| State | Background | Text | Effect |
|---|---|---|---|
| Default | `COLOUR_BTN_PRIMARY #2980B9` | `#E6E6E6`, `FONT_BODY 24 px` | `border_radius=8` |
| Hover | `COLOUR_BTN_HOVER #486490` | `#E6E6E6` | 150 ms `ease-in-out` background transition |
| Active (pressed) | `COLOUR_BTN_ACTIVE #243650` | `#E6E6E6` | `scale 0.97`, 80 ms |
| Focus (keyboard) | `#2980B9` | `#E6E6E6` | 3 px `COLOUR_FOCUS_RING #F39C12` outline, 2 px offset |

### 4.3 Popup Dismissal Sequence

When the **"Complete ✓"** button is clicked or activated via Enter/Space:

1. Any GIF animation stops.
2. The modal card scales out from `scale=1.0` to `scale=0.85` over **200 ms**
   with `ease-in` timing.
3. The scrim fades out from `alpha=190` to `alpha=0` simultaneously.
4. The `PlayingScreen` restores normal board input.
5. Turn management advances as per the post-combat normal flow.

### 4.4 Input Blocking (while popup is visible)

| Input | Behaviour |
|---|---|
| Board cell click (piece select / move) | Blocked |
| `S` (Save), `U` (Undo), `Q` (Quit), Arrow keys | Suppressed |
| `Tab` | Moves focus to "Complete ✓" button (only focusable element) |
| `Enter` / `Space` | Activates focused "Complete ✓"; dismisses popup |
| `Escape` | **No action** — popup cannot be dismissed with Escape (accidental dismissal would bypass the task) |
| Mouse click anywhere outside card | **No action** — click-outside-to-dismiss is disabled |

---

## 5. Heading Row Detail

```
┌──────────────────────────────────────────────────────────────────┐
│  ●  TASK ASSIGNED BY BLUE SCOUT RIDER    ← team dot + FONT_BODY  │
│  ──────────────────────────────────────                           │
│  Scout Rider captured your Miner!        ← FONT_SMALL, secondary │
└──────────────────────────────────────────────────────────────────┘
```

- The **team dot** (●) is a filled circle of radius 10 px coloured
  `COLOUR_TEAM_BLUE #3C6ED2` when the Blue army's unit triggered the task,
  or `COLOUR_TEAM_RED #C83C3C` when the Red army's unit triggered it.
- `"TASK ASSIGNED BY"` is rendered in `COLOUR_TEXT_SECONDARY #A0AFC3`;
  `"BLUE SCOUT RIDER"` (team + unit name) is rendered in the team colour
  to reinforce visual identity. Both words on the same line.
- Subtitle `"Scout Rider captured your Miner!"` uses the capturing unit's
  `display_name` from the mod and the captured unit's `display_name`.

---

## 6. Task Image Panel Detail

```
┌───────────────────────┐
│  ┌─────────────────┐  │
│  │                 │  │   ← 16 px padding around image
│  │   situps.gif    │  │
│  │   (animated)    │  │   ← 240×240 px max; aspect-ratio preserved
│  │                 │  │     letterboxing with COLOUR_PANEL #1E2D46
│  └─────────────────┘  │
└───────────────────────┘
   Panel bg: COLOUR_PANEL #1E2D46
```

**Image resolution priority:**

1. Path from `task.image_path` (resolved relative to the mod folder).
2. If path is `None` or file cannot be loaded → **placeholder** displayed:
   a "💪" emoji rendered at 64 px, centred in the 240 × 240 px panel.

**GIF handling:** Animated GIFs are pre-extracted into frame lists by
`SpriteManager` at mod load time. Within the popup, the frame timer advances
independently from the main game loop delta time so the GIF plays at its
native frame rate even while board input is frozen.

---

## 7. Data Model Extensions Required

> **Note to developers:** The following changes are required in the
> infrastructure and domain layers to support this UX design. The UX
> design drives these requirements; implementation details are delegated to
> developers following [`custom_armies.md`](../specifications/custom_armies.md).

### 7.1 Extended `army.json` Schema

The `units[rank]` object gains a new optional `tasks` array:

```json
{
  "mod_version": "1.0",
  "army_name": "Fitness Army",
  "units": {
    "LIEUTENANT": {
      "display_name": "Scout Rider",
      "tasks": [
        {
          "description": "Do 10 pushups",
          "image": "images/tasks/pushups.gif"
        },
        {
          "description": "Do 20 situps",
          "image": "images/tasks/situps.gif"
        },
        {
          "description": "Do 5 burpees",
          "image": "images/tasks/burpees.gif"
        }
      ]
    }
  }
}
```

**New fields:**

| Field | Type | Required | Validation |
|---|---|---|---|
| `tasks` | `list[object]` | No | Empty list or absent → no popup triggered |
| `tasks[n].description` | `string` | Yes (per task) | 1–120 characters; task skipped with warning if violated |
| `tasks[n].image` | `string` (relative path) | No | Relative to mod folder; absolute paths rejected; missing file shows placeholder with warning |

### 7.2 Extended `UnitCustomisation` Model

```
UnitCustomisation:
    rank: Rank
    display_name: str
    display_name_plural: str
    image_paths: list[Path]
    tasks: list[UnitTask]           ← NEW (empty list if not defined)
```

### 7.3 New `UnitTask` Value Object

```
UnitTask:
    description: str                ← task wording, 1–120 chars
    image_path: Path | None         ← absolute path from mod folder; None if omitted
```

### 7.4 Suggested Mod Task Image Directory

```
mods/
└── fitness_army/
    ├── army.json
    └── images/
        ├── lieutenant/
        │   └── scout_rider.png
        └── tasks/                  ← task images sub-folder (new convention)
            ├── pushups.gif
            ├── situps.gif
            └── burpees.gif
```

---

## 8. Mod Validation Rules (additions to `custom_armies.md §4.3`)

| Rule | Error behaviour |
|---|---|
| `tasks[n].description` must be 1–120 characters | That task skipped; warning logged; other tasks remain valid |
| `tasks[n].image` must be a relative path (no `..` or leading `/`) | Image treated as missing; placeholder shown; warning logged |
| `tasks[n].image` file does not exist or is unreadable | Placeholder shown; warning logged |
| `tasks[n].image` extension not in supported list (`.png`, `.jpg`, `.gif`, `.bmp`) | Placeholder shown; warning logged |

---

## 9. Annotations

1. **Suppress for AI players.** The popup MUST only appear to human players.
   When the captured player is the AI (i.e. the human captured the AI's piece),
   no popup is shown even if the human's capturing unit has tasks configured.
   The turn proceeds immediately. *(Rationale: the AI cannot physically perform
   a task; suppressing for AI players is the only sensible behaviour.)*

2. **Task selection is stateless.** Each combat event independently calls
   `random.choice(unit_customisation.tasks)`. The selection is not persisted
   or tracked across turns. This is intentional — a repeated task from the
   same unit in the same game is acceptable and keeps implementation simple.

3. **"Complete ✓" button placement (bottom-right).** The F-pattern of reading
   causes the eye to rest at the lower-right of a text block. Placing the
   confirmation button there (following Fitts's Law terminal-point placement)
   means the player's cursor arrives near the button naturally after reading
   the task description. This pattern is used consistently in Board Game Arena
   and Tabletop Simulator dialog boxes.

4. **No auto-dismiss timer.** The popup has no countdown. Requiring explicit
   confirmation upholds the spirit of the feature (players must complete the
   task honestly). A *Could Have* enhancement (§13 Q1) would add a minimum
   dwell time before the button activates, but this is not required for v1.0.

5. **Card width at higher resolutions.** At 1920 × 1080 and above, the modal
   card scales proportionally to a maximum of 880 px wide, then stays fixed.
   At 1280 × 720, the card fills approximately 720 px wide.

6. **2-player local handover.** In 2-player local mode the popup appears
   during the opponent's turn. The currently-seated player (who just made their
   move) must hand the device to the captured player. No additional handover
   overlay is needed — the task popup already occupies the full screen,
   preventing the seated player from seeing board state while the other player
   reads and completes their task.

---

## 10. UX Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Player dismisses popup without completing the task | High | Low (trust-based game) | Social enforcement; see Q1 for optional dwell timer |
| GIF animation stutters due to large file | Medium | Low | Pre-extract frames at load; decouple popup frame timer from game loop; warn in mod docs that GIFs > 2 MB may stutter |
| Task description overflows text panel | Low | Medium | 120-character hard limit; text wraps to 4 lines max at `FONT_SUBHEADING 32 px` within the ~400 px text panel |
| Player accidentally presses Escape thinking it dismisses | Low | Medium | Escape explicitly blocked (§4.4); visual hint: "Press Enter or click Complete ✓" shown in small text below button |
| Path traversal via `tasks[n].image` field in `army.json` | Low | High | Validate: absolute paths and `..` segments rejected per `custom_armies.md §10` |
| Task popup shown during vs AI mode to the wrong player | Medium | High | Trigger condition check in `PlayingScreen` must verify `captured_player.player_type == PlayerType.HUMAN` before showing popup |

---

## 11. Keyboard Navigation Summary

| Key | Action |
|---|---|
| `Tab` | Moves focus to "Complete ✓" button (only focusable element in the popup) |
| `Enter` / `Space` | Activates the focused "Complete ✓" button |
| `Escape` | **Blocked** — no action while popup is visible |
| All other keys | Suppressed while popup is visible |

The popup satisfies WCAG 2.1 AA keyboard accessibility: all functionality is
reachable via keyboard only, and the "Complete ✓" button has a visible 3 px
`#F39C12` focus ring.

---

## 12. Competitive Context

This feature has analogues in gamified fitness and physical-activity games:

| Product | Mechanism | Reference |
|---|---|---|
| **Wii Sports / Ring Fit Adventure** (Nintendo) | Game pauses and shows a physical challenge prompt with an illustration before resuming | In-game UI; pause-overlay pattern with single confirmation CTA |
| **Board Game Arena** | Combat result dialogs use a centred card with image, description text, and a single "Continue" CTA at the bottom-right | [boardgamearena.com](https://boardgamearena.com) |
| **Habitica** | Fitness "quests" with task descriptions and image icons shown in a modal card | [habitica.com/static/front](https://habitica.com/static/front) |

**Key pattern adopted from BGA:** centred modal card, image-left / text-right
two-column layout, single primary CTA in the bottom-right corner of the text
column.

**Key pattern adopted from Nintendo fitness titles:** game freezes completely
(no timer, no input) until the player confirms completion — reinforcing that
the physical task is the primary action, not the button click.

---

## 13. Open Questions

- [ ] **Q1 — Minimum dwell time (Could Have):** Should the "Complete ✓"
      button be initially disabled for a minimum period (e.g. 5 s) to prevent
      accidental instant dismissal? If yes, render a circular progress ring
      around the button border that fills over the dwell period, then enables
      the button. This is a Could Have for v1.0.
- [ ] **Q2 — Layout orientation:** Image is always on the left. Should the
      layout invert to text-left / image-right when the current player's
      language is right-to-left (Arabic, Hebrew)? Current proposal: no
      inversion — keep image-left for simplicity in v1.0 and revisit for i18n.
- [ ] **Q3 — Multiple captures in one turn (Scout multi-square move):** Can a
      Scout move multiple squares and capture? Per `game_components.md §4.2`,
      a Scout stops on the first enemy piece it encounters — only one capture
      per move. Confirm: at most one task popup per turn. This is expected.
- [ ] **Q4 — Reveal of opponent rank during popup:** When the popup is
      displayed, both pieces' ranks are already revealed (combat has resolved).
      The popup heading mentions the capturing unit's display name — this does
      not leak additional information beyond what `CombatResolved` already
      reveals. Confirm this is acceptable.
- [ ] **Q5 — Font support for non-Latin task descriptions:** If tasks contain
      non-Latin characters, the `load_font()` helper's fallback chain must
      include a font with broader Unicode coverage (e.g. `"noto sans"`,
      `"unifont"`). Out of scope for v1.0; flag for mod documentation.

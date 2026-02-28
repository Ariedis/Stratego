# User Journey Map: Unit Task Popup — Playing Screen

**Version:** v0.1 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-28  
**Feature:** Unit Task Popup (parent issue [#79](https://github.com/Ariedis/Stratego/issues/79))  
**Status:** Draft — appended to existing user journeys in `ux-user-journeys.md`

---

## Persona Definitions (inherited from `ux-user-journeys.md`)

| Persona | Summary |
|---|---|
| **Alex** (Novice) | First-time player; plays vs Easy AI; unfamiliar with Stratego rules |
| **Blake** (Experienced) | Long-time Stratego player; uses custom armies; keyboard-first |

---

## Journey 3 — Alex: Experiencing the First Task Popup (vs Custom Fitness Army)

**Persona:** Alex (Novice)  
**Goal:** Complete a game against a custom fitness army; understand and respond to task popups  
**Scenario:** Alex has selected the "Fitness Army" mod, which has tasks on several
unit types. Alex is Red. The Blue AI's Lieutenant (Scout Rider) captures Alex's Miner.
The task popup appears for the first time.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | AI makes a move; combat animation plays | `PlayingScreen` — board | 😐 Focused | Animation is quick; easy to miss | Ensure flash animation (600 ms) is noticeable before popup |
| 2 | Screen dims; a card slides in over the board | Task popup overlay (scrim + card) | 😮 Surprised | No prior warning that this feature exists | Consider a brief "ℹ Tasks enabled" toast on game start when any army has tasks |
| 3 | Reads heading: "TASK ASSIGNED BY BLUE SCOUT RIDER" | Heading row | 🤔 Curious | May not understand why a task appears | Heading is clear; subtitle "Scout Rider captured your Miner!" contextualises it |
| 4 | Looks at the GIF (situps animation) | Image panel | 😄 Amused | If GIF is slow to play, first frame may look static | GIF must be pre-loaded so it starts immediately |
| 5 | Reads "Do 20 situps" | Task description text | 😅 Challenged | Text is clear; no ambiguity | — |
| 6 | Reads "Complete this exercise before your opponent continues." | Instruction text | 🙂 Informed | — | — |
| 7 | Puts device down; does 20 situps | Physical space | 💪 Active | If playing alone, no one enforces completion | Social/trust-based — design cannot enforce physical activity |
| 8 | Returns; clicks "Complete ✓" | Complete button | 😊 Satisfied | Card is clearly visible; button is obvious | — |
| 9 | Popup dismisses; game continues as Red's turn | `PlayingScreen` | 🙂 Resumed | May have forgotten which piece was involved | Consider leaving the "last move" highlight on the board for 2 s after popup dismissal |

### Opportunities (Journey 3)

- **Must Have:** Display a "ℹ This army includes unit tasks" notice on the
  army preview panel in `ArmySelectScreen` so players know before the game
  starts that tasks may appear.
- **Should Have:** After popup dismissal, re-highlight the last-move squares
  (`COLOUR_MOVE_LAST_FROM #E67E22` and `COLOUR_MOVE_LAST_TO #F39C12`) for
  2 s so the player can re-orient after the interruption.
- **Could Have:** Show the task popup "intro" heading with a subtle entrance
  sound effect (if sound is enabled) to signal the new state.

---

## Journey 4 — Blake: Fast Task Confirmation (Keyboard-first, Custom Army)

**Persona:** Blake (Experienced)  
**Goal:** Minimise interruption from task popups; complete them efficiently  
**Scenario:** Blake is playing 2-player local with a friend. Blake's Red Marshal
is captured by Blue's Scout Rider. Blake expects a popup and wants to dismiss
it as fast as possible after completing the task.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | Sees Blue's piece capture Red Marshal | Board — combat animation | 😤 Frustrated (lost Marshal) | — | — |
| 2 | Task popup appears | Task popup overlay | 😐 Neutral | Already knew this army has tasks | — |
| 3 | Glances at task: "Do 10 pushups" | Task description | 😌 Accepting | No keyboard shortcut shown | Add hint text near button: "or press Enter" |
| 4 | Puts laptop aside; does pushups | Physical | 💪 Active | — | — |
| 5 | Returns; presses Enter (keyboard shortcut) | Keyboard — Enter key | 😊 Efficient | Focus must be on button; Tab may be needed first | Auto-focus "Complete ✓" on popup open so Enter works immediately |
| 6 | Popup dismisses; opponent's turn ends | `PlayingScreen` | 🙂 Satisfied | — | — |

### Opportunities (Journey 4)

- **Must Have:** Auto-focus the "Complete ✓" button on popup open so the player
  can press Enter immediately without needing to Tab first. This is critical for
  keyboard-first players (Blake persona) and also reduces time spent in the popup.
- **Should Have:** Display `"Press Enter to complete"` hint text in small type
  (`FONT_SMALL 18 px`, `COLOUR_TEXT_SECONDARY`) below the "Complete ✓" button.

---

## Journey 5 — 2-Player Local Handover with Task Popup

**Persona:** Two friends (Alex and Blake) playing local 2-player  
**Goal:** Complete a task without exposing the seated player's board view  
**Scenario:** Blake (Red) captures Alex's (Blue) unit with a unit that has tasks.
Alex must see the popup; Blake is seated at the device.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | Blake moves Red piece; Blue piece captured | Board — combat animation | 😊 Blake: pleased | — | — |
| 2 | Task popup appears over board | Task popup overlay | 😐 Blake: neutral | Blake sees Alex's task; could theoretically see the board state too — but scrim covers it | The modal card covers most of the board, and the scrim dims the rest — adequate in practice |
| 3 | Blake hands device to Alex | Physical handover | 😐 Neutral | No instruction on screen to hand over device | Add a sub-line in the heading: "Pass the device to [Blue player]" in 2-player local mode |
| 4 | Alex reads task and completes it | Physical | 💪 Active | — | — |
| 5 | Alex clicks "Complete ✓" | Complete button | 😊 Alex: satisfied | — | — |
| 6 | Popup dismisses; it is now Alex's turn | `PlayingScreen` | 🙂 Both players | — | — |

### Opportunities (Journey 5)

- **Should Have:** In 2-player local mode, add a sub-line beneath the capture
  subtitle in the heading row: `"Pass the device to Blue player"` (or
  `"Red player"` as appropriate). This guides the natural handover without
  requiring a separate overlay.
- **Could Have:** An explicit "Pass device" CTA button shown before the "Complete ✓"
  button, similar to the SetupScreen handover overlay — but this adds an extra
  step and the simpler in-heading instruction is sufficient for v1.0.

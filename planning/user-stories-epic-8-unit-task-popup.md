# EPIC-8: Unit Task Popup – User Stories

**Epic:** EPIC-8  
**Phase:** 8  
**Specification refs:**
[`ux-wireframe-task-popup.md`](./ux-wireframe-task-popup.md),
[`ux-user-journeys-task-popup.md`](./ux-user-journeys-task-popup.md),
[`custom_armies.md`](../specifications/custom_armies.md),
[`screen_flow.md §3.7`](../specifications/screen_flow.md),
[`data_models.md`](../specifications/data_models.md)  
**Parent issue:** [#79 – Feature: unit specific task displayed on unit capture](https://github.com/Ariedis/Stratego/issues/79)

---

## US-801: UnitTask Domain Value Object

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-wireframe-task-popup.md §7.2–§7.3`](./ux-wireframe-task-popup.md),
[`data_models.md`](../specifications/data_models.md)

**As a** developer,  
**I want** a `UnitTask` value object and a `tasks` field on `UnitCustomisation`,  
**so that** the domain and infrastructure layers can represent task data without coupling to any UI concern.

### Acceptance Criteria

- [ ] **AC-1:** Given a `UnitTask` constructed with `description="Do 20 situps"` and
      `image_path=Path("mods/fitness_army/images/tasks/situps.gif")`, When accessed,
      Then `unit_task.description == "Do 20 situps"` and `unit_task.image_path`
      resolves to the expected `Path`.
- [ ] **AC-2:** Given a `UnitTask` constructed with `image_path=None`, When accessed,
      Then `unit_task.image_path is None` (no error raised).
- [ ] **AC-3:** Given `UnitCustomisation` constructed without a `tasks` argument,
      When `unit_customisation.tasks` is accessed, Then it returns an **empty list**
      (not `None`).
- [ ] **AC-4:** Given `UnitCustomisation` constructed with a list of two `UnitTask`
      objects, When `unit_customisation.tasks` is accessed, Then both tasks are
      present and the order is preserved.
- [ ] **AC-5:** Given a `UnitTask` instance, When any attribute is mutated,
      Then a `FrozenInstanceError` (or equivalent immutability error) is raised,
      confirming it is a frozen value object.

### Example

```python
task = UnitTask(description="Do 20 situps", image_path=Path("tasks/situps.gif"))
assert task.description == "Do 20 situps"
assert task.image_path == Path("tasks/situps.gif")

customisation = UnitCustomisation(
    rank=Rank.LIEUTENANT,
    display_name="Scout Rider",
    display_name_plural="Scout Riders",
    image_paths=[],
    tasks=[task],
)
assert len(customisation.tasks) == 1
```

### Definition of Done

- [ ] `src/domain/models.py` (or equivalent data-models module) defines `UnitTask`
      as a frozen dataclass with fields `description: str` and
      `image_path: Path | None`.
- [ ] `UnitCustomisation` gains field `tasks: list[UnitTask]` with default
      `field(default_factory=list)`.
- [ ] `tests/unit/domain/test_unit_task.py` covers all five AC scenarios.

### Out of Scope

- Loading tasks from `army.json` (US-802).
- Any UI rendering of tasks (US-803, US-804).

---

## US-802: Army.json Task Parsing and Validation

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-wireframe-task-popup.md §7.1, §8`](./ux-wireframe-task-popup.md),
[`custom_armies.md §4.3`](../specifications/custom_armies.md)

**As a** mod author,  
**I want** the mod loader to parse my `tasks` array from `army.json` and the
mod validator to enforce the task field rules,  
**so that** my custom tasks are available during gameplay and malformed task
entries are rejected with actionable warnings rather than crashing the game.

### Acceptance Criteria

- [ ] **AC-1:** Given a valid `army.json` with
      `"tasks": [{"description": "Do 20 situps", "image": "images/tasks/situps.gif"}]`
      for `LIEUTENANT`, When `mod_loader.discover_mods()` runs, Then
      `unit_customisation.tasks[0].description == "Do 20 situps"` and
      `unit_customisation.tasks[0].image_path` is the resolved absolute `Path`.
- [ ] **AC-2:** Given a task entry where `description` has 121 characters,
      When the mod validator runs, Then that task is **skipped** (not the whole
      mod), a warning is logged containing the field name and rank, and all
      other tasks for that unit remain valid.
- [ ] **AC-3:** Given a task entry where `description` is an empty string (`""`),
      When the mod validator runs, Then that task is skipped with a warning.
- [ ] **AC-4:** Given a task entry with `"image": "../secrets/password.txt"`
      (path traversal attempt), When the mod validator runs, Then the image is
      treated as missing (placeholder shown); a warning is logged; the task
      description is still loaded.
- [ ] **AC-5:** Given a task entry with `"image": "/absolute/path/image.png"`
      (absolute path), When the mod validator runs, Then the image is treated
      as missing; a warning is logged.
- [ ] **AC-6:** Given a task entry with `"image": "images/tasks/pushups.xyz"`
      (unsupported extension), When the mod validator runs, Then the image is
      treated as missing; a warning is logged.
- [ ] **AC-7:** Given a unit with no `"tasks"` key in `army.json`,
      When loaded, Then `unit_customisation.tasks` is an empty list (no error).
- [ ] **AC-8:** Given a unit with `"tasks": []` (empty array),
      When loaded, Then `unit_customisation.tasks` is an empty list.

### Example

```json
{
  "mod_version": "1.0",
  "army_name": "Fitness Army",
  "units": {
    "LIEUTENANT": {
      "display_name": "Scout Rider",
      "tasks": [
        { "description": "Do 10 pushups", "image": "images/tasks/pushups.gif" },
        { "description": "Do 20 situps",  "image": "images/tasks/situps.gif"  },
        { "description": "Do 5 burpees",  "image": "images/tasks/burpees.gif" }
      ]
    }
  }
}
```

Expected result: `UnitCustomisation(rank=Rank.LIEUTENANT, ..., tasks=[UnitTask(...), UnitTask(...), UnitTask(...)])`

### Definition of Done

- [ ] `src/infrastructure/mod_loader.py` parses `tasks` arrays into
      `list[UnitTask]` within `UnitCustomisation` objects.
- [ ] `src/infrastructure/mod_validator.py` enforces:
      - `description` length 1–120 characters (skip task + warn on violation).
      - `image` is a relative path with no `..` segments and no leading `/`
        (treat as missing + warn on violation).
      - `image` extension is in `{".png", ".jpg", ".jpeg", ".gif", ".bmp"}`
        (treat as missing + warn on violation).
- [ ] `tests/unit/infrastructure/test_mod_loader.py` covers AC-1, AC-7, AC-8.
- [ ] `tests/unit/infrastructure/test_mod_validator.py` covers AC-2 through AC-6.

### Out of Scope

- Rendering the task image (US-806).
- The `TaskPopupOverlay` UI (US-803, US-804, US-805).

---

## US-803: Task Popup Overlay – Visual Layout

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-wireframe-task-popup.md §2, §3, §5, §6`](./ux-wireframe-task-popup.md),
[`screen_flow.md §3.7`](../specifications/screen_flow.md)

**As a** captured player,  
**I want** to see a clearly formatted full-screen modal overlay showing which
unit assigned the task, the task description, and a task image,  
**so that** I immediately understand what physical task I must complete before
the game continues.

### Acceptance Criteria

- [ ] **AC-1:** Given the popup is visible, When rendered at 1280 × 720 px,
      Then a full-window scrim (`#000000` at 75 % alpha) covers the entire
      `PlayingScreen`.
- [ ] **AC-2:** Given the popup is visible, When rendered, Then the modal card
      is centred horizontally and vertically; its size is 720 × 380 px at
      1280 × 720 reference resolution; `border_radius=12`; background
      `COLOUR_SURFACE #283A58`.
- [ ] **AC-3:** Given the Blue team's Lieutenant (display name "Scout Rider")
      captured the Red player's Miner, When the popup is rendered, Then the
      heading row shows:
      - A filled team-colour dot (`COLOUR_TEAM_BLUE #3C6ED2`, radius 10 px).
      - Heading text: `"TASK ASSIGNED BY"` in `COLOUR_TEXT_SECONDARY #A0AFC3`
        followed by `"BLUE SCOUT RIDER"` in `COLOUR_TEAM_BLUE #3C6ED2`; both
        on the same line; `FONT_BODY 24 px` Bold.
      - Subtitle: `"Scout Rider captured your Miner!"` in `FONT_SMALL 18 px`
        `COLOUR_TEXT_SECONDARY`.
- [ ] **AC-4:** Given a task with `image_path` pointing to a valid file,
      When rendered, Then the image is displayed in the image panel at
      240 × 240 px with aspect-ratio-preserving letterboxing; background
      `COLOUR_PANEL #1E2D46`.
- [ ] **AC-5:** Given a task with `image_path = None` or an unreadable file,
      When rendered, Then the image panel shows a "💪" placeholder centred
      at 64 px font size on a `COLOUR_PANEL #1E2D46` background.
- [ ] **AC-6:** Given any task, When rendered, Then the text panel shows:
      - `"Your task:"` label in `FONT_SMALL 18 px` `COLOUR_SUBTITLE #A0B9D2`.
      - Task description in `FONT_SUBHEADING 32 px` Bold `#E6E6E6`; wraps to
        a maximum of 4 lines.
      - Instruction: `"Complete this exercise before your opponent continues."`
        in `FONT_SMALL 18 px` `COLOUR_TEXT_SECONDARY #A0AFC3`.
- [ ] **AC-7:** Given the popup is visible, When rendered, Then the
      **"Complete ✓"** button is 200 × 52 px, positioned at the bottom-right
      of the text panel with 16 px margin, background `COLOUR_BTN_PRIMARY #2980B9`,
      `border_radius=8`.

### Example

```
Heading: ● TASK ASSIGNED BY [blue] BLUE SCOUT RIDER
         Scout Rider captured your Miner!
Image:   situps.gif (or 💪 placeholder)
Task:    "Your task:"
         "Do 20 situps"
         "Complete this exercise before your opponent continues."
Button:  [Complete ✓]
```

### Definition of Done

- [ ] `src/presentation/overlays/task_popup_overlay.py` (new file) implements
      `TaskPopupOverlay` with all elements specified in §3 of the wireframe.
- [ ] Heading row background is `COLOUR_PANEL #1E2D46`; card background is
      `COLOUR_SURFACE #283A58`.
- [ ] Team dot colour toggles between `COLOUR_TEAM_BLUE` and
      `COLOUR_TEAM_RED` based on the capturing player's side.
- [ ] Placeholder (💪) is shown when `image_path is None` or the image fails
      to load.
- [ ] `tests/unit/presentation/test_task_popup_overlay.py` verifies element
      visibility and layout constants (dimensions, colours, font sizes) without
      requiring a running display (use `pytest-mock` / headless pygame).

### Out of Scope

- Popup entrance/exit animation (US-805).
- GIF frame animation within the popup (US-806).
- Input blocking (US-805).

---

## US-804: Task Popup – Trigger and Dismissal Logic

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-wireframe-task-popup.md §1.1, §4.1, §4.3`](./ux-wireframe-task-popup.md),
[`ux-user-journeys-task-popup.md §Journey 3`](./ux-user-journeys-task-popup.md)

**As a** player,  
**I want** the task popup to appear automatically after the combat animation
completes when the capturing unit has tasks configured, and to disappear only
after I click "Complete ✓",  
**so that** I know when a task has been assigned and the game does not continue
until I confirm completion.

### Acceptance Criteria

- [ ] **AC-1:** Given a `CombatResolved` event where the winning unit's
      `UnitCustomisation.tasks` is non-empty and the **captured player is
      human**, When the combat animation (600 ms piece flash) finishes, Then
      `TaskPopupOverlay` is shown.
- [ ] **AC-2:** Given a `CombatResolved` event where the winning unit's
      `UnitCustomisation.tasks` is **empty**, When the event fires, Then
      no popup is shown and turn management proceeds normally.
- [ ] **AC-3:** Given the Classic army is in use (no custom mod), When any
      combat resolves, Then no popup is shown.
- [ ] **AC-4:** Given the captured player is the **AI** (human captured an AI
      piece), When `CombatResolved` fires with a task-enabled capturing unit,
      Then **no popup** is shown and the turn proceeds immediately.
- [ ] **AC-5:** Given both players are AI (headless / simulation mode), When
      any combat resolves, Then the popup is always suppressed.
- [ ] **AC-6:** Given the popup is visible and the player clicks "Complete ✓",
      When the click is registered, Then:
      - The popup begins its exit animation (US-805).
      - After the animation completes, normal board input is restored.
      - Turn management advances to the next phase.
- [ ] **AC-7:** Given the popup is visible, When the task is selected,
      Then it is chosen via `random.choice(unit_customisation.tasks)` (one
      task selected at random per combat event; selection is not persisted).

### Example

```
Scenario A – popup shown:
  Capturing unit: LIEUTENANT (display "Scout Rider"), tasks=[UnitTask("Do 20 situps", ...)]
  Captured player: HUMAN (Red)
  → popup shown; Red player must click "Complete ✓"

Scenario B – popup suppressed:
  Capturing unit: LIEUTENANT, tasks=[...]
  Captured player: AI
  → popup suppressed; turn continues

Scenario C – classic army:
  Capturing unit: MARSHAL (Classic army, tasks=[])
  → popup suppressed
```

### Definition of Done

- [ ] `src/presentation/screens/playing_screen.py` subscribes to
      `CombatResolved` and invokes `TaskPopupOverlay` when trigger
      conditions are met (captured player is human AND tasks non-empty).
- [ ] Task selection uses `random.choice(tasks)`.
- [ ] Post-dismissal: `PlayingScreen` restores board input and advances
      turn management.
- [ ] `tests/unit/presentation/test_playing_screen_task_trigger.py` covers
      all six trigger/suppression scenarios (AC-1 through AC-5) using
      mock events.

### Out of Scope

- Popup visual layout (US-803).
- Animation (US-805).
- GIF playback (US-806).

---

## US-805: Task Popup – Input Blocking, Animation, and Keyboard Navigation

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-wireframe-task-popup.md §4.1–§4.4, §11`](./ux-wireframe-task-popup.md),
[`ux-user-journeys-task-popup.md §Journey 4`](./ux-user-journeys-task-popup.md),
[`ux-accessibility.md`](./ux-accessibility.md)

**As a** player,  
**I want** all board interactions to be blocked while the task popup is visible,
the popup to animate in and out smoothly, and the "Complete ✓" button to be
keyboard-accessible,  
**so that** the task cannot be bypassed by accident and the popup feels
polished and accessible.

### Acceptance Criteria

#### Input Blocking

- [ ] **AC-1:** Given the popup is visible, When the player clicks any board
      cell, Then no piece selection or move occurs.
- [ ] **AC-2:** Given the popup is visible, When the player presses `S` (Save),
      `U` (Undo), `Q` (Quit), or any arrow key, Then the keypress is suppressed
      and no action is taken.
- [ ] **AC-3:** Given the popup is visible, When the player clicks anywhere
      outside the modal card, Then the popup is **not** dismissed.
- [ ] **AC-4:** Given the popup is visible, When the player presses `Escape`,
      Then the popup is **not** dismissed.

#### Animation

- [ ] **AC-5:** Given the popup is triggered, When it appears, Then the scrim
      fades from `alpha=0` to `alpha=190` over **300 ms**; simultaneously the
      modal card scales from `scale=0.85` to `scale=1.0` with `cubic-ease-out`
      timing.
- [ ] **AC-6:** Given the "Complete ✓" button is activated, When the popup
      dismisses, Then the modal card scales from `scale=1.0` to `scale=0.85`
      over **200 ms** with `ease-in` timing; the scrim fades from `alpha=190`
      to `alpha=0` simultaneously.

#### Keyboard Navigation

- [ ] **AC-7:** Given the popup opens, When rendered for the first time,
      Then the "Complete ✓" button receives **auto-focus** immediately so the
      player can press `Enter` without needing to press `Tab` first.
- [ ] **AC-8:** Given the popup is visible and the button is not focused,
      When the player presses `Tab`, Then focus moves to the "Complete ✓"
      button (the only focusable element).
- [ ] **AC-9:** Given the "Complete ✓" button is focused, When the player
      presses `Enter` or `Space`, Then the popup is dismissed (same as clicking
      the button).
- [ ] **AC-10:** Given the button has focus, When rendered, Then a 3 px
      `COLOUR_FOCUS_RING #F39C12` outline with 2 px offset is visible around
      the button (WCAG 2.1 AA compliant focus indicator).

#### Button Hover / Active States

- [ ] **AC-11:** Given the "Complete ✓" button, When the mouse hovers over it,
      Then the background transitions to `COLOUR_BTN_HOVER #486490` over
      150 ms `ease-in-out`.
- [ ] **AC-12:** Given the "Complete ✓" button, When pressed (mouse down),
      Then the button scales to `0.97` over 80 ms and background becomes
      `COLOUR_BTN_ACTIVE #243650`.

### Example

```
Player presses Escape while popup visible → no action (popup stays)
Player presses Enter while button focused → popup dismisses
Player clicks board cell while popup visible → no move registered
```

### Definition of Done

- [ ] `TaskPopupOverlay` intercepts all input events and suppresses non-popup
      events while visible.
- [ ] Entrance animation: 300 ms scrim fade + card scale-up.
- [ ] Exit animation: 200 ms scrim fade-out + card scale-down.
- [ ] Button auto-focused on popup open; `Tab` cycles to the button; `Enter`/
      `Space` activate it; `Escape` is explicitly blocked.
- [ ] Focus ring (`3 px #F39C12`, 2 px offset) rendered when button is focused.
- [ ] `tests/unit/presentation/test_task_popup_input.py` covers AC-1 through
      AC-4 (input blocking) and AC-7 through AC-9 (keyboard nav) using
      mocked pygame event queues.

### Out of Scope

- GIF animation within the image panel (US-806).
- Minimum dwell-time on the button (deferred to Could Have; see
  `ux-wireframe-task-popup.md §13 Q1`).

---

## US-806: Task Image GIF Animation

**Epic:** EPIC-8  
**Priority:** Should Have  
**Specification refs:** [`ux-wireframe-task-popup.md §6`](./ux-wireframe-task-popup.md),
[`custom_armies.md §5.1`](../specifications/custom_armies.md)

**As a** player,  
**I want** an animated GIF task image to play continuously while the task
popup is visible,  
**so that** the illustration of the exercise is lively and unambiguous.

### Acceptance Criteria

- [ ] **AC-1:** Given a task whose `image_path` points to an animated GIF with
      4 frames, When the popup is open, Then the GIF cycles through all 4 frames
      at the GIF's native frame rate.
- [ ] **AC-2:** Given an animated GIF task image, When the popup is open and
      board input is frozen, Then the GIF frame timer advances independently
      using the popup's own `delta_time`, so the animation does **not** stutter
      due to game-loop state.
- [ ] **AC-3:** Given a GIF that is still animating, When the "Complete ✓"
      button is activated, Then the GIF animation stops before the exit
      animation begins.
- [ ] **AC-4:** Given a task whose `image_path` points to a static PNG,
      When the popup is open, Then the image is displayed without animation
      (no flickering; single frame only).
- [ ] **AC-5:** Given a GIF file larger than 2 MB, When loaded at mod-load
      time, Then a warning is logged (`"Task GIF exceeds 2 MB; performance
      may be affected"`), but the GIF still loads and animates.

### Example

```
GIF: situps.gif — 4 frames, 200 ms per frame (5 fps)
While popup open: frames cycle 0→1→2→3→0→1→... at 5 fps
On dismiss: animation stops at current frame; exit animation begins
```

### Definition of Done

- [ ] `TaskPopupOverlay` maintains its own frame index and frame timer for
      animated task images, driven by `delta_time` passed to `update()`.
- [ ] GIF frames are pre-extracted by `SpriteManager` at mod-load time (not
      on popup open) so the popup opens instantly.
- [ ] Animation stops immediately when the "Complete ✓" button is activated.
- [ ] `tests/unit/presentation/test_task_popup_gif.py` covers AC-1 through
      AC-4 using a stub GIF surface list.

### Out of Scope

- GIF animation for piece sprites on the board (covered by US-704).
- Sound effects accompanying the GIF (Could Have; v2.0).

---

## US-807: Army Select Screen – Tasks Notification

**Epic:** EPIC-8  
**Priority:** Must Have  
**Specification refs:** [`ux-user-journeys-task-popup.md §Journey 3 Opportunities`](./ux-user-journeys-task-popup.md),
[`screen_flow.md §3.3`](../specifications/screen_flow.md)

**As a** new player (Alex persona),  
**I want** to see a notice on the Army Select screen when a selected army
includes unit tasks,  
**so that** I am not surprised when the first task popup appears mid-game.

### Acceptance Criteria

- [ ] **AC-1:** Given Player 1 selects an army where at least one
      `UnitCustomisation.tasks` list is non-empty, When the preview panel
      updates, Then an `"ℹ This army includes unit tasks"` notice is
      displayed in the preview panel in `FONT_SMALL 18 px`
      `COLOUR_TEXT_SECONDARY`.
- [ ] **AC-2:** Given Player 1 selects the Classic army (no tasks), When the
      preview panel updates, Then the tasks notice is **not** shown.
- [ ] **AC-3:** Given Player 1 selects an army with tasks, When the cursor
      hovers the notice, Then a tooltip explains:
      `"When a unit with tasks captures an enemy piece, you will be asked
      to complete a physical exercise before the game continues."`.
- [ ] **AC-4:** Given 2-player mode and Player 2 selects an army with tasks,
      When the Player 2 preview panel updates, Then the notice appears in
      the Player 2 preview panel (independent of Player 1's panel).

### Example

```
Player 1 dropdown: "Fitness Army" (has tasks on LIEUTENANT)
→ Preview panel shows: ℹ This army includes unit tasks

Player 1 dropdown: "Classic" (no tasks)
→ Preview panel shows: (no notice)
```

### Definition of Done

- [ ] `src/presentation/screens/army_select_screen.py` inspects
      `any(len(uc.tasks) > 0 for uc in army_mod.unit_customisations.values())`
      after each dropdown change.
- [ ] Notice rendered conditionally in the preview panel using the correct
      font and colour tokens.
- [ ] Tooltip text is correct per AC-3.
- [ ] `tests/unit/presentation/test_army_select_screen_tasks.py` covers
      AC-1 and AC-2.

### Out of Scope

- In-game task list viewer (v2.0).
- Listing which specific units have tasks in the preview panel (Could Have).

---

## US-808: Post-Dismissal Last-Move Re-highlight

**Epic:** EPIC-8  
**Priority:** Should Have  
**Specification refs:** [`ux-user-journeys-task-popup.md §Journey 3 Opportunities`](./ux-user-journeys-task-popup.md),
[`ux-wireframe-playing.md`](./ux-wireframe-playing.md)

**As a** captured player,  
**I want** the squares involved in the last move to be briefly re-highlighted
on the board after I dismiss the task popup,  
**so that** I can re-orient myself on the board after the interruption.

### Acceptance Criteria

- [ ] **AC-1:** Given a task popup is dismissed by clicking "Complete ✓",
      When the popup exit animation completes, Then the "from" and "to" squares
      of the last move are highlighted for **2 seconds** using the standard
      last-move colours:
      - From square: `COLOUR_MOVE_LAST_FROM #E67E22`.
      - To square: `COLOUR_MOVE_LAST_TO #F39C12`.
- [ ] **AC-2:** Given the 2-second re-highlight timer is running, When the
      timer expires, Then the highlight fades back to the normal board square
      colour (no abrupt disappearance).
- [ ] **AC-3:** Given no task popup was shown this turn (normal combat),
      When the turn ends, Then no extra re-highlight is applied (this feature
      is specific to post-popup dismissal).
- [ ] **AC-4:** Given the re-highlight is active and the current player makes
      a new move before the 2 seconds elapse, When the new move begins, Then
      the re-highlight timer is cancelled and the new move highlights replace it.

### Example

```
Turn 14: Blue LIEUTENANT captures Red MINER at (5,4)→(5,5)
→ Task popup shown; Red player completes task; clicks "Complete ✓"
→ Popup dismisses
→ Board squares (5,4) highlighted #E67E22 and (5,5) highlighted #F39C12
   for 2 000 ms, then fade to normal
```

### Definition of Done

- [ ] `src/presentation/screens/playing_screen.py` tracks a
      `post_popup_rehighlight_timer` (ms) after popup dismissal.
- [ ] Last-move squares painted with re-highlight colours while timer > 0.
- [ ] Timer decremented by `delta_time` each frame; highlight removed on
      expiry or new move.
- [ ] `tests/unit/presentation/test_playing_screen_rehighlight.py` covers
      AC-1 through AC-4.

### Out of Scope

- Re-highlighting for non-combat moves.
- Animated "pulse" effect on re-highlight squares (Could Have; v2.0).

---

## US-809: 2-Player Local Handover Prompt

**Epic:** EPIC-8  
**Priority:** Should Have  
**Specification refs:** [`ux-user-journeys-task-popup.md §Journey 5`](./ux-user-journeys-task-popup.md),
[`ux-wireframe-task-popup.md §9 annotation 6`](./ux-wireframe-task-popup.md)

**As a** player in 2-player local mode,  
**I want** the task popup to indicate which player should be looking at the
screen,  
**so that** the seated player knows to hand the device to their opponent before
the opponent reads and completes the task.

### Acceptance Criteria

- [ ] **AC-1:** Given a 2-player local game and the popup is triggered,
      When the popup renders in the heading row, Then a sub-line below the
      capture subtitle reads:
      `"Pass the device to [Blue / Red] player"`
      using the captured player's team colour name; rendered in
      `FONT_SMALL 18 px` `COLOUR_TEXT_SECONDARY`.
- [ ] **AC-2:** Given a vs-AI game and the popup is triggered (human player
      is captured), When the popup renders, Then the `"Pass the device to…"`
      sub-line is **not** shown (it is only relevant in 2-player local mode).
- [ ] **AC-3:** Given a 2-player local game where Red team's unit is captured,
      When the popup heading is rendered, Then the sub-line reads
      `"Pass the device to Red player"`.
- [ ] **AC-4:** Given a 2-player local game where Blue team's unit is captured,
      When the popup heading is rendered, Then the sub-line reads
      `"Pass the device to Blue player"`.

### Example

```
2-player local mode, Blue captures Red's Miner:
  Heading:  ● TASK ASSIGNED BY BLUE SCOUT RIDER
  Subtitle: Scout Rider captured your Miner!
  Sub-line: Pass the device to Red player   ← new element (2-player only)
```

### Definition of Done

- [ ] `TaskPopupOverlay` accepts a `game_mode: GameMode` parameter and
      `captured_player_side: PlayerSide`.
- [ ] Sub-line rendered conditionally when `game_mode == GameMode.TWO_PLAYER`.
- [ ] `tests/unit/presentation/test_task_popup_handover.py` covers AC-1
      through AC-4.

### Out of Scope

- An explicit "Pass device" CTA button before the "Complete ✓" button
  (deferred; `ux-user-journeys-task-popup.md §Journey 5 Opportunities`
  Could Have).
- Any board-state concealment mechanism beyond what the scrim provides.

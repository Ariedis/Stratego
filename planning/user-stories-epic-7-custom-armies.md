# EPIC-7: Custom Armies & Polish – User Stories

**Epic:** EPIC-7  
**Phase:** 7  
**Specification refs:** [`custom_armies.md`](../specifications/custom_armies.md),
[`screen_flow.md §3.3`](../specifications/screen_flow.md)

---

## US-701: Built-In Classic Army

**Epic:** EPIC-7  
**Priority:** Must Have  
**Specification refs:** [`custom_armies.md §8`](../specifications/custom_armies.md)

**As a** player,  
**I want** the game to ship with a built-in "Classic" army that uses the
standard Stratego piece names,  
**so that** the game is immediately playable without any mod files installed.

### Acceptance Criteria

- [ ] **AC-1:** Given `ClassicArmy.get()`, When called, Then returns an
      `ArmyMod` with `army_name="Classic"` and all 12 ranks mapped to
      their official names (e.g., `MARSHAL → "Marshal"`, `BOMB → "Bomb"`).
- [ ] **AC-2:** Given the Classic army, When displayed in any Army Select
      dropdown, Then it appears as the **first** entry.
- [ ] **AC-3:** Given `ClassicArmy`, When attempting to delete or modify it
      at runtime, Then the operation is rejected (immutable).
- [ ] **AC-4:** Given a mod whose image folder for `MARSHAL` is empty,
      When the SpriteManager resolves images, Then the Classic built-in
      image is used as a fallback.

### Example

```python
classic = ClassicArmy.get()
assert classic.unit_customisations[Rank.MARSHAL].display_name == "Marshal"
assert classic.unit_customisations[Rank.BOMB].display_name == "Bomb"
assert classic.mod_id == "classic"
```

### Definition of Done

- [ ] `src/domain/classic_army.py` defines `ClassicArmy` with all 12 rank
      entries as a hard-coded `ArmyMod` singleton.
- [ ] `tests/unit/domain/test_classic_army.py` verifies all display names and
      that it is always first in any loaded army list.

### Out of Scope

- Mod marketplace (v2.0).

---

## US-702: Mod Loader

**Epic:** EPIC-7  
**Priority:** Should Have  
**Specification refs:** [`custom_armies.md §3, §6`](../specifications/custom_armies.md)

**As a** player,  
**I want** the application to automatically discover and load all custom army
mods from the configured mod directory at startup,  
**so that** I can install a mod simply by copying its folder to the mod
directory without any in-game configuration steps.

### Acceptance Criteria

- [ ] **AC-1:** Given a valid mod folder `~/.conquestquest/mods/dragon_horde/`
      containing `army.json`, When `mod_loader.discover_mods(mod_dir)`,
      Then an `ArmyMod` for "Dragon Horde" is returned.
- [ ] **AC-2:** Given a folder with a malformed `army.json` (invalid JSON),
      When `discover_mods()`, Then that mod is skipped, a warning is logged,
      and all other valid mods are still returned.
- [ ] **AC-3:** Given two mod folders with the same `mod_id` (same folder name),
      When `discover_mods()`, Then only the first is loaded; the second is
      skipped with a warning.
- [ ] **AC-4:** Given an empty mod directory, When `discover_mods()`,
      Then an empty list is returned (no error).
- [ ] **AC-5:** Given a mod folder with no `images/` subfolder,
      When loaded, Then the `ArmyMod` is created successfully (images are
      optional; fallback to Classic).

### Example

```
~/.conquestquest/mods/
├── dragon_horde/army.json    ← valid
├── broken_mod/army.json      ← invalid JSON
└── space_age/army.json       ← valid

Result: [ArmyMod("dragon_horde"), ArmyMod("space_age")]
Warning logged for broken_mod.
```

### Definition of Done

- [ ] `src/infrastructure/mod_loader.py` implements `discover_mods(mod_dir: Path) -> list[ArmyMod]`.
- [ ] `src/infrastructure/mod_validator.py` implements `validate_manifest(raw_json) -> list[ValidationError]`.
- [ ] `tests/unit/infrastructure/test_mod_loader.py` covers all AC scenarios
      using temporary directories.

### Out of Scope

- Mod image loading (US-704).
- Mod validation UI feedback (Could Have).

---

## US-703: Mod Validator

**Epic:** EPIC-7  
**Priority:** Should Have  
**Specification refs:** [`custom_armies.md §4.3`](../specifications/custom_armies.md)

**As a** developer,  
**I want** the mod validator to enforce all schema rules from `custom_armies.md §4.3`
and return detailed validation errors,  
**so that** invalid mods are rejected cleanly and mod authors receive
actionable feedback.

### Acceptance Criteria

- [ ] **AC-1:** Given `mod_version = "2.0"` (unsupported), When validated,
      Then `ValidationError(field="mod_version", message="Unsupported version: 2.0")`.
- [ ] **AC-2:** Given `army_name = ""` (empty string), When validated,
      Then `ValidationError(field="army_name", message="Must be 1–64 characters")`.
- [ ] **AC-3:** Given `army_name = "A" * 65` (65 chars), When validated,
      Then `ValidationError(field="army_name", ...)`.
- [ ] **AC-4:** Given `display_name = "A" * 33` (33 chars), When validated,
      Then `ValidationError(field="units.MARSHAL.display_name", ...)`.
- [ ] **AC-5:** Given an unknown rank key `"WIZARD"` in `units`, When validated,
      Then a warning is logged but no error is raised (unknown keys ignored).
- [ ] **AC-6:** Given a fully valid manifest, When validated,
      Then the returned error list is empty.

### Definition of Done

- [ ] `mod_validator.py` implements `validate_manifest(data: dict) -> list[ValidationError]`.
- [ ] `tests/unit/infrastructure/test_mod_validator.py` covers all AC scenarios.

### Out of Scope

- Path traversal checks (handled in SpriteManager, US-704).

---

## US-704: Mod-Aware Sprite Manager

**Epic:** EPIC-7  
**Priority:** Should Have  
**Specification refs:** [`custom_armies.md §5`](../specifications/custom_armies.md)

**As a** player,  
**I want** piece images from my selected custom army to replace the Classic
artwork in-game, with automatic fallback to Classic images when mod images
are unavailable,  
**so that** custom armies look visually distinct without breaking the game
when images are missing or invalid.

### Acceptance Criteria

- [ ] **AC-1:** Given a mod with `images/marshal/dragon_lord.png`, When the
      game loads that army, Then the Marshal piece is rendered with
      `dragon_lord.png`.
- [ ] **AC-2:** Given a mod with no `images/spy/` folder, When the Spy piece
      is rendered, Then the Classic built-in Spy image is used.
- [ ] **AC-3:** Given a mod with 3 images for `images/marshal/`, When the
      game session starts, Then exactly **one** image is randomly selected for
      all Marshals for the duration of that session.
- [ ] **AC-4:** Given an animated GIF `images/flag/banner.gif` with 4 frames,
      When rendered in the Playing Screen, Then the animation cycles through
      all 4 frames at the GIF's native frame rate.
- [ ] **AC-5:** Given an image path in `army.json` containing `../` (path
      traversal attempt), When `SpriteManager.preload_army()`,
      Then `PathTraversalError` is raised and loading aborts.
- [ ] **AC-6:** Given a corrupt image file, When loaded,
      Then the file is skipped with an error logged and the next valid image
      (or Classic fallback) is used.

### Example

```
Session start:
  Marshal images pool: [dragon_lord_1.png, dragon_lord_2.png, dragon_lord_3.png]
  Random selection: dragon_lord_2.png
  → All Marshals use dragon_lord_2.png for this entire session
```

### Definition of Done

- [ ] `src/presentation/sprite_manager.py` implements `preload_army(army_mod)`,
      `get_surface(rank, frame=0)`, and `advance_animation(delta_time)`.
- [ ] Path traversal check in `preload_army()`.
- [ ] GIF frame extraction at load time; `current_frame` advanced by
      `advance_animation()` using `delta_time`.
- [ ] `tests/unit/presentation/test_sprite_manager.py` covers fallback logic
      and path traversal rejection.

### Out of Scope

- Board skin mods (v2.0).
- Sound packs (v2.0).

---

## US-705: Army Select Screen

**Epic:** EPIC-7  
**Priority:** Should Have  
**Specification refs:** [`screen_flow.md §3.3`](../specifications/screen_flow.md),
[`custom_armies.md §8`](../specifications/custom_armies.md)

**As a** player,  
**I want** to choose a custom army from a dropdown before the game starts,
with a preview panel showing the army name and sample piece images,  
**so that** I can pick my preferred visual style before each game.

### Acceptance Criteria

- [ ] **AC-1:** Given 3 mods are loaded plus the Classic army, When
      `ArmySelectScreen` opens, Then the Player 1 dropdown contains exactly
      4 entries with "Classic" first.
- [ ] **AC-2:** Given the player selects "Dragon Horde" from the dropdown,
      When the preview panel updates, Then `army_name = "Dragon Horde"` and
      all custom unit names (e.g., "Dragon Lord" for Marshal) are visible.
- [ ] **AC-3:** Given 2-player mode, When `ArmySelectScreen` opens,
      Then both Player 1 and Player 2 dropdowns are visible.
- [ ] **AC-4:** Given vs-AI mode, When `ArmySelectScreen` opens,
      Then only the Player 1 dropdown is visible; AI army is selected
      automatically.
- [ ] **AC-5:** Given clicking **Confirm**, When `on_exit()` is called,
      Then the dict includes `player1_army`, `player2_army`, `game_mode`,
      `ai_difficulty`.

### Definition of Done

- [ ] `src/presentation/screens/army_select_screen.py` implements all controls.
- [ ] Screen transition data matches `screen_flow.md §5`.

### Out of Scope

- Mod installation from in-game (v2.0 marketplace).

---

## US-706: Integration Test Suite

**Epic:** EPIC-7  
**Priority:** Must Have  
**Specification refs:** All specification documents

**As a** developer,  
**I want** integration tests that exercise complete game flows end-to-end,  
**so that** all layers work together correctly and regressions are caught
before release.

### Acceptance Criteria

- [ ] **AC-1 (Full game):** Given a scripted game session (both players use
      pre-defined move sequences), When the session completes, Then the
      winner is the expected player and `phase == GAME_OVER`.
- [ ] **AC-2 (Save/load cycle):** Given a game saved at turn 20, When loaded
      and play continues to turn 25, Then the game state at turn 25 is
      identical to a game that ran continuously to turn 25 with the same moves.
- [ ] **AC-3 (AI game):** Given a full AI-vs-AI game (Easy vs Easy),
      When run headlessly, Then the game terminates within 5 minutes
      (either a winner or draw at 3000 half-moves).
- [ ] **AC-4 (Mod loading):** Given a test mod in `tests/fixtures/test_mod/`,
      When `discover_mods()` is called, Then the mod loads and its custom
      names appear in the army select data.
- [ ] **AC-5 (Coverage):** Given `uv run pytest --cov=src tests/`, When the
      full suite runs, Then `src/domain/` coverage is ≥ 80 %.

### Definition of Done

- [ ] `tests/integration/test_full_game_session.py` implements AC-1 and AC-3.
- [ ] `tests/integration/test_save_load_cycle.py` implements AC-2.
- [ ] `tests/fixtures/test_mod/` contains a minimal valid mod for AC-4.
- [ ] All integration tests run without a display (headless via `TerminalRenderer`
      or mocked pygame).

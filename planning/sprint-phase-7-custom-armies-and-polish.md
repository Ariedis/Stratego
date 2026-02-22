# Sprint Plan – Phase 7: Custom Armies & Polish

**Phase:** 7  
**Duration:** 2 weeks (Sprints 16–17)  
**Exit criteria:** Custom army mod loads and renders correctly; full integration test suite green; domain coverage ≥ 80 %  
**Epic:** EPIC-7  
**Specification refs:** [`custom_armies.md`](../specifications/custom_armies.md),
[`screen_flow.md §3.3`](../specifications/screen_flow.md)

---

## Sprint 16 (Week 16): Mod System

**Goal:** Classic army defined; mod loader and validator operational; sprite manager mod-aware.

### Tasks

---

#### TASK-701: Implement Classic Army

**User story:** US-701  
**Module:** `src/domain/classic_army.py`  
**Depends on:** TASK-103

**Input:** `custom_armies.md §8`  
**Output:** Hard-coded `ClassicArmy` singleton

**Steps:**

1. Create `src/domain/classic_army.py`.
2. Define `UnitCustomisation(rank: Rank, display_name: str, display_name_plural: str, image_paths: list[Path])`.
3. Define `ArmyMod(mod_id: str, army_name: str, author: str | None, description: str | None, unit_customisations: dict[Rank, UnitCustomisation], mod_directory: Path)`.
4. Implement `ClassicArmy` with:
   - `mod_id = "classic"`
   - `army_name = "Classic"`
   - All 12 ranks mapped to their official Stratego names:
     ```
     MARSHAL → "Marshal", GENERAL → "General", COLONEL → "Colonel",
     MAJOR → "Major", CAPTAIN → "Captain", LIEUTENANT → "Lieutenant",
     SERGEANT → "Sergeant", MINER → "Miner", SCOUT → "Scout",
     SPY → "Spy", BOMB → "Bomb", FLAG → "Flag"
     ```
   - `image_paths` points to `assets/pieces/<rank_lower>/` folder.
5. Expose `ClassicArmy.get() -> ArmyMod` class method returning the singleton.
6. Write `tests/unit/domain/test_classic_army.py`.

**Test cases to cover:**

- All 12 rank display names correct.
- `mod_id == "classic"`.
- `ArmyMod` is immutable (frozen dataclass).

---

#### TASK-702: Implement Mod Validator

**User story:** US-703  
**Module:** `src/infrastructure/mod_validator.py`  
**Depends on:** TASK-701

**Input:** `custom_armies.md §4.3`  
**Output:** `validate_manifest(data: dict) -> list[ValidationError]`

**Steps:**

1. Create `src/infrastructure/mod_validator.py`.
2. Define `ValidationError(field: str, message: str)` dataclass.
3. Implement `validate_manifest(data: dict) -> list[ValidationError]`:
   - Check `mod_version == "1.0"`: if not, append `ValidationError`.
   - Check `army_name` length 1–64: if not, append `ValidationError`.
   - For each rank key in `units`:
     - If key is not a valid `Rank` name: log warning (do not reject).
     - Check `display_name` length 1–32: if not, append `ValidationError` for
       that rank field but continue validating others.
   - Check JSON parse success (caller catches `json.JSONDecodeError`).
4. Return accumulated list of `ValidationError`; empty list = valid.
5. Write `tests/unit/infrastructure/test_mod_validator.py`.

**Test cases to cover:**

- `mod_version = "2.0"` → error.
- `army_name = ""` → error.
- `army_name` 65 chars → error.
- `display_name` 33 chars → error.
- Unknown rank key → warning only (no error).
- Valid manifest → empty error list.

---

#### TASK-703: Implement Mod Loader

**User story:** US-702  
**Module:** `src/infrastructure/mod_loader.py`  
**Depends on:** TASK-701, TASK-702

**Input:** `custom_armies.md §3, §6`  
**Output:** `discover_mods(mod_dir: Path) -> list[ArmyMod]`

**Steps:**

1. Create `src/infrastructure/mod_loader.py`.
2. Implement `discover_mods(mod_dir: Path) -> list[ArmyMod]`:
   - If `mod_dir` does not exist: return `[]`.
   - List all subdirectories in `mod_dir`.
   - For each subdirectory:
     a. Look for `army.json`; if missing: log warning, skip.
     b. Read and parse `army.json`; if `JSONDecodeError`: log warning, skip.
     c. Call `validate_manifest(raw_data)`; if errors: log warning, skip.
     d. Build `ArmyMod` from validated data.
     e. If `mod_id` already seen: log warning, skip (duplicate).
   - Prepend `ClassicArmy.get()` to the result list (always first).
3. Implement `_build_army_mod(mod_id, data, mod_dir) -> ArmyMod`:
   - Map `units` dict entries to `UnitCustomisation` objects.
   - Fall back to Classic name for missing ranks.
4. Write `tests/unit/infrastructure/test_mod_loader.py` using `tmp_path`
   pytest fixture for temporary directories.

**Example:**

```python
# Valid mod + invalid mod
mods = discover_mods(Path("/tmp/test_mods"))
assert len(mods) == 2           # Classic + 1 valid mod
assert mods[0].mod_id == "classic"
```

**Test cases to cover:**

- Valid mod discovered and parsed.
- Malformed `army.json` skipped with warning.
- Duplicate mod ID: second skipped.
- Empty directory returns `[ClassicArmy]`.
- Missing `army.json` skipped.

---

#### TASK-704: Extend Sprite Manager for Mod Support and GIF Animation

**User story:** US-704  
**Module:** `src/presentation/sprite_manager.py`  
**Depends on:** TASK-402, TASK-703

**Input:** `custom_armies.md §5`  
**Output:** `preload_army(army_mod)` with fallback and GIF support

**Steps:**

1. Extend `SpriteManager.preload_army(army_mod: ArmyMod) -> None`:
   - For each rank:
     a. List image files in `army_mod.mod_directory / "images" / rank_lower /`.
     b. Validate each path: reject any path containing `..` or that resolves
        outside the mod directory (`PathTraversalError`).
     c. Load valid images; for GIF files, extract all frames using
        `pygame.image.load()` in a loop over frames.
     d. If no mod images found for this rank: fall back to Classic asset.
     e. Randomly select one image (or frame list for GIFs) per rank.
     f. Cache in `self._surfaces[rank]` (list of frames; length ≥ 1).
2. Implement `advance_animation(delta_time: float) -> None`:
   - For each animated rank (frame count > 1), advance frame index based on
     `delta_time` and the GIF frame duration (default 100 ms per frame).
3. Update `get_surface(rank, owner, revealed) -> pygame.Surface`:
   - Returns `self._surfaces[rank][self._current_frame[rank]]`.
4. Write `tests/unit/presentation/test_sprite_manager.py` with updated tests.

**Test cases to cover:**

- Path traversal `../` raises `PathTraversalError`.
- Missing mod images fall back to Classic.
- Corrupt image file skipped, fallback used.
- `advance_animation()` increments frame index correctly.

---

## Sprint 17 (Week 17): Army Select Screen and Integration Tests

**Goal:** Full screen flow with army selection; complete integration test suite.

### Tasks

---

#### TASK-705: Implement Army Select Screen

**User story:** US-705  
**Module:** `src/presentation/screens/army_select_screen.py`  
**Depends on:** TASK-703, TASK-306

**Steps:**

1. Implement `ArmySelectScreen(Screen)`.
2. `on_enter(data)`: Receive `{game_mode, ai_difficulty}`;
   load army list from `ModLoader.discover_mods()`.
3. Render Player 1 army dropdown (always shown).
4. If `game_mode == TWO_PLAYER`: render Player 2 army dropdown.
5. Preview panel: show `army.army_name`, list of unit custom names,
   and a sample piece image using `SpriteManager`.
6. Confirm button: call `on_exit()` returning
   `{player1_army, player2_army, game_mode, ai_difficulty}`.
7. Back button: `screen_manager.pop()`.

---

#### TASK-706: Write integration test suite

**User story:** US-706  
**Module:** `tests/integration/`  
**Depends on:** All previous tasks

**Steps:**

1. Create `tests/integration/test_full_game_session.py`:
   - Script a complete game between two human players using pre-defined move
     sequences (scripted via `GameController.submit_command()`).
   - Assert `game_state.phase == GAME_OVER` at the end.
   - Assert `game_state.winner` is the expected player.
2. Create `tests/integration/test_save_load_cycle.py`:
   - Play 20 moves; save game; load game; play 5 more moves.
   - Assert state after 25 moves equals state from a continuous 25-move game
     with identical moves.
3. Create `tests/integration/test_ai_game.py`:
   - Run AI_EASY vs AI_EASY headlessly using `TerminalRenderer`.
   - Assert game terminates within 3 000 half-moves.
   - Assert the terminating state is `GAME_OVER` with a valid winner or draw.
4. Create `tests/fixtures/test_mod/` with:
   - A minimal valid `army.json` for use in mod loading tests.
5. Run `uv run pytest --cov=src tests/` and verify:
   - All tests pass.
   - `src/domain/` coverage ≥ 80 %.

**Test cases to cover:**

- Full game session terminates correctly.
- Save/load round-trip preserves game continuity.
- AI game terminates within bounds.
- Mod loading integration with `discover_mods()`.

---

## Phase 7 Definition of Done

- [ ] All 7 epics' Must Have features implemented.
- [ ] `uv run pytest` reports 0 failures.
- [ ] `src/domain/` coverage ≥ 80 % (reported by `pytest-cov`).
- [ ] `uv run mypy --strict src/` reports 0 errors.
- [ ] `uv run ruff check src/ tests/` reports 0 violations.
- [ ] `ruff` rule `S301` (no pickle) reports 0 violations.
- [ ] No cross-layer imports (domain → pygame, domain → infrastructure, etc.).
- [ ] Custom army mod can be installed by copying a folder to the mod directory
      with no code changes required.
- [ ] Hard AI (depth-6) completes a move in < 950 ms in an integration test.
- [ ] Full game session (human vs AI, Hard difficulty) plays to a conclusion
      without error.

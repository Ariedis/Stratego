# EPIC-6: Infrastructure – User Stories

**Epic:** EPIC-6  
**Phase:** 6  
**Specification refs:** [`system_design.md §2.5, §8`](../specifications/system_design.md),
[`data_models.md §6`](../specifications/data_models.md),
[`technology_stack.md §7, §8`](../specifications/technology_stack.md)

---

## US-601: JSON Save/Load

**Epic:** EPIC-6  
**Priority:** Must Have  
**Specification refs:** [`data_models.md §6`](../specifications/data_models.md),
[`technology_stack.md §7`](../specifications/technology_stack.md)

**As a** player,  
**I want** to save my current game to disk and reload it in a future session,  
**so that** I can pause a game and resume it later without losing any progress.

### Acceptance Criteria

- [ ] **AC-1:** Given a `GameState` at turn 50 with a complex board,
      When `json_repository.save(state, "game_001.json")`, Then a valid
      JSON file is created at `~/.stratego/saves/game_001.json` containing
      the `"version": "1.0"` field.
- [ ] **AC-2:** Given a saved JSON file, When `json_repository.load("game_001.json")`,
      Then the returned `GameState` is equal to the original state (full
      round-trip: all pieces, positions, turn number, move history preserved).
- [ ] **AC-3:** Given a JSON file with `"version": "2.0"` (unknown version),
      When `load()` is called, Then `UnsupportedSaveVersionError` is raised
      with a message including the version string.
- [ ] **AC-4:** Given a corrupt JSON file (invalid syntax), When `load()` is
      called, Then `SaveFileCorruptError` is raised and the error is logged
      with full stack trace.
- [ ] **AC-5:** Given `json_repository.get_most_recent_save()` with 3 save
      files, When called, Then the path of the most recently written file is
      returned.
- [ ] **AC-6:** Given `get_most_recent_save()` with no save files,
      When called, Then `None` is returned.
- [ ] **AC-7:** `pickle` is never imported or used; `ruff` rule `S301`
      reports zero violations.

### Example

Save file naming pattern: `stratego_YYYYMMDD_HHMMSS_turn{N}.json`
e.g., `stratego_20260115_143022_turn50.json`

```json
{
  "version": "1.0",
  "phase": "PLAYING",
  "active_player": "RED",
  "turn_number": 50,
  "board": { "squares": [ ... ] },
  "move_history": [ ... ],
  "winner": null
}
```

### Definition of Done

- [ ] `src/infrastructure/json_repository.py` implements `save`, `load`,
      `get_most_recent_save`, `list_saves`, `delete_save`.
- [ ] Custom `JSONEncoder` and `JSONDecoder` handle all domain types
      (Rank, PlayerSide, GamePhase enums; Position, Piece dataclasses).
- [ ] `tests/unit/infrastructure/test_json_repository.py` covers all 7 AC
      scenarios including round-trip equality.
- [ ] `tests/fixtures/sample_save_files/turn_50.json` exists as a fixture.
- [ ] `ruff check src/` with `S301` enabled reports zero violations.

### Out of Scope

- Autosave scheduling (should be triggered by Turn Manager in Application Layer).
- Save file migration logic (v2.0 when schema changes).
- Cloud sync or remote persistence.

---

## US-602: Configuration Loader

**Epic:** EPIC-6  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §8`](../specifications/system_design.md)

**As a** developer,  
**I want** the application to load settings from `config.yaml` at startup and
fall back to hardcoded defaults when the file is absent or a key is missing,  
**so that** the application always starts successfully even on a fresh
installation and settings can be customised without code changes.

### Acceptance Criteria

- [ ] **AC-1:** Given no `config.yaml` exists, When `Config.load()`,
      Then the returned config object has `display.fps_cap=60`,
      `ai.default_difficulty="medium"`, `ai.time_limit_ms=950`.
- [ ] **AC-2:** Given a `config.yaml` with `display.fps_cap: 144`,
      When `Config.load()`, Then `config.display.fps_cap == 144`.
- [ ] **AC-3:** Given a `config.yaml` missing the `ai` section,
      When `Config.load()`, Then the `ai` section defaults are applied
      without error.
- [ ] **AC-4:** Given an invalid `config.yaml` (YAML parse error),
      When `Config.load()`, Then `ConfigLoadError` is raised with a
      descriptive message.
- [ ] **AC-5:** Given `Config.save(config, path)`, When the file is
      subsequently loaded, Then `loaded_config == config`.

### Example

```python
config = Config.load(Path("~/.stratego/config.yaml"))
assert config.ai.search_depth.hard == 6
assert config.persistence.save_directory == Path("~/.stratego/saves")
```

### Definition of Done

- [ ] `src/infrastructure/config.py` implements `Config.load()` and `Config.save()`.
- [ ] Config schema matches all keys defined in `system_design.md §8`.
- [ ] `tests/unit/infrastructure/test_config.py` covers missing file,
      missing keys, and round-trip.

### Out of Scope

- GUI settings screen (US-411, EPIC-4).

---

## US-603: Structured Logger

**Epic:** EPIC-6  
**Priority:** Should Have  
**Specification refs:** [`system_design.md §2.5`](../specifications/system_design.md)

**As a** developer,  
**I want** a structured logger that writes to both a rotating log file and
the console, with configurable log levels,  
**so that** debugging production issues is possible by inspecting the log file
without having to reproduce problems interactively.

### Acceptance Criteria

- [ ] **AC-1:** Given `logger.error("Invalid move", exc_info=True)`,
      When the log file is read, Then the entry includes the timestamp,
      level, message, and full stack trace.
- [ ] **AC-2:** Given `config.logging.level = "WARNING"`, When `logger.info()`,
      Then no entry is written (level filtering respected).
- [ ] **AC-3:** Given the log file reaches 5 MB, When the next log entry is
      written, Then the file rotates and the old log is renamed with a suffix.
- [ ] **AC-4:** Given the log directory `~/.stratego/` does not exist,
      When the logger initialises, Then the directory is created automatically.

### Example

```
2026-01-15 14:30:22 INFO  [game_controller] Move applied: RED Scout (6,4)→(5,4) [turn=1]
2026-01-15 14:30:25 ERROR [rules_engine] Invalid move attempted: RED piece at (4,2) (lake)
```

### Definition of Done

- [ ] `src/infrastructure/logger.py` wraps `logging.getLogger` with a
      `RotatingFileHandler` and a `StreamHandler`.
- [ ] Log format includes ISO timestamp, level, module name, and message.
- [ ] `tests/unit/infrastructure/test_logger.py` verifies log output using
      `caplog` pytest fixture.

### Out of Scope

- Remote log aggregation (v2.0).
- Structured JSON log format (Could Have).

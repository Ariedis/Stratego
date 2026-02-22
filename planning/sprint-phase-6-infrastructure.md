# Sprint Plan – Phase 6: Infrastructure

**Phase:** 6  
**Duration:** 2 weeks (Sprints 14–15)  
**Exit criteria:** Save/load round-trip works; settings persist; structured logging active  
**Epic:** EPIC-6  
**Specification refs:** [`system_design.md §2.5, §8`](../specifications/system_design.md),
[`data_models.md §6`](../specifications/data_models.md),
[`technology_stack.md §7`](../specifications/technology_stack.md)

---

## Sprint 14 (Week 14): JSON Persistence

**Goal:** Full save/load round-trip for `GameState` with version validation.

### Tasks

---

#### TASK-601: Implement JSON encoder/decoder for domain types

**User story:** US-601  
**Module:** `src/infrastructure/json_repository.py`  
**Depends on:** TASK-104

**Input:** `data_models.md §6`  
**Output:** Custom `StrategoJSONEncoder` and `StrategoJSONDecoder`

**Steps:**

1. Create `src/infrastructure/json_repository.py`.
2. Implement `StrategoJSONEncoder(json.JSONEncoder)`:
   - Serialise `Rank` → `rank.name` (string).
   - Serialise `PlayerSide` → `side.name`.
   - Serialise `GamePhase` → `phase.name`.
   - Serialise `Position` → `[row, col]` (compact array).
   - Serialise `Piece` → `{"rank": ..., "owner": ..., "revealed": bool, "has_moved": bool}`.
   - Serialise `Board` → `{"squares": [...]}` per `data_models.md §6`.
   - Serialise `GameState` → full schema from `data_models.md §6` with
     `"version": "1.0"` field.
3. Implement `StrategoJSONDecoder` (or `object_hook`):
   - Detect `"version"` field: if not `"1.0"`, raise `UnsupportedSaveVersionError`.
   - Reconstruct `Position`, `Piece`, `Board`, `Player`, `MoveRecord`,
     `GameState` from dict keys.
4. Implement `json_repository.save(state: GameState, filepath: Path) -> None`:
   - Ensure save directory exists (`~/.stratego/saves/`).
   - Write JSON using `StrategoJSONEncoder` with `indent=2`.
5. Implement `json_repository.load(filepath: Path) -> GameState`:
   - Read file; parse with decoder.
   - Catch `json.JSONDecodeError` → raise `SaveFileCorruptError`.
6. Write `tests/unit/infrastructure/test_json_repository.py`.

**Example:**

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

**Test cases to cover:**

- Round-trip: `save(state)` then `load()` produces equal `GameState`.
- Version `"2.0"` raises `UnsupportedSaveVersionError`.
- Corrupt JSON raises `SaveFileCorruptError`.
- `pickle` is not imported (check with `grep`).

---

#### TASK-602: Implement save file management

**User story:** US-601  
**Module:** `src/infrastructure/json_repository.py`  
**Depends on:** TASK-601

**Input:** Save directory on disk  
**Output:** `list_saves()`, `get_most_recent_save()`, `delete_save()`

**Steps:**

1. Define save file naming pattern: `stratego_{YYYYMMDD}_{HHMMSS}_turn{N}.json`
   e.g., `stratego_20260115_143022_turn050.json`.
2. Implement `list_saves(save_dir: Path) -> list[Path]`:
   - Returns all `.json` files in `save_dir`, sorted newest-first by
     `mtime` (file modification time).
3. Implement `get_most_recent_save(save_dir: Path) -> Path | None`:
   - Returns the first result from `list_saves()` or `None` if empty.
4. Implement `delete_save(filepath: Path) -> None`:
   - Delete file; log `INFO` message.
5. Wire autosave into `TurnManager`: every N turns (from config), call
   `json_repository.save(state, autosave_path)`.
6. Write tests for all new methods.

**Test cases to cover:**

- `list_saves()` sorted newest-first.
- `get_most_recent_save()` returns `None` for empty directory.
- `delete_save()` removes the file.

---

## Sprint 15 (Week 15): Configuration and Logging

**Goal:** Config loader and structured logger operational.

### Tasks

---

#### TASK-603: Implement configuration loader

**User story:** US-602  
**Module:** `src/infrastructure/config.py`  
**Depends on:** TASK-101

**Input:** `system_design.md §8`  
**Output:** `Config` class loaded from `config.yaml`

**Steps:**

1. Create `src/infrastructure/config.py`.
2. Define nested `dataclass` hierarchy for config:
   - `DisplayConfig(width, height, fullscreen, fps_cap)`.
   - `AIConfig(default_difficulty, search_depth: SearchDepthConfig, time_limit_ms)`.
   - `SearchDepthConfig(easy, medium, hard)`.
   - `PersistenceConfig(save_directory, autosave, autosave_interval_turns)`.
   - `LoggingConfig(level, file)`.
   - `Config(display, ai, persistence, logging)`.
3. Implement `Config.load(path: Path | None = None) -> Config`:
   - If `path` is `None`, look for `~/.stratego/config.yaml`.
   - If file not found: return `Config` with all defaults.
   - Parse YAML using `yaml.safe_load()`.
   - Merge parsed values with defaults (missing keys get default values).
   - Catch `yaml.YAMLError` → raise `ConfigLoadError`.
4. Implement `Config.save(config: Config, path: Path) -> None`.
5. Define all default values matching `system_design.md §8`.
6. Add `PyYAML>=6.0` to `pyproject.toml` dependencies.
7. Write `tests/unit/infrastructure/test_config.py`.

**Example:**

```python
config = Config.load(None)  # no file present
assert config.display.fps_cap == 60
assert config.ai.time_limit_ms == 950
assert config.ai.search_depth.hard == 6
```

**Test cases to cover:**

- Missing file uses defaults.
- Partial YAML (missing `ai` section) merges with defaults.
- Invalid YAML raises `ConfigLoadError`.
- Round-trip: `save` then `load` produces equal config.

---

#### TASK-604: Implement structured logger

**User story:** US-603  
**Module:** `src/infrastructure/logger.py`  
**Depends on:** TASK-603

**Input:** `system_design.md §2.5`  
**Output:** `get_logger(name)` returning a configured Python logger

**Steps:**

1. Create `src/infrastructure/logger.py`.
2. Implement `configure_logging(config: LoggingConfig) -> None`:
   - Create `~/.stratego/` directory if not present.
   - Add `RotatingFileHandler(config.file, maxBytes=5_000_000, backupCount=3)`.
   - Add `StreamHandler(sys.stdout)` for console output.
   - Set format: `"%(asctime)s %(levelname)-8s [%(name)s] %(message)s"`.
   - Set root logger level from `config.level`.
3. Implement `get_logger(name: str) -> logging.Logger`:
   - Returns `logging.getLogger(name)`.
4. Call `configure_logging()` in the application entry point before the
   game loop starts.
5. Write `tests/unit/infrastructure/test_logger.py` using `pytest`'s
   `caplog` fixture.

**Test cases to cover:**

- `WARNING` level suppresses `INFO` messages.
- Error log includes full stack trace when `exc_info=True`.
- Log directory auto-created when missing.
- File rotation: verify `RotatingFileHandler` is added (not checking 5 MB limit
  in tests – just that it is configured).

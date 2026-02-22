# Sprint Plan – Phase 1: Project Foundation

**Phase:** 1  
**Duration:** 2 weeks (Sprints 1–2)  
**Exit criteria:** `uv run pytest` passes; all enum/dataclass models importable with zero mypy errors  
**Epic:** EPIC-1  
**Specification refs:** [`architecture_overview.md §7`](../specifications/architecture_overview.md),
[`data_models.md §3`](../specifications/data_models.md),
[`technology_stack.md`](../specifications/technology_stack.md)

---

## Sprint 1 (Week 1): Project Scaffolding and Toolchain

**Goal:** Running project skeleton with configured toolchain.

### Tasks

---

#### TASK-101: Create project skeleton with uv

**User story:** US-101  
**Module:** `pyproject.toml`, `src/`, `tests/`  
**Depends on:** Nothing

**Input:** Empty repository  
**Output:** Runnable `uv` project with all package stubs

**Steps:**

1. Run `uv init --package stratego` in the repository root to generate
   `pyproject.toml` and `src/stratego/`.
2. Update `pyproject.toml`:
   - Set `requires-python = ">=3.12"`.
   - Add production dependencies: `pygame-ce>=2.4`, `pygame-gui>=0.6`.
   - Add dev dependencies: `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-mock>=3.12`,
     `mypy>=1.10`, `ruff>=0.4`.
3. Create the five `src/` subdirectories with empty `__init__.py`:
   `src/domain/`, `src/application/`, `src/ai/`, `src/presentation/`,
   `src/infrastructure/`.
4. Rename `src/stratego/` to `src/` (flat `src` layout) and update
   `pyproject.toml` `packages` accordingly.
5. Create test directories: `tests/unit/domain/`, `tests/unit/application/`,
   `tests/unit/ai/`, `tests/unit/infrastructure/`, `tests/unit/presentation/`,
   `tests/integration/`, `tests/fixtures/`. Add `__init__.py` to each.
6. Run `uv sync` to verify all dependencies install.

**Example:**

> `uv run python -c "from src.domain import __version__"` exits 0.

**Test cases to cover:**

- `uv run pytest` exits 0 with "no tests ran".
- `uv run ruff check src/` exits 0.
- `uv run mypy --strict src/` exits 0.

---

#### TASK-102: Configure ruff, mypy, and pytest

**User story:** US-104  
**Module:** `pyproject.toml`  
**Depends on:** TASK-101

**Input:** `pyproject.toml` with dependencies  
**Output:** All tools configured in `pyproject.toml`

**Steps:**

1. Add `[tool.pytest.ini_options]` section:
   - `testpaths = ["tests"]`
   - `addopts = "--strict-markers"`
2. Add `[tool.mypy]` section: `strict = true`, `python_version = "3.12"`.
3. Add `[tool.ruff]` section:
   - `line-length = 100`
   - `select = ["E", "F", "S", "I"]`
   - `"S301"` included in select (ban pickle).
4. Add `[tool.coverage.run]` section: `source = ["src"]`.
5. Verify `uv run ruff check src/` and `uv run mypy --strict src/` exit 0.

**Test cases to cover:**

- `ruff` rule `S301` is active (confirmed by checking the config).

---

## Sprint 2 (Week 2): Domain Enumerations and Value Objects

**Goal:** All domain models defined, importable, and tested.

### Tasks

---

#### TASK-103: Implement domain enumerations

**User story:** US-102  
**Module:** `src/domain/enums.py`  
**Depends on:** TASK-101

**Input:** `data_models.md §3`  
**Output:** All 7 enumerations in `src/domain/enums.py`

**Steps:**

1. Create `src/domain/enums.py`.
2. Define `Rank(IntEnum)` with members:
   `FLAG=0, SPY=1, SCOUT=2, MINER=3, SERGEANT=4, LIEUTENANT=5,
   CAPTAIN=6, MAJOR=7, COLONEL=8, GENERAL=9, MARSHAL=10, BOMB=99`.
3. Define `PlayerSide(Enum)`: `RED, BLUE`.
4. Define `PlayerType(Enum)`: `HUMAN, AI_EASY, AI_MEDIUM, AI_HARD, NETWORK`.
5. Define `GamePhase(Enum)`: `MAIN_MENU, SETUP, PLAYING, GAME_OVER`.
6. Define `TerrainType(Enum)`: `NORMAL, LAKE`.
7. Define `MoveType(Enum)`: `MOVE, ATTACK`.
8. Define `CombatOutcome(Enum)`: `ATTACKER_WINS, DEFENDER_WINS, DRAW`.
9. Write `tests/unit/domain/test_enums.py` verifying all integer values
   and member counts.

**Example:**

```python
assert Rank.BOMB.value == 99   # not 11
assert len(list(Rank)) == 12
```

**Test cases to cover:**

- All 12 `Rank` members with correct integer values.
- `BOMB.value == 99`.
- `MARSHAL.value > GENERAL.value`.
- All other enum member counts correct.

---

#### TASK-104: Implement core value-object dataclasses

**User story:** US-103  
**Module:** `src/domain/position.py`, `src/domain/square.py`, `src/domain/board.py`,
`src/domain/piece.py`, `src/domain/player.py`, `src/domain/move.py`,
`src/domain/move_record.py`, `src/domain/combat_result.py`, `src/domain/game_state.py`  
**Depends on:** TASK-103

**Input:** `data_models.md §2–§4`  
**Output:** All 9 dataclasses defined as `frozen=True`

**Steps:**

1. `position.py`: `@dataclass(frozen=True) class Position` with `row: int`,
   `col: int`, `is_valid() -> bool` (`0 ≤ row ≤ 9 and 0 ≤ col ≤ 9`).
2. `square.py`: `Square(position, piece: Piece | None, terrain: TerrainType)`.
3. `piece.py`: `Piece(rank, owner, revealed: bool, has_moved: bool, position)`.
4. `board.py`: `Board(squares: dict[Position, Square])` with class method
   `create_empty() -> Board` that pre-populates all 100 squares including
   the 8 lake squares. Add `is_lake(pos)`, `get_square(pos)`,
   `neighbours(pos)`, `is_empty(pos)`, `is_in_setup_zone(pos, side)`.
   Lake positions hard-coded as a `frozenset` constant.
5. `player.py`: `Player(side, player_type, pieces_remaining, flag_position)`.
6. `move.py`: `Move(piece, from_pos, to_pos, move_type)`.
7. `move_record.py`: `MoveRecord(move, combat_result: CombatResult | None, turn_number, timestamp)`.
8. `combat_result.py`: `CombatResult(attacker, defender, outcome, attacker_survived, defender_survived)`.
9. `game_state.py`: `GameState(board, players, active_player, phase, turn_number, move_history, winner)`.
10. Write `tests/unit/domain/test_models.py` verifying all 10 invariants from
    `data_models.md §4`.

**Example:**

```python
pos = Position(row=10, col=0)
assert pos.is_valid() is False  # row must be 0–9
```

**Test cases to cover:**

- `Position.is_valid()` boundary conditions (0,0), (9,9), (-1,0), (10,0).
- `Board.create_empty()` has exactly 8 lake squares.
- `Piece` is immutable (`FrozenInstanceError` on mutation).
- All 10 invariants from `data_models.md §4` (I-1 through I-10).

---

#### TASK-105: Create test fixtures

**User story:** US-104  
**Module:** `tests/fixtures/sample_game_states.py`  
**Depends on:** TASK-104

**Input:** Dataclasses from TASK-104  
**Output:** Factory functions for reusable test game states

**Steps:**

1. Create `tests/fixtures/__init__.py`.
2. Create `tests/fixtures/sample_game_states.py` with:
   - `make_empty_board() -> Board`
   - `make_initial_game_state() -> GameState` (Setup phase, no pieces placed)
   - `make_playing_state() -> GameState` (Playing phase, standard mid-game
     position with at least 10 pieces per side for use in rules tests)
3. Export all factory functions from `tests/fixtures/__init__.py`.

**Test cases to cover:**

- Each factory function returns a valid `GameState` that passes invariant checks.

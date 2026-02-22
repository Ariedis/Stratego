# EPIC-1: Project Foundation – User Stories

**Epic:** EPIC-1  
**Phase:** 1  
**Specification refs:** [`architecture_overview.md §7`](../specifications/architecture_overview.md),
[`data_models.md`](../specifications/data_models.md),
[`technology_stack.md`](../specifications/technology_stack.md)

---

## US-101: Project Scaffolding

**Epic:** EPIC-1  
**Priority:** Must Have  
**Specification refs:** [`architecture_overview.md §7`](../specifications/architecture_overview.md),
[`technology_stack.md §8`](../specifications/technology_stack.md)

**As a** developer,  
**I want** a correctly structured Python project with `uv`, `pyproject.toml`,
and the five-layer folder hierarchy (`domain/`, `application/`, `ai/`,
`presentation/`, `infrastructure/`) created under `src/`,  
**so that** all subsequent development tasks can be started without any
scaffolding overhead and tools are configured from day one.

### Acceptance Criteria

- [ ] **AC-1:** Given an empty repository, When `uv sync` is run, Then all
      declared dependencies install without error.
- [ ] **AC-2:** Given the installed project, When `uv run python -c "import src"`,
      Then the command exits with code 0.
- [ ] **AC-3:** Given the project root, When `uv run ruff check src/`, Then zero
      linting violations are reported on the skeleton files.
- [ ] **AC-4:** Given the project root, When `uv run mypy --strict src/`, Then
      zero type errors are reported on the skeleton files.
- [ ] **AC-5:** Given the project root, When `uv run pytest`, Then the test runner
      discovers tests and reports 0 failures (empty test suite passes).

### Example

> Running `uv run pytest --co -q` prints `no tests ran` rather than an error.

### Definition of Done

- [ ] `pyproject.toml` declares Python `>=3.12`, all required prod and dev
      dependencies from `technology_stack.md §10`.
- [ ] `src/domain/`, `src/application/`, `src/ai/`, `src/presentation/`,
      `src/infrastructure/` all exist with `__init__.py` files.
- [ ] `tests/unit/`, `tests/integration/`, `tests/fixtures/` exist.
- [ ] `ruff` and `mypy` configurations are in `pyproject.toml`.
- [ ] A root `README.md` documents how to install and run.

### Out of Scope

- Implementation of any game logic.
- Asset files (images, sounds).

---

## US-102: Domain Enumerations

**Epic:** EPIC-1  
**Priority:** Must Have  
**Specification refs:** [`data_models.md §3`](../specifications/data_models.md)

**As a** developer,  
**I want** all domain enumerations defined in `src/domain/enums.py` with the
exact integer values specified in `data_models.md §3`,  
**so that** all other domain modules can import a single, authoritative set of
type-safe constants without duplication.

### Acceptance Criteria

- [ ] **AC-1:** Given `from src.domain.enums import Rank`, When `Rank.FLAG.value`,
      Then the result is `0`.
- [ ] **AC-2:** Given `Rank`, When iterating all members, Then exactly 12 members
      exist: FLAG, SPY, SCOUT, MINER, SERGEANT, LIEUTENANT, CAPTAIN, MAJOR,
      COLONEL, GENERAL, MARSHAL, BOMB.
- [ ] **AC-3:** Given `Rank.BOMB.value`, When compared to `99`, Then they are
      equal (not 11).
- [ ] **AC-4:** Given `Rank.MARSHAL.value > Rank.GENERAL.value`, Then `True`.
- [ ] **AC-5:** Given `from src.domain.enums import GamePhase`, When
      `GamePhase.SETUP`, `GamePhase.PLAYING`, `GamePhase.GAME_OVER`,
      `GamePhase.MAIN_MENU`, Then all four members exist.
- [ ] **AC-6:** Given `mypy --strict src/domain/enums.py`, Then zero errors.

### Example

```python
from src.domain.enums import Rank, PlayerSide, CombatOutcome

assert Rank.BOMB.value == 99       # not 11
assert Rank.MARSHAL.value == 10
assert PlayerSide.RED != PlayerSide.BLUE
assert CombatOutcome.DRAW.name == "DRAW"
```

### Definition of Done

- [ ] `src/domain/enums.py` contains all 7 enumerations.
- [ ] Unit test `tests/unit/domain/test_enums.py` verifies all integer values
      and member counts.
- [ ] Zero `mypy` errors.

### Out of Scope

- Serialisation logic (covered in EPIC-6).
- Display names / labels (covered in EPIC-7).

---

## US-103: Core Value-Object Dataclasses

**Epic:** EPIC-1  
**Priority:** Must Have  
**Specification refs:** [`data_models.md §2–§5`](../specifications/data_models.md)

**As a** developer,  
**I want** all nine core domain dataclasses defined as `frozen=True` Python
`dataclass` objects in `src/domain/`,  
**so that** game state is immutable by construction, enabling safe AI search,
undo/redo, and easy serialisation.

### Acceptance Criteria

- [ ] **AC-1:** Given `Position(row=5, col=3)`, When `pos.is_valid()`, Then
      `True`; When `Position(row=-1, col=0).is_valid()`, Then `False`.
- [ ] **AC-2:** Given a `Piece(rank=Rank.SCOUT, owner=PlayerSide.RED, revealed=False, has_moved=False, position=Position(6,4))`,
      When attempting `piece.revealed = True`, Then `FrozenInstanceError`
      is raised (immutability enforced).
- [ ] **AC-3:** Given a `Board` with 100 squares, When `board.is_lake(Position(4,2))`,
      Then `True`; When `board.is_lake(Position(0,0))`, Then `False`.
- [ ] **AC-4:** Given a valid initial `GameState`, When accessing
      `game_state.phase`, Then `GamePhase.SETUP`.
- [ ] **AC-5:** Given `GameState`, When checking all 10 invariants from
      `data_models.md §4`, Then all pass.

### Example

```python
from src.domain.board import Board
from src.domain.piece import Piece
from src.domain.enums import Rank, PlayerSide

board = Board.create_empty()
assert board.is_lake(Position(4, 2)) is True
assert board.is_lake(Position(0, 0)) is False
assert len(board.squares) == 100
```

### Definition of Done

- [ ] `Position`, `Square`, `Board`, `Piece`, `Player`, `Move`, `MoveRecord`,
      `CombatResult`, `GameState` all defined in separate files under
      `src/domain/`.
- [ ] All dataclasses use `frozen=True`.
- [ ] `Board` pre-populates lake squares per `game_components.md §2.2`.
- [ ] `tests/unit/domain/test_models.py` verifies all invariants from
      `data_models.md §4`.
- [ ] `mypy --strict src/domain/` reports zero errors.

### Out of Scope

- Business logic (movement, combat) – covered in EPIC-2.
- Serialisation – covered in EPIC-6.

---

## US-104: Test Infrastructure

**Epic:** EPIC-1  
**Priority:** Must Have  
**Specification refs:** [`technology_stack.md §5–§6`](../specifications/technology_stack.md)

**As a** developer,  
**I want** pytest, pytest-cov, pytest-mock, mypy, and ruff configured and
runnable from a single `uv run pytest` command,  
**so that** every subsequent feature can be test-driven and code quality is
enforced continuously.

### Acceptance Criteria

- [ ] **AC-1:** Given `uv run pytest --cov=src tests/`, When the test suite
      runs, Then a coverage report is printed.
- [ ] **AC-2:** Given `uv run ruff check src/ tests/`, When run on clean code,
      Then exit code 0.
- [ ] **AC-3:** Given `uv run mypy --strict src/`, When run on clean code,
      Then exit code 0.
- [ ] **AC-4:** Given a test using `pytest.mark.parametrize`, When the
      parametrised test runs, Then all parameter variants execute.
- [ ] **AC-5:** `ruff` rule `S301` (ban pickle) is enabled in `pyproject.toml`.

### Example

> Running `uv run pytest -v` after Phase 1 completion should show all model
> tests passing and a coverage report showing ≥ 80 % for `src/domain/`.

### Definition of Done

- [ ] `[tool.pytest.ini_options]` section in `pyproject.toml` with `testpaths`,
      `addopts = "--strict-markers"`.
- [ ] `[tool.mypy]` section with `strict = true`.
- [ ] `[tool.ruff]` section with `select = ["E", "F", "S"]` and `S301` enabled.
- [ ] `tests/fixtures/sample_game_states.py` provides at least one factory
      function for creating test `GameState` objects.

### Out of Scope

- CI/CD pipeline configuration (out of scope for v1.0).
- Code coverage gates (recommended but not enforced in v1.0).

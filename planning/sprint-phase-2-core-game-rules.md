# Sprint Plan – Phase 2: Core Game Rules

**Phase:** 2  
**Duration:** 3 weeks (Sprints 3–5)  
**Exit criteria:** All combat, movement, and win-condition unit tests pass; `src/domain/` coverage ≥ 80 %  
**Epic:** EPIC-2  
**Specification refs:** [`game_components.md`](../specifications/game_components.md),
[`data_models.md §4`](../specifications/data_models.md)

---

## Sprint 3 (Week 3): Board Operations and Setup Validation

**Goal:** Board model fully operational; setup phase validation complete.

### Tasks

---

#### TASK-201: Implement board operations

**User story:** US-201  
**Module:** `src/domain/board.py`  
**Depends on:** TASK-104

**Input:** `game_components.md §2`  
**Output:** Complete `Board` methods

**Steps:**

1. Confirm `Board.create_empty()` creates all 100 squares with correct
   terrain (8 lakes at the positions listed in `game_components.md §2.2`).
2. Implement `Board.get_square(pos: Position) -> Square`.
3. Implement `Board.neighbours(pos: Position) -> list[Position]`: returns
   orthogonal neighbours that are within bounds (no lake filter here –
   that is the rules engine's job).
4. Implement `Board.is_lake(pos: Position) -> bool`.
5. Implement `Board.is_empty(pos: Position) -> bool` (no piece on that square).
6. Implement `Board.is_in_setup_zone(pos: Position, side: PlayerSide) -> bool`:
   RED → rows 6–9; BLUE → rows 0–3.
7. Implement `Board.place_piece(piece: Piece, pos: Position) -> Board`:
   returns a **new** `Board` (immutable) with the piece placed.
8. Implement `Board.remove_piece(pos: Position) -> Board`.
9. Implement `Board.move_piece(from_pos: Position, to_pos: Position) -> Board`.
10. Write `tests/unit/domain/test_board.py` covering all methods.

**Example:**

```python
board = Board.create_empty()
assert board.is_lake(Position(4, 2)) is True
assert len(board.neighbours(Position(0, 0))) == 2   # corner
assert len(board.neighbours(Position(5, 5))) == 4   # centre
```

**Test cases to cover:**

- All 8 lake positions are identified correctly.
- Corner, edge, and centre neighbour counts.
- Setup zone boundaries for both players.
- `place_piece` returns new board (original unchanged).

---

#### TASK-202: Implement setup phase validation

**User story:** US-206  
**Module:** `src/domain/rules_engine.py`  
**Depends on:** TASK-201

**Input:** `game_components.md §7`  
**Output:** `validate_placement()` and `is_setup_complete()`

**Steps:**

1. Create `src/domain/rules_engine.py`.
2. Define `ValidationResult(Enum)`: `OK, INVALID`.
3. Define `RulesViolationError(Exception)`.
4. Implement `validate_placement(state: GameState, cmd: PlacePiece) -> ValidationResult`:
   - Reject if `pos` is not in the player's setup zone.
   - Reject if `pos` is a lake square.
   - Reject if `pos` is already occupied.
5. Implement `is_setup_complete(state: GameState) -> bool`:
   - Returns `True` only when both players have exactly 40 pieces on the board.
6. Implement `apply_placement(state: GameState, cmd: PlacePiece) -> GameState`:
   - Validates first; if invalid raises `RulesViolationError`.
   - Returns new `GameState` with piece placed.
7. Write `tests/unit/domain/test_rules_engine.py` with a `TestSetupPhase` class.

**Example:**

```python
result = validate_placement(state, PlacePiece(flag, Position(9, 0)))
assert result == ValidationResult.OK

result = validate_placement(state, PlacePiece(scout, Position(2, 0)))
assert result == ValidationResult.INVALID  # Blue zone
```

**Test cases to cover:**

- Valid Red placement (row 6–9).
- Invalid Red placement in Blue zone (row 0–3).
- Invalid placement on lake.
- `is_setup_complete()` with 39/40/40 pieces per side.

---

## Sprint 4 (Week 4): Movement Validation

**Goal:** All movement rules implemented and fully tested.

### Tasks

---

#### TASK-203: Implement normal piece movement validation

**User story:** US-202  
**Module:** `src/domain/rules_engine.py`  
**Depends on:** TASK-202

**Input:** `game_components.md §4.1, §4.3`  
**Output:** `validate_move()` for normal pieces and immovable pieces

**Steps:**

1. Implement `validate_move(state: GameState, move: Move) -> ValidationResult`:
   a. Reject if `phase != GamePhase.PLAYING`.
   b. Reject if the piece's owner is not the active player.
   c. Reject if piece is `BOMB` or `FLAG` (immovable).
   d. Reject if `from_pos == to_pos` (stationary move).
   e. Reject if the move is diagonal (row delta and col delta both non-zero).
   f. Reject if the piece is not a Scout and the distance is > 1.
   g. Reject if `to_pos` is a lake square.
   h. Reject if `to_pos` contains a friendly piece.
2. Implement `apply_move(state: GameState, move: Move) -> GameState`:
   - Validates via `validate_move`; raises `RulesViolationError` if invalid.
   - Returns new `GameState` with piece moved; increments `turn_number`.
   - If `to_pos` has enemy piece, delegates to `combat.py`.
3. Implement the **two-square rule** check inside `validate_move`:
   - Inspect the last 4 entries in `move_history` for the same piece.
   - If the piece has oscillated between the same two squares for ≥ 2 full
     round trips, return `ValidationResult.INVALID`.

**Example:**

```python
# Two-square rule
result = validate_move(state_after_two_oscillations, oscillation_move)
assert result == ValidationResult.INVALID
```

**Test cases to cover:**

- Valid 1-square orthogonal moves in all 4 directions.
- Rejected diagonal move.
- Rejected move > 1 square for non-Scout.
- Rejected move to lake.
- Rejected move to friendly piece.
- Bomb and Flag movement rejected.
- Two-square rule triggered after 2 complete back-and-forth cycles.

---

#### TASK-204: Implement Scout movement validation

**User story:** US-203  
**Module:** `src/domain/rules_engine.py`  
**Depends on:** TASK-203

**Input:** `game_components.md §4.2`  
**Output:** Scout-specific movement logic in `validate_move()`

**Steps:**

1. In `validate_move()`, after the diagonal check, add Scout branch:
   - Determine the direction vector (row or col delta, normalised to ±1).
   - Traverse from `from_pos` toward `to_pos` one step at a time.
   - If any intermediate square is a lake: `INVALID`.
   - If any intermediate square contains a friendly piece: `INVALID`.
   - If an intermediate square contains an enemy piece and `to_pos` is
     beyond it: `INVALID` (cannot jump over enemy).
   - If `to_pos` contains an enemy piece: `OK` (sets `move_type = ATTACK`).
   - If `to_pos` is empty and within the board: `OK`.
2. Write a dedicated `TestScoutMovement` class in the test file.

**Example:**

```python
# Long-range move in empty column
result = validate_move(state, Move(scout, Pos(6,4), Pos(2,4), MoveType.MOVE))
assert result == ValidationResult.OK

# Blocked by friendly piece at (4,4)
result = validate_move(state_with_friendly_at_4_4, Move(scout, Pos(6,4), Pos(3,4)))
assert result == ValidationResult.INVALID
```

**Test cases to cover:**

- Scout moves 1 to 8 squares in all 4 directions.
- Blocked by friendly piece at various distances.
- Blocked by lake.
- Attack: Scout stops on enemy square (does not jump over).
- Diagonal rejected (same as normal pieces).

---

## Sprint 5 (Week 5): Combat Resolution and Win Conditions

**Goal:** Full combat resolution with all special cases; win conditions detected.

### Tasks

---

#### TASK-205: Implement combat resolution

**User story:** US-204  
**Module:** `src/domain/combat.py`  
**Depends on:** TASK-104

**Input:** `game_components.md §5`  
**Output:** `resolve_combat()` function

**Steps:**

1. Create `src/domain/combat.py`.
2. Implement `resolve_combat(attacker: Piece, defender: Piece) -> CombatResult`:
   - **Flag capture:** If `defender.rank == Rank.FLAG` → `ATTACKER_WINS`
     (caller then triggers game over).
   - **Bomb special case:** If `defender.rank == Rank.BOMB`:
     - If `attacker.rank == Rank.MINER` → `ATTACKER_WINS`.
     - Else → `DEFENDER_WINS`.
   - **Spy special case:** If `attacker.rank == Rank.SPY` and
     `defender.rank == Rank.MARSHAL` → `ATTACKER_WINS`.
   - **General case:** Compare `attacker.rank.value` vs `defender.rank.value`:
     - Attacker > Defender → `ATTACKER_WINS`.
     - Attacker < Defender → `DEFENDER_WINS`.
     - Equal → `DRAW` (both removed).
   - Set `attacker_survived` and `defender_survived` based on outcome.
   - Set `revealed=True` on both pieces in the returned `CombatResult`.
3. Write `tests/unit/domain/test_combat.py`.

**Example:**

```python
result = resolve_combat(attacker=spy, defender=marshal)
assert result.outcome == CombatOutcome.ATTACKER_WINS
assert result.attacker_survived is True
assert result.defender_survived is False

result = resolve_combat(attacker=marshal, defender=spy)
assert result.outcome == CombatOutcome.ATTACKER_WINS  # normal rank comparison
```

**Test cases to cover:**

- All 10 AC scenarios from US-204.
- Spy attacking Marshal vs Marshal attacking Spy.
- Both-removed draw case.
- Post-combat `revealed=True` on both pieces.

---

#### TASK-206: Integrate combat with move application and win detection

**User story:** US-205  
**Module:** `src/domain/rules_engine.py`  
**Depends on:** TASK-205

**Input:** `game_components.md §5, §6`  
**Output:** `apply_move()` integrates combat; `check_win_condition()` implemented

**Steps:**

1. In `apply_move()`, when `move.move_type == MoveType.ATTACK`:
   - Call `resolve_combat(attacker, defender)`.
   - Update board based on outcome (remove loser(s), move winner if applicable).
   - Append `MoveRecord(move, combat_result, turn_number)` to `move_history`.
   - Mark both pieces `revealed=True` in the new state.
2. Implement `check_win_condition(state: GameState) -> GameState`:
   - If a Flag was just captured → set `phase=GAME_OVER`, `winner=attacker.owner`.
   - If the active player's opponent has no moveable pieces → set
     `phase=GAME_OVER`, `winner=active_player`.
   - If `turn_number >= 3000` → set `phase=GAME_OVER`, `winner=None` (draw).
   - Otherwise return state unchanged.
3. Call `check_win_condition()` at the end of every `apply_move()`.
4. Write `TestWinConditions` class in `test_rules_engine.py`.

**Test cases to cover:**

- Flag capture immediately triggers GAME_OVER.
- Player with only Bombs and Flag loses.
- Turn counter ≥ 3000 results in draw.
- No false GAME_OVER trigger in normal mid-game.

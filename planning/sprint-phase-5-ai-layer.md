# Sprint Plan – Phase 5: AI Layer

**Phase:** 5  
**Duration:** 3 weeks (Sprints 11–13)  
**Exit criteria:** Hard AI (depth-6 minimax) completes a move in < 950 ms; all AI unit tests pass  
**Epic:** EPIC-5  
**Specification refs:** [`ai_strategy.md`](../specifications/ai_strategy.md)

---

## Sprint 11 (Week 11): Evaluation Function and Move Ordering

**Goal:** AI can score board positions; move ordering heuristic implemented.

### Tasks

---

#### TASK-501: Implement piece value table and material score

**User story:** US-501  
**Module:** `src/ai/evaluation.py`  
**Depends on:** TASK-104

**Input:** `ai_strategy.md §6.2`  
**Output:** `PIECE_VALUES` dict and `material_score(state, side)`

**Steps:**

1. Create `src/ai/evaluation.py`.
2. Define `PIECE_VALUES: dict[Rank, float]` with values from
   `ai_strategy.md §6.2`:
   ```
   FLAG: infinity (sentinel: 1_000_000)
   BOMB: 7, MARSHAL: 10, GENERAL: 9, COLONEL: 8, MAJOR: 7,
   CAPTAIN: 6, LIEUTENANT: 5, SERGEANT: 4, MINER: 8, SCOUT: 3, SPY: 6
   ```
3. Implement `material_score(state: GameState, side: PlayerSide) -> float`:
   Sum of `PIECE_VALUES[piece.rank]` for all pieces belonging to `side`.
4. Write unit tests verifying Miner=8 (not 3) and Spy=6 (not 1).

**Example:**

```python
assert PIECE_VALUES[Rank.MINER] == 8   # strategic value > raw rank
assert PIECE_VALUES[Rank.SPY] == 6
assert PIECE_VALUES[Rank.MARSHAL] == 10
```

**Test cases to cover:**

- All 12 piece values match `ai_strategy.md §6.2`.
- `material_score()` sums correctly for a test state.

---

#### TASK-502: Implement mobility, flag safety, and information advantage scores

**User story:** US-501  
**Module:** `src/ai/evaluation.py`  
**Depends on:** TASK-501, TASK-203

**Input:** `ai_strategy.md §6.1`  
**Output:** Three additional scoring components and `evaluate()` aggregation

**Steps:**

1. Implement `mobility_score(state: GameState, side: PlayerSide) -> float`:
   Count all legal moves available to `side`'s pieces using
   `rules_engine.generate_moves(state, side)`.
   (Implement `generate_moves()` in `rules_engine.py` if not yet present.)
2. Implement `flag_safety_score(state: GameState, side: PlayerSide) -> float`:
   - Find `side`'s Flag position.
   - Find closest opponent moveable piece (Manhattan distance).
   - Score = `distance * weight` + `bomb_coverage_count * weight`.
3. Implement `info_advantage_score(state: GameState, ai_side: PlayerSide) -> float`:
   - Count opponent pieces with `revealed=False`.
   - Score = `-(unrevealed_count * weight)` (penalty for uncertainty).
4. Implement `evaluate(state: GameState, ai_side: PlayerSide) -> float`:
   - If `state.winner == ai_side`: return `+1_000_000`.
   - If `state.winner is not None`: return `-1_000_000`.
   - Return weighted sum: material×0.40 + mobility×0.20 + flag_safety×0.25
     + info_advantage×0.15.
5. Write `tests/unit/ai/test_evaluation.py`.

**Test cases to cover:**

- Terminal win state returns max sentinel.
- Terminal loss state returns min sentinel.
- Flag surrounded by Bombs gives high flag safety score.
- All-revealed state gives 0 information advantage penalty.

---

#### TASK-503: Implement move ordering

**User story:** US-502  
**Module:** `src/ai/evaluation.py`  
**Depends on:** TASK-502

**Input:** `ai_strategy.md §7`  
**Output:** `order_moves(moves, state, ai_side) -> list[Move]`

**Steps:**

1. Implement `order_moves(moves: list[Move], state: GameState, ai_side: PlayerSide) -> list[Move]`:
   - **Captures** first: moves with `move_type == ATTACK`, sorted by
     `PIECE_VALUES[target.rank]` descending.
   - **Flag-approach moves**: moves that reduce Manhattan distance to the
     estimated opponent Flag location.
   - **Probe moves**: Scout moves to unknown-rank opponent pieces.
   - **All others**: sorted by mobility improvement.
2. Write tests verifying captures are ordered before non-captures and
   flag-approach before random moves.

---

## Sprint 12 (Week 12): Minimax and AI Orchestrator

**Goal:** Minimax search functional at all three depths within time budget.

### Tasks

---

#### TASK-504: Implement minimax with alpha-beta pruning

**User story:** US-502  
**Module:** `src/ai/minimax.py`  
**Depends on:** TASK-503

**Input:** `ai_strategy.md §4.2`  
**Output:** `minimax(state, depth, ai_side, alpha, beta, time_limit) -> Move | None`

**Steps:**

1. Create `src/ai/minimax.py`.
2. Implement `minimax(state, depth, ai_side, alpha=-inf, beta=+inf, deadline=None) -> Move | None`:
   - Base cases: `depth == 0` or `state.phase == GAME_OVER` → return
     `evaluate(state, ai_side)`.
   - For maximising player (AI): iterate `order_moves(generate_moves(state, ai_side))`;
     recurse; track alpha; prune when `alpha >= beta`.
   - For minimising player (opponent): iterate opponent's moves; recurse;
     track beta; prune when `beta <= alpha`.
   - Check `time.monotonic() > deadline` inside the loop; if exceeded,
     return best move found so far (iterative deepening support).
3. Add `node_count: int` attribute for test assertions.
4. Implement iterative deepening wrapper `best_move(state, max_depth, deadline)`:
   - Calls minimax at depth 1, 2, …, `max_depth`.
   - Returns best move at the deepest completed depth before deadline.
5. Write `tests/unit/ai/test_minimax.py`.

**Example:**

```python
move = best_move(state_flag_in_reach, max_depth=4, deadline=time.monotonic()+5)
# AI should find the flag-capture move
assert rules_engine.validate_move(state, move) == ValidationResult.OK
```

**Test cases to cover:**

- Legal move always returned.
- Forced win-in-1 detected at depth 2.
- Depth-6 search completes in < 950 ms on a representative mid-game state.
- With ordering: fewer nodes evaluated than without ordering (at same depth).
- `None` returned when no legal moves exist.

---

#### TASK-505: Implement AI Orchestrator

**User story:** US-503  
**Module:** `src/ai/ai_orchestrator.py`  
**Depends on:** TASK-504

**Input:** `ai_strategy.md §8`  
**Output:** `AIOrchestrator.request_move(state, player_type) -> Move`

**Steps:**

1. Create `src/ai/ai_orchestrator.py`.
2. Define depth mapping:
   ```python
   DIFFICULTY_DEPTH = {
       PlayerType.AI_EASY: 2,
       PlayerType.AI_MEDIUM: 4,
       PlayerType.AI_HARD: 6,
   }
   ```
3. Implement `request_move(state: GameState, player_type: PlayerType) -> Move`:
   - Determine `depth = DIFFICULTY_DEPTH[player_type]`.
   - If fewer than 10 pieces per side: `depth += 2` (endgame boost).
   - Set `deadline = time.monotonic() + (time_limit_ms / 1000)`.
   - Check opening book first (US-504); if in opening → return book move.
   - Call `best_move(state, depth, deadline)`.
   - Validate returned move via `rules_engine.validate_move()`.
   - If invalid: retry up to 3 times (regenerate and search again).
   - If 3 failures: raise `AIMoveFailed("AI could not produce a legal move")`.
4. Write `tests/unit/ai/test_ai_orchestrator.py` with mocked minimax.

**Test cases to cover:**

- Easy → depth 2; Medium → depth 4; Hard → depth 6.
- Endgame boost applies when < 10 pieces per side.
- Retry logic triggers on illegal move.
- `AIMoveFailed` raised after 3 failures.

---

## Sprint 13 (Week 13): Opening Book and Probability Tracker

**Goal:** AI plays strong openings; probability tracker updates correctly.

### Tasks

---

#### TASK-506: Implement Opening Book

**User story:** US-504  
**Module:** `src/ai/opening_book.py`  
**Depends on:** TASK-104

**Input:** `ai_strategy.md §4.1`  
**Output:** `OpeningBook.get_setup(difficulty, strategy) -> dict[Position, Piece]`

**Steps:**

1. Create `src/ai/opening_book.py`.
2. Define two base setup dictionaries for RED (rows 6–9):
   - **Fortress**: Flag at `(9,0)`, 3 Bombs around Flag, Miners in rows 7–8,
     Scouts in row 6, Marshal/General/Colonels in row 7.
   - **Blitz**: Scouts and high-rank pieces in row 6, Marshal at `(6,5)`,
     Flag deeper at `(9,4)`.
3. Implement `get_setup(difficulty: PlayerType, strategy: str = "fortress") -> dict[Position, Piece]`:
   - For `AI_EASY`: shuffle all piece positions randomly within the setup zone.
   - For `AI_MEDIUM`: apply 30 % random perturbations to the base setup.
   - For `AI_HARD`: return the unperturbed base setup.
4. Validate that every returned setup contains exactly 40 pieces in valid
   positions (rows 6–9 for RED; rows 0–3 for BLUE via mirroring).
5. Write `tests/unit/ai/test_opening_book.py`.

**Test cases to cover:**

- Exactly 40 pieces returned for all difficulty levels.
- Fortress: Flag in back row.
- Easy: Returns different arrangements across calls (random).
- Hard: Returns same arrangement on repeated calls (deterministic).

---

#### TASK-507: Implement Probability Tracker

**User story:** US-505  
**Module:** `src/ai/probability_tracker.py`  
**Depends on:** TASK-104

**Input:** `ai_strategy.md §5`  
**Output:** `ProbabilityTracker` with Bayesian updates

**Steps:**

1. Create `src/ai/probability_tracker.py`.
2. Implement `ProbabilityTracker.__init__(opponent_pieces: list[Piece])`:
   - For each unrevealed piece, initialise `possible_ranks` as the full
     set of opponent ranks; compute uniform probability distribution.
3. Implement `update_on_move(piece: Piece) -> None`:
   - Remove `BOMB` and `FLAG` from `possible_ranks`; renormalise.
4. Implement `update_on_reveal(piece: Piece, actual_rank: Rank) -> None`:
   - Collapse distribution to `{actual_rank: 1.0}`.
   - Remove `actual_rank` from all other pieces' possible_ranks; renormalise.
5. Implement `update_on_combat_loss(piece: Piece, loser_rank: Rank) -> None`:
   - If piece survived, eliminate all ranks ≤ `loser_rank`; renormalise.
6. Implement `get_distribution(piece: Piece) -> dict[Rank, float]`.
7. Implement `get_most_likely_rank(piece: Piece) -> Rank`.
8. Write `tests/unit/ai/test_probability_tracker.py`.

**Example:**

```python
tracker.update_on_move(blue_piece)
dist = tracker.get_distribution(blue_piece)
assert dist[Rank.BOMB] == 0.0
assert dist[Rank.FLAG] == 0.0
assert abs(sum(dist.values()) - 1.0) < 1e-9
```

**Test cases to cover:**

- Initial uniform distribution.
- Move eliminates BOMB and FLAG.
- Reveal collapses distribution.
- Distribution always sums to 1.0 after any update.

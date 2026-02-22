# EPIC-5: AI Layer – User Stories

**Epic:** EPIC-5  
**Phase:** 5  
**Specification refs:** [`ai_strategy.md`](../specifications/ai_strategy.md)

---

## US-501: Evaluation Function

**Epic:** EPIC-5  
**Priority:** Must Have  
**Specification refs:** [`ai_strategy.md §6`](../specifications/ai_strategy.md)

**As a** game designer,  
**I want** the AI evaluation function to score a board position using material,
mobility, flag safety, and information advantage,  
**so that** the AI makes strategically sound decisions that account for more
than just piece counts.

### Acceptance Criteria

- [ ] **AC-1:** Given a state where the AI has captured Blue's Marshal (rank 10),
      When evaluated, Then the score is higher than the same state without
      that capture (material component).
- [ ] **AC-2:** Given a state where the AI's Flag is surrounded by Bombs with
      no enemy pieces nearby, When evaluated, Then the flag safety score is
      maximal.
- [ ] **AC-3:** Given a state where all opponent pieces are revealed,
      When evaluated, Then the information advantage penalty is 0 (no
      uncertainty).
- [ ] **AC-4:** Given `evaluate(terminal_state_ai_wins)`, When called,
      Then the score is `+infinity` (or the maximum sentinel value).
- [ ] **AC-5:** Given `evaluate(terminal_state_ai_loses)`, When called,
      Then the score is `-infinity` (or the minimum sentinel value).
- [ ] **AC-6:** Piece value weights match `ai_strategy.md §6.2`:
      Marshal=10, Miner=8 (not 3), Spy=6 (not 1), Bomb=7, Scout=3.

### Example

```python
# Miner is more valuable than its rank suggests
assert PIECE_VALUES[Rank.MINER] == 8
assert PIECE_VALUES[Rank.SPY] == 6
assert PIECE_VALUES[Rank.MARSHAL] == 10
```

### Definition of Done

- [ ] `src/ai/evaluation.py` implements `evaluate(game_state, ai_side) -> float`.
- [ ] `tests/unit/ai/test_evaluation.py` verifies all piece values and all
      four scoring components.

### Out of Scope

- MCTS evaluation (v2.0).

---

## US-502: Minimax with Alpha-Beta Pruning

**Epic:** EPIC-5  
**Priority:** Must Have  
**Specification refs:** [`ai_strategy.md §4.2, §7`](../specifications/ai_strategy.md)

**As a** player,  
**I want** the AI to search game positions to the configured depth using
minimax with alpha-beta pruning and move ordering,  
**so that** the AI plays at a competent level within the time budget.

### Acceptance Criteria

- [ ] **AC-1:** Given a depth-2 search on a mid-game state, When `minimax(state, 2)`,
      Then the returned `Move` is a legal move in the current state.
- [ ] **AC-2:** Given a forced win-in-1 (AI can capture the Flag immediately),
      When `minimax(state, 2)`, Then the returned `Move` is the flag capture.
- [ ] **AC-3:** Given a depth-6 search, When timed, Then execution completes
      in < 950 ms on a standard laptop (or time limit triggers iterative
      deepening early exit).
- [ ] **AC-4:** Given move ordering enabled, When comparing two search runs
      at the same depth (with/without ordering), Then the ordered version
      evaluates fewer nodes (verified by node counter).
- [ ] **AC-5:** Given a state where all AI moves are illegal (game over),
      When `minimax` is called, Then it returns `None` or raises
      `NoLegalMovesError`.

### Example

```python
best_move = minimax(state, depth=4, ai_side=PlayerSide.BLUE)
assert rules_engine.validate_move(state, best_move) == ValidationResult.OK
```

### Definition of Done

- [ ] `src/ai/minimax.py` implements `minimax(state, depth, ai_side, alpha, beta) -> Move | None`.
- [ ] Iterative deepening used to respect `time_limit_ms`.
- [ ] Node counter available for test assertions.
- [ ] `tests/unit/ai/test_minimax.py` covers all AC scenarios.

### Out of Scope

- MCTS (v2.0).
- Probability Tracker integration (US-505).

---

## US-503: AI Orchestrator

**Epic:** EPIC-5  
**Priority:** Must Have  
**Specification refs:** [`ai_strategy.md §8`](../specifications/ai_strategy.md)

**As a** developer,  
**I want** the AI Orchestrator to route requests to the correct search depth
based on difficulty, enforce the time limit, and retry on illegal moves,  
**so that** the AI always produces a legal move within budget regardless of
difficulty setting.

### Acceptance Criteria

- [ ] **AC-1:** Given `PlayerType.AI_EASY`, When `request_move()`,
      Then `minimax` is called with `depth=2`.
- [ ] **AC-2:** Given `PlayerType.AI_MEDIUM`, When `request_move()`,
      Then `minimax` is called with `depth=4`.
- [ ] **AC-3:** Given `PlayerType.AI_HARD`, When `request_move()`,
      Then `minimax` is called with `depth=6`.
- [ ] **AC-4:** Given the AI returns a move rejected by the rules engine,
      When the orchestrator retries, Then it calls `minimax` again; after 3
      failures it logs a `CRITICAL` error.
- [ ] **AC-5:** Given `time_limit_ms=950` and the search exceeds this,
      When the limit is hit, Then the best move found so far is returned.
- [ ] **AC-6:** Given end-game (fewer than 10 pieces per side), When
      `request_move()`, Then depth is increased to 8.

### Example

> Orchestrator is called for Hard AI on turn 45. It sets `time_limit_ms=950`,
> calls minimax at depth 6. Minimax finds the flag-capture move at depth 3
> and returns it early. Orchestrator submits it to the Turn Manager.

### Definition of Done

- [ ] `src/ai/ai_orchestrator.py` implements `request_move(state, player_type) -> Move`.
- [ ] Difficulty-to-depth mapping configurable via `config.yaml`.
- [ ] `tests/unit/ai/test_ai_orchestrator.py` mocks minimax and verifies
      routing and retry logic.

### Out of Scope

- Opening book (US-504).
- Parallel/multi-threaded search.

---

## US-504: Opening Book

**Epic:** EPIC-5  
**Priority:** Should Have  
**Specification refs:** [`ai_strategy.md §4.1`](../specifications/ai_strategy.md)

**As a** player,  
**I want** the AI to use a strong pre-defined piece arrangement at the start
of each game,  
**so that** the AI plays competent openings without the cost of searching
the full setup space.

### Acceptance Criteria

- [ ] **AC-1:** Given `difficulty=HARD`, When `opening_book.get_setup(HARD)`,
      Then a valid 40-piece arrangement covering Red rows 6–9 is returned.
- [ ] **AC-2:** Given `difficulty=EASY`, When `get_setup(EASY)`, Then the
      arrangement is a random permutation of a base setup (not the optimal
      Fortress) to simulate weaker play.
- [ ] **AC-3:** Given the Fortress strategy, When generated, Then the Flag is
      in a back corner (`(9,0)`, `(9,1)`, `(9,8)`, or `(9,9)`) surrounded
      by at least 3 Bombs.
- [ ] **AC-4:** Given `get_setup()` called 5 times with `difficulty=MEDIUM`,
      When comparing results, Then at least 2 different arrangements are
      returned (some randomisation).

### Example

```python
setup = opening_book.get_setup(difficulty=Difficulty.HARD, strategy="fortress")
flag_pos = next(p for p, piece in setup.items() if piece.rank == Rank.FLAG)
assert flag_pos.row == 9  # back row
```

### Definition of Done

- [ ] `src/ai/opening_book.py` defines at least 2 strategies (Fortress,
      Blitz).
- [ ] `tests/unit/ai/test_opening_book.py` validates that returned setups
      contain exactly 40 pieces covering only valid setup squares.

### Out of Scope

- Probe strategy (Could Have).
- Learning/adaptive opening book.

---

## US-505: Probability Tracker

**Epic:** EPIC-5  
**Priority:** Should Have  
**Specification refs:** [`ai_strategy.md §5`](../specifications/ai_strategy.md)

**As a** developer,  
**I want** the Probability Tracker to maintain and update a probability
distribution over possible ranks for each unrevealed opponent piece,  
**so that** the AI can make informed decisions about likely piece identities
rather than treating all unrevealed pieces as equally dangerous.

### Acceptance Criteria

- [ ] **AC-1:** Given game start, When `probability_tracker.get_distribution(piece)`,
      Then all 12 ranks have equal probability (uniform distribution summing to 1.0).
- [ ] **AC-2:** Given an opponent piece moves, When `update_on_move(piece)`,
      Then `BOMB` and `FLAG` probabilities are set to 0 for that piece (they
      cannot move) and the distribution is renormalised.
- [ ] **AC-3:** Given a piece is revealed as `SCOUT` through combat, When
      `update_on_reveal(piece, Rank.SCOUT)`, Then that piece's distribution
      collapses to `{SCOUT: 1.0}` and other pieces' SCOUT probability is
      updated.
- [ ] **AC-4:** Given any update, When `sum(distribution.values())`,
      Then the result is `1.0` (± 1e-9 floating-point tolerance).

### Example

```python
tracker = ProbabilityTracker(opponent_pieces=blue_pieces)
tracker.update_on_move(blue_piece_at_3_4)
dist = tracker.get_distribution(blue_piece_at_3_4)
assert dist[Rank.BOMB] == 0.0
assert dist[Rank.FLAG] == 0.0
assert abs(sum(dist.values()) - 1.0) < 1e-9
```

### Definition of Done

- [ ] `src/ai/probability_tracker.py` implements `update_on_move`, `update_on_reveal`,
      and `get_distribution`.
- [ ] `tests/unit/ai/test_probability_tracker.py` covers all AC scenarios
      including renormalisation invariant.

### Out of Scope

- ISMCTS sampling over the probability distribution (v2.0).

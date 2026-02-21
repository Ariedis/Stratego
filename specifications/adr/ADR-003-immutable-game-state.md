# ADR-003: Immutable GameState Snapshots

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

The `GameState` object is central to all game logic, AI search, and
persistence. We must decide whether game state should be mutated in-place or
replaced with immutable snapshots on each state transition.

## Decision

**GameState is immutable. The rules engine produces a new GameState for each
move rather than mutating the existing state.**

## Rationale

1. **AI safety:** The AI search tree explores many future states simultaneously
   (conceptually). Immutable states ensure the AI cannot accidentally corrupt
   the live game state during search.

2. **Undo / redo:** A stack of `GameState` snapshots provides undo/redo for
   free. The application layer simply pops the stack.

3. **Save game simplicity:** Any snapshot can be serialised directly to disk.
   No complex serialisation logic needed to capture mutable in-progress state.

4. **Testability:** Tests can prepare a `GameState`, call `apply_move()`, and
   assert on the returned state without worrying about state leaking between
   test cases.

5. **Precedent:** `python-chess` uses a `Board.copy()` strategy for its search
   tree and has demonstrated that this approach is performant enough for
   complex game trees. Stratego's 10×10 board with 80 pieces is significantly
   simpler than a chess position, so shallow copy performance is not a concern.

## Trade-offs

- **Memory:** Each move creates a new object. For a 300-turn game this means
  300 `GameState` objects in the undo stack plus search tree copies. Each
  object is small (10×10 grid + metadata ≈ a few KB). Total memory impact
  is negligible on modern hardware.
- **Performance:** Shallow copy of a 10×10 grid is O(100) operations.
  Profiling showed no measurable overhead for turn-based gameplay.

## Alternatives Considered

| Approach | Outcome |
|---|---|
| Mutable in-place state with undo log | More complex undo; risk of state corruption during AI search; rejected |
| Persistent (functional) immutable data structures | No Python library provides production-quality persistent trees for this use case; unnecessary complexity |

## Consequences

- `GameState`, `Board`, `Piece`, `Move` are all implemented as
  `dataclasses(frozen=True)` or equivalent.
- `rules_engine.apply_move(state, move) → GameState` always returns a new
  object.
- The application layer maintains an `undo_stack: list[GameState]`.

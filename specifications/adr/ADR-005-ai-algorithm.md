# ADR-005: Minimax + Alpha-Beta Pruning for AI (Phase 1)

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

Stratego is a game of imperfect information (hidden piece ranks). We need to
select an AI algorithm that:

1. Produces challenging, human-like play.
2. Runs within the 950 ms per-move time budget.
3. Is implementable in Phase 1 without third-party AI libraries.
4. Is extensible to handle hidden information in Phase 2.

## Decision

**Phase 1: Minimax with alpha-beta pruning on a determinised board state.**  
**Phase 2: Upgrade to Information Set Monte Carlo Tree Search (ISMCTS).**

## Rationale

### Phase 1 – Minimax

1. **Proven algorithm:** Minimax is the gold standard for two-player zero-sum
   games. It is well-understood, easy to implement correctly, and easy to
   verify with unit tests.

2. **Determinisation:** For Phase 1, unknown opponent pieces are assigned their
   most likely rank (based on the Probability Tracker). This converts the
   imperfect-information game into a perfect-information game that minimax can
   handle directly.

3. **Alpha-beta pruning** reduces the effective branching factor from ~30 to
   ~√30 ≈ 5.5 per level in the best case, making depth-6 search feasible
   within the time budget.

4. **No library dependency:** Minimax is a dozen lines of recursive logic.
   No third-party library adds risk or dependency management overhead.

### Phase 2 – ISMCTS

Information Set MCTS, as demonstrated by the winning 2011 Computer Stratego
Championship entry (*Master of the Flag*), correctly handles the full
hidden-information nature of the game. It is the recommended Phase 2
algorithm.

## Alternatives Considered

| Algorithm | Outcome |
|---|---|
| Pure minimax (no determinisation) | Cannot handle hidden information directly; requires extensive extension |
| Random play | Rejected: trivially beatable; not a satisfying opponent |
| Neural network / deep learning | Requires training data and GPU; far exceeds project scope for Phase 1 |
| Negamax | Equivalent to minimax for zero-sum games; could be used as implementation variant |

## Consequences

- The `Minimax` class receives a `GameState` (determinised) and returns a
  `Move`.
- The `ProbabilityTracker` must be implemented to support determinisation.
- The evaluation function must be well-calibrated to make depth-6 search
  effective (shallow search with a bad evaluation is worse than deep search
  with a good one).
- In Phase 2, `MCTS` replaces `Minimax` behind the `AIOrchestrator` interface
  with no changes to the rest of the application.

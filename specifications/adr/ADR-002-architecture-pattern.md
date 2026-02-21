# ADR-002: MVC + Event Bus over ECS

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

We need to choose the primary architectural pattern for the Stratego game.
The two main candidates are:

- **MVC (Model-View-Controller)** – well understood, maps naturally to
  turn-based games.
- **ECS (Entity-Component-System)** – data-oriented, preferred for
  real-time games with many heterogeneous entities.

## Decision

**Use MVC as the primary structural pattern, augmented with an Event Bus for
component decoupling.**

## Rationale

1. **Entity count:** Stratego has at most 80 pieces, all with fixed, well-defined
   behaviours. ECS's main advantage (composable behaviour for thousands of
   heterogeneous entities) does not apply here.

2. **Turn-based nature:** Stratego has a sequential, turn-based game loop.
   ECS excels at per-frame parallel system updates (physics, rendering, AI
   all running simultaneously). This is unnecessary overhead for a turn-based
   game.

3. **Testability:** MVC's clean Model layer (zero UI dependencies) enables
   straightforward unit testing of all game rules without mocking a pygame
   context.

4. **Precedent:** Open-source Python board games (chess engines, Go boards,
   draughts implementations) universally use model-first, rendering-agnostic
   architectures aligned with MVC rather than ECS.

5. **Event Bus addition:** An Event Bus (publish/subscribe) decouples the
   Domain Layer from the Presentation Layer, providing the loose coupling
   benefit of ECS without its complexity.

## Alternatives Considered

| Pattern | Outcome |
|---|---|
| Pure ECS (Esper library) | Rejected: overcomplicated for 80 fixed-behaviour entities |
| Monolithic (single module) | Rejected: untestable, unmaintainable |
| Actor Model | Rejected: adds concurrency complexity with no benefit for single-threaded game loop |

## Consequences

- Domain layer has no imports from the presentation or infrastructure layers.
- All inter-component communication goes through the Event Bus.
- Adding a new renderer (e.g., web front-end) requires only a new subscriber,
  no domain changes.
- If a real-time mode is added in a future phase, ECS may need to be
  reconsidered for in-game entity management while MVC is retained for menus
  and state management.

# ADR-001: Python 3.12 as the Target Runtime

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

We must choose a Python version for the Stratego implementation. The choice
affects language features available to developers, library compatibility,
and long-term support horizon.

## Decision

**Use Python 3.12 as the minimum supported version.**

## Rationale

1. **`match` / `case` structural pattern matching** (available since 3.10)
   significantly simplifies combat resolution logic and game-phase state
   transitions, reducing conditional complexity.

2. **`dataclasses` with `frozen=True`** (3.7+) enable clean immutable value
   objects for `GameState`, `Move`, and `Position` without boilerplate.

3. **`typing` improvements** in 3.12 (`TypeAlias`, `TypeVarTuple`) improve
   domain model expressiveness and IDE support.

4. **Performance improvements** in 3.12's `asyncio` and general interpreter
   speed benefit the multiplayer server in v2.0.

5. **Security:** Python 3.12 is the current stable branch with security
   patches. Older versions approach end-of-life.

## Alternatives Considered

| Version | Outcome |
|---|---|
| Python 3.11 | Acceptable but misses 3.12 interpreter optimisations |
| Python 3.10 | Minimum for `match`; missing 3.12 improvements |
| PyPy | Incomplete `pygame-ce` support; rejected |

## Consequences

- Developers must use Python 3.12+.
- CI pipelines must test against 3.12.
- Some legacy systems running older Python versions cannot run the game
  without upgrading their Python installation (acceptable trade-off).

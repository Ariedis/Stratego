# Stratego – Technology Stack

**Document type:** Technology Stack  
**Version:** 1.0  
**Author:** Software Architect (Python Game Specialist)  
**Status:** Approved  
**Depends on:** [`architecture_overview.md`](./architecture_overview.md)

---

## 1. Purpose

This document justifies every library and tool selected for the Stratego
Python project. Each selection includes the alternatives considered, the
reasons for the decision, and real-world precedents from comparable projects.

---

## 2. Core Language

### Python 3.12

| Attribute | Detail |
|---|---|
| **Why 3.12** | Latest stable branch with long-term support. Structural pattern matching (`match`/`case`, added in 3.10) simplifies combat resolution switch logic. `dataclasses` (3.7+) with `frozen=True` provides clean immutable value objects. `typing` module improvements in 3.12 improve IDE support. |
| **Why not 3.11** | 3.12 includes significant `asyncio` and performance improvements; no cost to adopting latest stable. |
| **Why not PyPy** | pygame has incomplete PyPy support; CPython is sufficient for a 10×10 turn-based game. |

---

## 3. Game Engine / Rendering

### pygame-ce 2.x (Community Edition)

| Attribute | Detail |
|---|---|
| **What** | Fork of the original `pygame` library with active maintenance, bug fixes, and Python 3.12 compatibility. |
| **Why** | De-facto standard for 2D Python games. Extensive documentation, large community, and dozens of comparable open-source games (e.g., *Pygame Zero* tutorial games, *Dungeon Crawl Stone Soup* Python bots, open-source board-game clones). |
| **Alternatives considered** | **arcade** – more modern API, excellent docs, but smaller community. Recommended for new greenfield projects; pygame-ce chosen here for familiarity and ecosystem maturity. **pyglet** – lower-level, less suited for board-game UIs. **Panda3D** – 3D engine; overkill. |
| **Risk** | pygame's text rendering (`pygame.font`) is limited; use `pygame-gui` for complex menus. |
| **Precedent** | Open-source Stratego clones such as `pythonator/stratego` on GitHub use pygame. Multiple Python board-game projects (chess, Go, checkers) use pygame for rendering. |

### pygame-gui 0.6.x

| Attribute | Detail |
|---|---|
| **What** | UI toolkit built on top of pygame for menus, dialogs, and panels. |
| **Why** | Avoids reimplementing buttons, scrollbars, and text inputs from scratch. Integrates natively with pygame's event loop. |

---

## 4. AI / Search

### Standard library only (Phase 1)

The minimax implementation with alpha-beta pruning requires no third-party AI
libraries. Python's standard library `copy`, `dataclasses`, and `typing` are
sufficient.

### numpy (optional optimisation)

| Attribute | Detail |
|---|---|
| **When** | If profiling reveals the evaluation function is the bottleneck. |
| **Why** | Board representation as a 10×10 `numpy.ndarray` enables fast vectorised operations for piece count and mobility scoring. |
| **Precedent** | *python-chess* uses bitboards for speed; *Leela Chess Zero* uses numpy-backed board representations in its Python training pipeline. |

---

## 5. Testing

### pytest 8.x

| Attribute | Detail |
|---|---|
| **Why** | Industry-standard Python test framework. Fixture system, parametrised tests, and rich plugin ecosystem. Preferred over `unittest` for its concise syntax. |
| **Key plugins** | `pytest-cov` (coverage), `pytest-xdist` (parallel tests), `pytest-mock` (mocking). |

### pytest-mock

Used to mock the pygame event loop and renderer in unit tests, ensuring the
domain layer is fully testable without a display.

---

## 6. Static Analysis & Code Quality

### mypy 1.x (strict mode)

| Attribute | Detail |
|---|---|
| **Why** | Static type checking catches type errors before runtime. With `frozen=True` dataclasses and explicit `Enum` types, mypy can verify combat logic at analysis time. |
| **Configuration** | Run in `--strict` mode; no `Any` types in the domain layer. |

### ruff

| Attribute | Detail |
|---|---|
| **Why** | Extremely fast Python linter (replaces flake8 + isort + pep8 in a single tool). Native support in VS Code and PyCharm. |

---

## 7. Serialisation

### Python `json` (standard library)

Used for save-game files. The `json` module with custom `JSONEncoder` /
`JSONDecoder` for domain types (Enums, dataclasses) avoids third-party
dependencies for a core feature.

**Alternative considered:** `pydantic` – excellent for schema validation and
JSON serialisation with version evolution. Recommended if the save format
needs rigorous schema migration support in v2.0.

---

## 8. Dependency Management

### uv

| Attribute | Detail |
|---|---|
| **Why** | Modern, extremely fast Python package and project manager (replaces pip + venv). Resolves dependencies in milliseconds and produces a lockfile (`uv.lock`) for reproducible builds. |
| **Alternative** | `poetry` – mature, well-established, but slower. Either is acceptable; `uv` is the forward-looking choice for new projects in 2024–2025. |

---

## 9. Multiplayer (v2.0)

### websockets 13.x

| Attribute | Detail |
|---|---|
| **Why** | Pure-Python, asyncio-native WebSocket library. Minimal dependencies, well-maintained, widely used in Python game servers. |
| **Alternative** | `aiohttp` – heavier, full HTTP framework. Unnecessary for a dedicated game server. |

---

## 10. Full Dependency Summary

| Package | Version constraint | Purpose | Required |
|---|---|---|---|
| `pygame-ce` | `>=2.4` | 2D rendering and input | Yes |
| `pygame-gui` | `>=0.6` | UI widgets | Yes |
| `numpy` | `>=1.26` | Board evaluation optimisation | Optional |
| `websockets` | `>=13.0` | Multiplayer networking | v2.0 |
| `pydantic` | `>=2.6` | Save-game schema validation | Optional |
| `pytest` | `>=8.0` | Testing | Dev |
| `pytest-cov` | `>=5.0` | Coverage | Dev |
| `pytest-mock` | `>=3.12` | Mocking | Dev |
| `mypy` | `>=1.10` | Static type checking | Dev |
| `ruff` | `>=0.4` | Linting / formatting | Dev |
| `uv` | `>=0.4` | Dependency management | Dev |

---

## 11. What to Avoid

Based on lessons learned from comparable Python game projects:

| Library | Reason to avoid |
|---|---|
| `pygame` (original, not CE) | Unmaintained; Python 3.12 compatibility issues |
| `tkinter` for game rendering | Not designed for game loops; poor performance above 30 FPS |
| `kivy` | Cross-platform mobile focus; heavier than needed for a desktop game |
| `PIL` / `Pillow` for rendering | Image manipulation only, not a game engine |
| `asyncio` in the main game loop (phase 1) | Unnecessary complexity; pygame's synchronous event loop is sufficient for single-player |

---

## 12. Related Documents

| Document | Purpose |
|---|---|
| [`architecture_overview.md`](./architecture_overview.md) | How these technologies fit the architecture |
| [`system_design.md`](./system_design.md) | Which module uses which library |

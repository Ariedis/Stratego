# Stratego – High-Level Architecture Overview

**Document type:** Architecture Overview  
**Version:** 1.1  
**Author:** Software Architect (Python Game Specialist)  
**Status:** Approved  
**Changelog:** v1.1 – Added Game Loop pattern, Object Pool consideration, anti-patterns section; corrected layer diagram (removed erroneous pickle reference); added industry references from generalistprogrammer.com

---

## 1. Purpose

This document establishes the high-level architecture for a Python
implementation of the classic two-player board game **Stratego**. It defines
the system boundaries, primary layers, key modules, and the architectural
principles that will guide the detailed design of every subsystem.

All subsequent specification documents in this repository derive from and must
be consistent with this overview.

---

## 2. System Context

```mermaid
graph TD
    HumanPlayer["Human Player\n(keyboard / mouse)"]
    AIPlayer["AI Opponent\n(bot engine)"]
    NetworkPlayer["Remote Player\n(optional multiplayer)"]

    subgraph Stratego Application
        UI["Presentation Layer\n(pygame / terminal)"]
        GameEngine["Game Engine\n(rules, turns, combat)"]
        AIEngine["AI Engine\n(minimax / MCTS)"]
        Persistence["Persistence Layer\n(save / load)"]
    end

    HumanPlayer -->|input events| UI
    NetworkPlayer -->|WebSocket messages| GameEngine
    UI --> GameEngine
    AIPlayer -->|move decisions| AIEngine
    AIEngine --> GameEngine
    GameEngine --> Persistence
    GameEngine --> UI
```

### Key External Actors

| Actor | Interaction |
|---|---|
| Human Player | Keyboard / mouse input via the Presentation Layer |
| AI Opponent | Move decisions via the AI Engine |
| Remote Player | Network messages over WebSocket (optional phase 2) |
| File System | Save / load game state via Persistence Layer |

---

## 3. Architectural Style

### 3.1 Primary Pattern: Layered MVC with an Event Bus

A **Model-View-Controller** (MVC) architecture is the primary structural
pattern. An **Event Bus** decouples components and prevents circular
dependencies.

**Why MVC?**

Stratego is a turn-based game with a clear separation between game state,
rules enforcement, and visual representation. Games such as *Battle for
Wesnoth* and numerous open-source chess engines use MVC successfully for
turn-based titles because it:

- Makes the rules engine independently testable (no UI dependency).
- Allows swapping renderers (pygame ↔ terminal ↔ web) without touching game
  logic.
- Maps cleanly to Stratego's phases: setup, turn execution, combat resolution.

**Why not pure ECS (Entity-Component-System)?**

ECS excels for real-time games with thousands of heterogeneous entities (e.g.,
*Factorio*, *Minecraft* at the systems level). Stratego has at most 80 pieces
with fixed, well-defined behaviour. An ECS would add complexity without
meaningful performance benefit. ECS **may** be reconsidered if a future phase
adds real-time animations or particle effects.

> **Industry reference:** The open-source Python project *python-chess* (used
> in production AI research) follows a clean model-first approach similar to
> the MVC pattern recommended here, keeping its `Board` and `Move` objects
> entirely free of rendering concerns.

### 3.2 Game Loop Pattern

The **Game Loop** is the backbone of the Stratego runtime. As documented by
[generalistprogrammer.com](https://generalistprogrammer.com/game-design-patterns)
and Robert Nystrom's *Game Programming Patterns*, every interactive game
requires a loop that:

1. **Processes input** – reads player/network events and queues them.
2. **Updates state** – applies queued commands; ticks the turn manager and
   any animations.
3. **Renders** – draws the current game state to screen.

For Stratego the loop is **fixed-timestep** at 60 FPS. Because the game is
turn-based, the `update()` phase is lightweight on most frames (no move is
pending); the loop's main cost per idle frame is rendering.

```
while game_running:
    process_input()   ← InputHandler gathers OS events; enqueues Commands
    update()          ← GameController applies pending Commands; fires Events
    render()          ← Renderer redraws changed board regions
    clock.tick(FPS)   ← cap to 60 FPS
```

**Why a fixed loop rather than event-driven?** A fixed loop simplifies
animation timing, ensures AI thinking time is bounded within a predictable
frame budget, and aligns with pygame's standard architecture. Pure
event-driven designs (no active loop) struggle with smooth animation.

### 3.3 Supporting Patterns

| Pattern | Where applied | Benefit | Source |
|---|---|---|---|
| **State Machine** | Game flow (Setup → Playing → Game Over) | Prevents illegal transitions | *Game Programming Patterns* ch. State |
| **Command** | Player moves, undo/redo support | Reversible actions, testability | *Game Programming Patterns* ch. Command |
| **Observer / Event Bus** | UI reacting to model changes | Loose coupling | generalistprogrammer.com |
| **Strategy** | AI difficulty levels | Swappable algorithms | GoF |
| **Repository** | Save / load game state | Decouples persistence format | DDD |
| **Game Loop** | Main application runtime | Consistent input → update → render | generalistprogrammer.com |
| **Object Pool** | UI animations, particle effects (v2.0) | Avoids GC pauses during combat animations | *Game Programming Patterns* ch. Object Pool |

> **Object Pool note (v1.0):** Stratego v1.0 has no real-time particle
> effects, so object pooling is low priority. It should be introduced in v2.0
> if combat animations spawn many short-lived sprites. Pre-allocating a pool
> of 50–100 sprite objects will eliminate garbage collection pauses that
> would cause frame drops during combat resolution.

---

## 3a. Anti-Patterns to Avoid

The following patterns are commonly misused in game development and must be
actively avoided in this project. These are highlighted by
[generalistprogrammer.com](https://generalistprogrammer.com/game-design-patterns)
and the game-development community as leading causes of unmaintainable
codebases.

| Anti-pattern | Description | How we avoid it |
|---|---|---|
| **God Object** | A single class that knows and does too much (e.g., a `Game` class that manages rules, rendering, AI, and persistence) | Strict layer architecture: each module has a single, narrow responsibility |
| **Spaghetti Code** | Over-complex, unstructured logic; tightly coupled systems that are impossible to test or extend independently | Enforce zero cross-layer imports; domain layer has no UI or I/O dependencies |
| **Singleton Overuse** | Using a single global instance for too many services, creating hidden dependencies and making unit testing impossible | No Singletons in the domain layer; dependency injection used instead. The Event Bus is the only application-layer shared service |
| **Deep Inheritance Hierarchies** | Modelling piece behaviours through many levels of subclassing (e.g., `Piece → MovablePiece → AttackingPiece → Scout`) | Composition over inheritance: use `dataclass` fields and `Rank` enum; special behaviour encoded in `combat.py` and `rules_engine.py`, not subclass overrides |
| **Tight Coupling to pygame** | Game logic directly calling pygame functions, making the domain layer untestable without a display | All pygame calls are confined to the Presentation Layer; domain layer uses only abstract data structures |

---

## 4. Layer Definitions

```mermaid
graph TB
    subgraph Presentation Layer
        PY_UI["pygame Renderer"]
        TERM_UI["Terminal Renderer (fallback)"]
    end

    subgraph Application Layer
        CTRL["Game Controller\n(input → commands)"]
        EVTBUS["Event Bus"]
    end

    subgraph Domain Layer
        ENGINE["Game Engine\n(rules, turn manager)"]
        BOARD["Board Model"]
        PIECES["Piece Models"]
        COMBAT["Combat Resolver"]
        STATE["Game State Machine"]
    end

    subgraph AI Layer
        AIORCH["AI Orchestrator"]
        MINIMAX["Minimax + Alpha-Beta"]
        MCTS["MCTS (optional)"]
        EVALFN["Evaluation Function"]
    end

    subgraph Infrastructure Layer
        PERSIST["Save/Load (JSON)"]
        NETW["Network Adapter (WebSocket)"]
        CONFIG["Config / Settings"]
    end

    Presentation Layer --> Application Layer
    Application Layer --> Domain Layer
    AI Layer --> Domain Layer
    Domain Layer --> Infrastructure Layer
```

### Layer Responsibilities

**Presentation Layer**
- Renders game board, pieces (visible/hidden), and UI chrome.
- Translates raw OS input events to abstract game actions (e.g., `SelectPiece`,
  `MovePiece`).
- Contains zero game-logic.

**Application Layer (Controller)**
- Receives abstract actions and dispatches Commands to the Domain Layer.
- Manages turn sequencing and player-type routing (human vs. AI vs. network).
- Publishes domain events to the Event Bus.

**Domain Layer**
- The authoritative source of game rules and state.
- Stateless rules engine where possible (functions that receive state and return
  new state or errors).
- Exposes a clean API consumed by the Application Layer and AI Layer.

**AI Layer**
- Implements computer opponents as Strategy implementations.
- Reads game state via domain models; does not directly mutate state.
- Communicates decisions as `Move` value objects back to the Controller.

**Infrastructure Layer**
- Handles all I/O: disk, network, configuration.
- Adapters follow the repository / adapter pattern so the domain layer never
  depends on concrete I/O libraries.

---

## 5. Key Architectural Decisions (Summary)

Full ADRs are in [`adr/`](./adr/).

| # | Decision | Rationale |
|---|---|---|
| ADR-001 | Python 3.12 | Latest stable; `match` statements simplify combat resolution; `dataclasses` + type hints improve model clarity |
| ADR-002 | MVC + Event Bus over ECS | Turn-based game with small entity count; MVC is simpler, more testable; ECS adds complexity without performance benefit |
| ADR-003 | Immutable `GameState` snapshots | AI search safety; free undo/redo; simple persistence; precedent from python-chess |
| ADR-004 | JSON for save games | Human-readable, debuggable, no external dependencies; `pickle` explicitly rejected – code-execution security risk |
| ADR-005 | Minimax + alpha-beta for AI | Proven for two-player zero-sum games; Stratego's hidden-information handled via determinised MCTS in phase 2 |

---

## 6. Quality Attribute Goals

| Attribute | Goal | Design approach |
|---|---|---|
| **Testability** | ≥ 80 % domain-layer coverage | Domain layer has zero I/O dependencies |
| **Extensibility** | New AI strategies, renderers without core changes | Strategy pattern, dependency inversion |
| **Performance** | AI move < 1 s at depth-6 | Alpha-beta pruning, bitboard representation |
| **Maintainability** | Clear module ownership | Strict layer discipline; no cross-layer imports |
| **Portability** | Runs on Windows, macOS, Linux | Pure Python + pygame (all cross-platform) |

---

## 7. Folder Structure (Target)

```
stratego/
├── specifications/          ← Architecture documents (this folder)
│   ├── architecture_overview.md
│   ├── system_design.md
│   ├── game_components.md
│   ├── data_models.md
│   ├── technology_stack.md
│   ├── ai_strategy.md
│   └── adr/
│       ├── ADR-001-python-version.md
│       └── ...
├── src/
│   ├── domain/              ← Game Engine, Board, Piece, Combat, State Machine
│   ├── application/         ← Controller, Event Bus, Command objects
│   ├── ai/                  ← AI Orchestrator, Minimax, MCTS
│   ├── presentation/        ← pygame Renderer, Terminal Renderer
│   └── infrastructure/      ← Persistence, Network Adapter, Config
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 8. Out of Scope (v1.0)

- Online multiplayer (planned for v2.0 – see `system_design.md`).
- Mobile / web front-end.
- Account management or leaderboards.
- Tournament mode.

---

## 9. Related Documents

| Document | Purpose |
|---|---|
| [`system_design.md`](./system_design.md) | Detailed module-level design |
| [`game_components.md`](./game_components.md) | Game rule encoding and component breakdown |
| [`data_models.md`](./data_models.md) | Domain model definitions and relationships |
| [`technology_stack.md`](./technology_stack.md) | Library choices and justifications |
| [`ai_strategy.md`](./ai_strategy.md) | AI algorithm selection and design |

---

## 10. Key Sources and Industry References

| Source | Relevance |
|---|---|
| [generalistprogrammer.com – Game Design Patterns](https://generalistprogrammer.com/game-design-patterns) | Game Loop, Component, ECS, Observer, Object Pool, Singleton anti-pattern; scalable architecture principles |
| Robert Nystrom – *Game Programming Patterns* (gameprogrammingpatterns.com) | Canonical reference for Command, State, Game Loop, Update Method, Object Pool, Singleton (with cautions) |
| python-chess (GitHub) | Production Python game library demonstrating model-first, renderer-agnostic MVC design |
| *Master of the Flag* – Stankiewicz et al. (2011) | Computer Stratego Championship winner; basis for ISMCTS AI recommendation |
| *Opponent Modelling in Stratego* – de Boer et al. (2007) | Piece value weights and probability-tracking approach for hidden-information Stratego AI |

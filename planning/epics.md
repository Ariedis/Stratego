# Stratego – Epic Catalogue

**Document type:** Backlog – Epics  
**Version:** 1.0  
**Author:** Senior Business Analyst (Python Game Specialist)  
**Status:** Approved  
**Specification refs:** [`architecture_overview.md`](../specifications/architecture_overview.md),
[`system_design.md`](../specifications/system_design.md)

---

## Summary Table

| ID | Epic | Priority | Phase | Features |
|---|---|---|---|---|
| EPIC-1 | Project Foundation | Must Have | 1 | F-1.1 – F-1.4 |
| EPIC-2 | Domain Layer – Core Game Rules | Must Have | 2 | F-2.1 – F-2.6 |
| EPIC-3 | Application Layer | Must Have | 3 | F-3.1 – F-3.7 |
| EPIC-4 | Presentation Layer | Must Have | 4 | F-4.1 – F-4.11 |
| EPIC-5 | AI Layer | Must Have | 5 | F-5.1 – F-5.5 |
| EPIC-6 | Infrastructure | Must Have | 6 | F-6.1 – F-6.3 |
| EPIC-7 | Custom Armies & Polish | Should Have | 7 | F-7.1 – F-7.6 |
| EPIC-8 | Unit Task Popup | Should Have | 8 | F-8.1 – F-8.9 |

---

# Epic: Project Foundation

**ID:** EPIC-1  
**Priority:** Must Have  
**Specification refs:** [`architecture_overview.md §7`](../specifications/architecture_overview.md),
[`technology_stack.md`](../specifications/technology_stack.md),
[`data_models.md`](../specifications/data_models.md)  
**Summary:** Establish the project skeleton, toolchain, and all core domain
enumerations and dataclass models that every subsequent epic depends on.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-1.1 | Project scaffolding (uv, pyproject.toml, folder structure) | Must Have |
| F-1.2 | Domain enumerations (Rank, PlayerSide, PlayerType, GamePhase, TerrainType, MoveType, CombatOutcome) | Must Have |
| F-1.3 | Core value-object dataclasses (Position, Square, Board, Piece, Player, Move, MoveRecord, CombatResult, GameState) | Must Have |
| F-1.4 | Test infrastructure (pytest, ruff, mypy configuration) | Must Have |

## Assumptions

- Python 3.12 is installed and available as the runtime (ADR-001).
- `uv` is used for dependency management (`technology_stack.md §8`).

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Python version mismatch on developer machines | Low | Med | Pin Python version in `pyproject.toml` and document in README |
| Incorrect `Rank.BOMB` integer value (should be 99, not 11) | Low | High | Enforce via unit test; document in code comment |

---

# Epic: Domain Layer – Core Game Rules

**ID:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md`](../specifications/game_components.md),
[`data_models.md`](../specifications/data_models.md)  
**Summary:** Implement the complete, tested Stratego rules engine so that all
game logic is correct and independently verifiable without any UI dependency.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-2.1 | Board construction: 10×10 grid, lake squares, neighbour queries | Must Have |
| F-2.2 | Movement validation: normal pieces (1 square), immovable pieces (Bomb/Flag), two-square rule | Must Have |
| F-2.3 | Scout movement: any number of squares in one direction; blocked by pieces and lakes | Must Have |
| F-2.4 | Combat resolution: general rank comparison + special cases (Spy/Marshal, Miner/Bomb, Flag capture) | Must Have |
| F-2.5 | Win condition detection: Flag capture, no legal moves | Must Have |
| F-2.6 | Setup phase validation: zone boundaries, all 40 pieces placed | Must Have |

## Assumptions

- Lake squares are at the fixed positions defined in `game_components.md §2.2`.
- The two-square rule is enforced (variant rule that prevents AI stalling).

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Edge case in Spy rule (Spy defending vs Spy attacking) | Med | High | Explicit unit test for both directions |
| Scout movement incorrectly allowing diagonal moves | Low | High | Parametrised unit tests covering all 8 directions |
| Two-square rule too strict, blocking valid play | Med | Med | Review against official Stratego rules PDF |

---

# Epic: Application Layer

**ID:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.2, §3, §4, §5, §6, §7`](../specifications/system_design.md)  
**Summary:** Wire the domain layer into a runnable game loop with commands,
events, turn management, and a screen stack – without any pygame dependency.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-3.1 | Command objects (PlacePiece, MovePiece) | Must Have |
| F-3.2 | Event Bus: publish/subscribe with typed events | Must Have |
| F-3.3 | Game Controller: routes commands to domain, publishes events | Must Have |
| F-3.4 | Turn Manager: alternates players, triggers AI when AI's turn | Must Have |
| F-3.5 | Game Loop: fixed-rate process_input → update → render at 60 FPS | Must Have |
| F-3.6 | Screen Manager: push/pop/replace screen stack | Should Have |
| F-3.7 | Session lifecycle management | Should Have |

## Assumptions

- The Game Loop runs in the main thread; AI search runs in a `ThreadPoolExecutor` worker thread.
- The Event Bus is synchronous within a single frame.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI thread producing a result while main thread is mid-update | Med | High | Use `concurrent.futures.Future`; collect result at the top of `update()` before processing other commands |
| Event Bus subscriber raising an exception blocking other subscribers | Med | Med | Wrap subscriber callbacks in try/except; log and continue |

---

# Epic: Presentation Layer

**ID:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`screen_flow.md`](../specifications/screen_flow.md),
[`system_design.md §2.4`](../specifications/system_design.md),
[`game_components.md §3.2`](../specifications/game_components.md)  
**Summary:** Deliver a fully playable human-vs-human game through the pygame UI
with all eight screens functional and fog-of-war correctly applied.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-4.1 | pygame Renderer: board grid, lakes, piece sprites | Must Have |
| F-4.2 | Input Handler: mouse events → abstract InputEvent | Must Have |
| F-4.3 | Fog-of-war: opponent pieces rendered hidden until revealed | Must Have |
| F-4.4 | MainMenuScreen with Continue/Load/Settings buttons | Must Have |
| F-4.5 | SetupScreen: drag-and-drop piece placement, Auto-arrange, Clear, Ready | Must Have |
| F-4.6 | PlayingScreen: board + side panel + controls bar | Must Have |
| F-4.7 | GameOverScreen: winner, winning condition, turn count | Must Have |
| F-4.8 | Terminal Renderer: ASCII board for headless testing | Should Have |
| F-4.9 | StartGameScreen: mode and difficulty selection | Must Have |
| F-4.10 | LoadGameScreen: save file browser | Should Have |
| F-4.11 | SettingsScreen: display and game-play preferences | Should Have |

## Assumptions

- pygame-ce 2.x is available in the project dependencies.
- pygame-gui 0.6.x is used for menus and dialogs.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fog-of-war leaking opponent rank to the renderer | Med | High | Unit test: render from Player 2 perspective and assert all Player 1 unrevealed pieces show no rank |
| Drag-and-drop on Setup Screen dropping pieces outside valid zones | Med | Med | Snap to valid grid squares only; reject drops outside setup zone |

---

# Epic: AI Layer

**ID:** EPIC-5  
**Priority:** Must Have  
**Specification refs:** [`ai_strategy.md`](../specifications/ai_strategy.md)  
**Summary:** Deliver a working computer opponent at three difficulty levels
using minimax with alpha-beta pruning, opening book, and a probability tracker
for hidden-information reasoning.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-5.1 | Evaluation function: material + mobility + flag safety + information advantage | Must Have |
| F-5.2 | Minimax with alpha-beta pruning and move ordering | Must Have |
| F-5.3 | AI Orchestrator: difficulty routing, time-limit enforcement | Must Have |
| F-5.4 | Opening book: 3 strategies (Blitz, Fortress, Probe) at all difficulty levels | Should Have |
| F-5.5 | Probability Tracker: Bayesian updates for unrevealed opponent pieces | Should Have |

## Assumptions

- MCTS (phase 2) is out of scope for v1.0.
- Search depth is configurable via `config.yaml`.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hard AI exceeds 950 ms time budget | Med | Med | Implement iterative deepening; return best move found when time limit hit |
| AI selects illegal move after determinisation | Low | High | Rules engine validates every AI move; orchestrator retries up to 3 times |
| Probability Tracker becoming inconsistent after many updates | Med | Med | Add invariant: probability distribution must always sum to 1.0; assert in tests |

---

# Epic: Infrastructure

**ID:** EPIC-6  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.5`](../specifications/system_design.md),
[`data_models.md §6`](../specifications/data_models.md),
[`technology_stack.md §7, §8`](../specifications/technology_stack.md)  
**Summary:** Implement all I/O concerns: JSON save/load with version
validation, configuration from `config.yaml`, and structured logging.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-6.1 | JSON save/load: serialise/deserialise GameState with version field | Must Have |
| F-6.2 | Config loader: load config.yaml with hardcoded defaults | Must Have |
| F-6.3 | Structured logger: wraps Python logging, file + console output | Should Have |

## Assumptions

- Save files are stored in `~/.stratego/saves/` by default.
- `pickle` is never used (enforced by `ruff` rule S301 and ADR-004).

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Save file schema evolving and breaking old saves | Low | High | Version field in every save file; migration logic in `json_repository.py` |
| Config file written by older version loaded by newer version | Low | Med | Use default values for any missing config keys |

---

# Epic: Custom Armies & Polish

**ID:** EPIC-7  
**Priority:** Should Have  
**Specification refs:** [`custom_armies.md`](../specifications/custom_armies.md),
[`screen_flow.md §3.3`](../specifications/screen_flow.md)  
**Summary:** Deliver the custom army mod system allowing players to replace
piece names and images, and complete end-to-end integration testing.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-7.1 | Built-in Classic army (hard-coded ArmyMod, always first in list) | Must Have |
| F-7.2 | Mod loader: discover and parse army.json files in mod directory | Should Have |
| F-7.3 | Mod validator: validate manifest fields, length limits, version check | Should Have |
| F-7.4 | Sprite manager (mod-aware): image resolution priority, GIF animation | Should Have |
| F-7.5 | ArmySelectScreen: dropdowns, preview panel, army data flow to SetupScreen | Should Have |
| F-7.6 | Integration test suite (full game session, save/load cycle) | Must Have |

## Assumptions

- Mods affect presentation only; domain layer requires no changes.
- Animated GIF support requires frame extraction at load time.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Path traversal in mod image filenames | Low | High | Resolve all paths relative to mod folder; reject absolute paths |
| Malformed image file crashing SpriteManager | Med | Med | Wrap image loading in try/except; fall back to Classic image |
| Two mods with same folder name | Low | Med | Log warning; skip second mod; unique ID enforced by directory name |

---

# Epic: Unit Task Popup

**ID:** EPIC-8  
**Priority:** Should Have  
**Specification refs:** [`ux-wireframe-task-popup.md`](./ux-wireframe-task-popup.md),
[`ux-user-journeys-task-popup.md`](./ux-user-journeys-task-popup.md),
[`custom_armies.md §4`](../specifications/custom_armies.md),
[`screen_flow.md §3.7`](../specifications/screen_flow.md)  
**Summary:** Deliver the Unit Task Popup feature, which pauses the game after
a custom-army unit captures an enemy piece and displays a physical task that
the captured human player must acknowledge before play resumes.

## Features

| ID | Feature | Priority |
|----|---------|----------|
| F-8.1 | `UnitTask` domain value object + `tasks` field on `UnitCustomisation` | Must Have |
| F-8.2 | Army.json task parsing and validation (description length, image path safety) | Must Have |
| F-8.3 | `TaskPopupOverlay` visual layout (scrim, card, heading, image panel, text panel, Complete button) | Must Have |
| F-8.4 | Task popup trigger and dismissal logic (CombatResolved event, player-type checks, random task selection) | Must Have |
| F-8.5 | Input blocking, entrance/exit animation, and keyboard navigation | Must Have |
| F-8.6 | Animated GIF playback within the popup image panel | Should Have |
| F-8.7 | Army Select Screen tasks notification (ℹ notice in preview panel) | Must Have |
| F-8.8 | Post-dismissal last-move re-highlight (2 s, COLOUR_MOVE_LAST colours) | Should Have |
| F-8.9 | 2-player local handover prompt in popup heading row | Should Have |

## Assumptions

- Tasks are a presentation-layer concern; no domain rules change.
- The `CombatResolved` event already carries both the winning and losing unit references.
- `SpriteManager` pre-extracts GIF frames at mod-load time (existing behaviour per US-704).
- The popup is suppressed for AI captured players; the AI cannot perform physical tasks.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Path traversal via `tasks[n].image` in `army.json` | Low | High | Validate: absolute paths and `..` segments rejected per `custom_armies.md §10` and US-802 |
| Task popup shown to wrong player in vs-AI mode | Med | High | Trigger condition must verify `captured_player.player_type == PlayerType.HUMAN` before showing popup |
| GIF animation stuttering due to large file (> 2 MB) | Med | Low | Pre-extract frames at load; warn in mod docs; decouple popup frame timer from main game loop |
| Player dismisses popup without completing the task | High | Low | Social/trust-based enforcement; Could Have: minimum dwell timer (`ux-wireframe-task-popup.md §13 Q1`) |

# Stratego – Prioritised Product Backlog

**Document type:** Backlog  
**Version:** 1.0  
**Author:** Senior Business Analyst (Python Game Specialist)  
**Status:** Approved  
**Specification refs:** All documents in [`/specifications/`](../specifications/)

---

## MoSCoW Key

| Priority | Meaning |
|---|---|
| **M** – Must Have | Critical; product cannot ship without this |
| **S** – Should Have | High value; include if possible |
| **C** – Could Have | Nice-to-have; include if time allows |
| **W** – Won't Have (v1.0) | Explicitly deferred to v2.0 |

---

## Phase 1 – Project Foundation

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-1.1 | Project scaffolding: uv, pyproject.toml, src/domain/, src/application/, src/ai/, src/presentation/, src/infrastructure/, tests/ | M | EPIC-1 | `architecture_overview.md §7` |
| F-1.2 | Domain enumerations: Rank (FLAG=0…MARSHAL=10, BOMB=99), PlayerSide, PlayerType, GamePhase, TerrainType, MoveType, CombatOutcome | M | EPIC-1 | `data_models.md §3` |
| F-1.3 | Core dataclasses: Position, Square, Board, Piece, Player, Move, MoveRecord, CombatResult, GameState (all frozen=True) | M | EPIC-1 | `data_models.md §2–§5` |
| F-1.4 | Test infrastructure: pytest 8.x, pytest-cov, pytest-mock, mypy --strict, ruff configured | M | EPIC-1 | `technology_stack.md §5–§6` |

---

## Phase 2 – Core Game Rules

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-2.1 | Board: 10×10 grid, lake detection, neighbour traversal, setup-zone boundaries | M | EPIC-2 | `game_components.md §2` |
| F-2.2a | Movement: normal piece moves exactly 1 square orthogonally; diagonal rejected | M | EPIC-2 | `game_components.md §4.1` |
| F-2.2b | Movement: Bomb and Flag movement attempts rejected with RulesViolationError | M | EPIC-2 | `game_components.md §4.3` |
| F-2.2c | Two-square rule: back-and-forth more than twice consecutively is rejected | M | EPIC-2 | `game_components.md §4.4` |
| F-2.3 | Scout movement: any distance in one orthogonal direction; blocked by intervening pieces or lakes | M | EPIC-2 | `game_components.md §4.2` |
| F-2.4a | Combat: attacker rank > defender rank → attacker wins; defender removed | M | EPIC-2 | `game_components.md §5.1` |
| F-2.4b | Combat: equal ranks → both removed (draw) | M | EPIC-2 | `game_components.md §5.1` |
| F-2.4c | Combat: Spy attacks Marshal → Spy wins | M | EPIC-2 | `game_components.md §5.2` |
| F-2.4d | Combat: Miner attacks Bomb → Miner wins | M | EPIC-2 | `game_components.md §5.2` |
| F-2.4e | Combat: any piece attacks Bomb (non-Miner) → attacker loses | M | EPIC-2 | `game_components.md §5.2` |
| F-2.4f | Combat: any piece attacks Flag → attacker wins; game ends | M | EPIC-2 | `game_components.md §5.2` |
| F-2.4g | Combat: post-combat both pieces permanently revealed | M | EPIC-2 | `game_components.md §5.3` |
| F-2.5a | Win: Flag captured → GAME_OVER with correct winner | M | EPIC-2 | `game_components.md §6` |
| F-2.5b | Win: player has no legal moves → GAME_OVER, opponent wins | M | EPIC-2 | `game_components.md §6` |
| F-2.5c | Draw: turn counter ≥ 3 000 half-moves → GAME_OVER, no winner | S | EPIC-2 | `game_components.md §6` |
| F-2.6 | Setup validation: pieces placed only in own rows (Red: 6–9, Blue: 0–3); exactly 40 per player | M | EPIC-2 | `game_components.md §7` |

---

## Phase 3 – Application Layer

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-3.1 | Command objects: PlacePiece(pos, piece), MovePiece(from_pos, to_pos) as frozen dataclasses | M | EPIC-3 | `system_design.md §2.2` |
| F-3.2 | Event Bus: subscribe(event_type, callback), publish(event) with typed events | M | EPIC-3 | `system_design.md §7` |
| F-3.3 | Game Controller: submit_command() validates via RulesEngine, updates GameState, publishes events | M | EPIC-3 | `system_design.md §4` |
| F-3.4 | Turn Manager: alternates active_player; fires TurnChanged event; routes to AI for AI players | M | EPIC-3 | `system_design.md §2.2` |
| F-3.5 | Game Loop: process_input → update → render cycle at 60 FPS; AI future collected in update() | M | EPIC-3 | `system_design.md §3` |
| F-3.6 | Screen Manager: push/pop/replace stack; on_exit() → on_enter(data) data passing | S | EPIC-3 | `screen_flow.md §4` |
| F-3.7 | Session: initialise new game, manage lifecycle (new/load/save/end) | S | EPIC-3 | `system_design.md §2.2` |

---

## Phase 4 – Presentation Layer

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-4.1 | pygame Renderer: 10×10 board, lake highlight, piece sprites at correct positions | M | EPIC-4 | `system_design.md §2.4` |
| F-4.2 | Input Handler: left-click select, left-click move, right-click deselect → InputEvent objects | M | EPIC-4 | `system_design.md §2.4` |
| F-4.3 | Fog-of-war: opponent pieces rendered face-down; only revealed pieces show rank | M | EPIC-4 | `game_components.md §3.2` |
| F-4.4 | MainMenuScreen: Start Game, Continue (greyed if no save), Load Game, Settings, Quit | M | EPIC-4 | `screen_flow.md §3.1` |
| F-4.5 | SetupScreen: piece tray, drag-and-drop to valid zone, Auto-arrange, Clear, Ready button | M | EPIC-4 | `screen_flow.md §3.6` |
| F-4.6 | PlayingScreen: board area, side panel (active player, captured pieces, turn counter), Save/Quit/Undo bar | M | EPIC-4 | `screen_flow.md §3.7` |
| F-4.7 | GameOverScreen: winner name, winning condition, total turn count, Play Again / Main Menu / Quit | M | EPIC-4 | `screen_flow.md §3.8` |
| F-4.8 | Terminal Renderer: ASCII board for headless CI testing | S | EPIC-4 | `system_design.md §2.4` |
| F-4.9 | StartGameScreen: 2-player / vs AI toggle, AI difficulty selector | M | EPIC-4 | `screen_flow.md §3.2` |
| F-4.10 | LoadGameScreen: scrollable save list (newest-first), Load/Delete/Back | S | EPIC-4 | `screen_flow.md §3.4` |
| F-4.11 | SettingsScreen: resolution, fullscreen, FPS cap, sound, music, mod folder; persists to config.yaml | S | EPIC-4 | `screen_flow.md §3.5` |

---

## Phase 5 – AI Layer

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-5.1a | Evaluation: material score (piece value weights per ai_strategy.md §6.2) | M | EPIC-5 | `ai_strategy.md §6` |
| F-5.1b | Evaluation: mobility score (count of legal moves) | M | EPIC-5 | `ai_strategy.md §6.1` |
| F-5.1c | Evaluation: flag safety score (distance from closest enemy moveable piece to Flag) | M | EPIC-5 | `ai_strategy.md §6.1` |
| F-5.1d | Evaluation: information advantage score (penalty for unknown opponent pieces) | S | EPIC-5 | `ai_strategy.md §6.1` |
| F-5.2a | Minimax: recursive alpha-beta pruning to configurable depth | M | EPIC-5 | `ai_strategy.md §4.2` |
| F-5.2b | Move ordering: captures first (highest value first), then flag-approach, probe, other | M | EPIC-5 | `ai_strategy.md §7` |
| F-5.3 | AI Orchestrator: routes to correct depth by difficulty; enforces time_limit_ms; retries on illegal move (max 3) | M | EPIC-5 | `ai_strategy.md §8` |
| F-5.4a | Opening book: Fortress setup (Flag in back corner, Bombs around, Miners mid-board) | S | EPIC-5 | `ai_strategy.md §4.1` |
| F-5.4b | Opening book: Blitz setup (Scouts and high-rank pieces rush centre) | S | EPIC-5 | `ai_strategy.md §4.1` |
| F-5.4c | Opening book: Probe setup (Scouts advance first) | C | EPIC-5 | `ai_strategy.md §4.1` |
| F-5.5 | Probability Tracker: tracks possible_ranks per unrevealed piece; updates on move/combat/reveal events | S | EPIC-5 | `ai_strategy.md §5` |

---

## Phase 6 – Infrastructure

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-6.1a | JSON save: serialise full GameState to JSON with version="1.0" field | M | EPIC-6 | `data_models.md §6` |
| F-6.1b | JSON load: deserialise GameState; validate version; reject unknown versions | M | EPIC-6 | `data_models.md §6` |
| F-6.1c | JsonRepository.get_most_recent_save(): returns path or None | M | EPIC-6 | `screen_flow.md §6` |
| F-6.1d | Autosave every N turns (configurable via config.yaml) | S | EPIC-6 | `system_design.md §8` |
| F-6.2 | Config loader: reads config.yaml; falls back to hardcoded defaults if file missing | M | EPIC-6 | `system_design.md §8` |
| F-6.3 | Logger: structured logging to file and console; wraps Python logging | S | EPIC-6 | `system_design.md §2.5` |

---

## Phase 7 – Custom Armies & Polish

| ID | Feature | Priority | Epic | Spec ref |
|---|---|---|---|---|
| F-7.1 | Classic army: hard-coded ArmyMod in src/domain/classic_army.py; always first in list | M | EPIC-7 | `custom_armies.md §8` |
| F-7.2 | Mod loader: discover subdirectories in mod_directory; parse army.json | S | EPIC-7 | `custom_armies.md §6` |
| F-7.3 | Mod validator: check mod_version=="1.0", army_name 1–64 chars, display_name 1–32 chars | S | EPIC-7 | `custom_armies.md §4.3` |
| F-7.4a | Sprite manager: image resolution priority (mod → built-in) | S | EPIC-7 | `custom_armies.md §5` |
| F-7.4b | Sprite manager: GIF animation (frame extraction, frame timer driven by delta_time) | C | EPIC-7 | `custom_armies.md §5.1` |
| F-7.5 | ArmySelectScreen: dropdown per player, preview panel, Confirm/Back | S | EPIC-7 | `screen_flow.md §3.3` |
| F-7.6 | Integration tests: full game session, save/load cycle, army mod loading | M | EPIC-7 | All specs |

---

## Won't Have (v1.0)

| ID | Feature | Deferred to |
|---|---|---|
| W-1 | Online multiplayer (WebSocket) | v2.0 |
| W-2 | MCTS / ISMCTS AI | v2.0 |
| W-3 | Mod marketplace | v2.0 |
| W-4 | Board skin mods | v2.0 |
| W-5 | Sound packs | v2.0 |
| W-6 | Mobile / web front-end | v2.0 |
| W-7 | Tournament mode | v2.0 |
| W-8 | Account management / leaderboards | v2.0 |
| W-9 | Undo/redo (beyond tracking move_history) | v2.0 |

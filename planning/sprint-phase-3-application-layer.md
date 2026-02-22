# Sprint Plan – Phase 3: Application Layer

**Phase:** 3  
**Duration:** 2 weeks (Sprints 6–7)  
**Exit criteria:** Game loop runs headlessly; commands dispatch, events fire, turns alternate correctly  
**Epic:** EPIC-3  
**Specification refs:** [`system_design.md §2.2, §3, §4, §5, §6, §7`](../specifications/system_design.md),
[`screen_flow.md §4`](../specifications/screen_flow.md)

---

## Sprint 6 (Week 6): Commands, Events, and Game Controller

**Goal:** Command/event plumbing wired; controller routes moves to domain layer.

### Tasks

---

#### TASK-301: Implement command objects

**User story:** US-301  
**Module:** `src/application/commands.py`  
**Depends on:** TASK-104

**Input:** `system_design.md §2.2`  
**Output:** `PlacePiece` and `MovePiece` frozen dataclasses

**Steps:**

1. Create `src/application/commands.py`.
2. Define `@dataclass(frozen=True) class PlacePiece` with fields:
   `piece: Piece`, `pos: Position`.
3. Define `@dataclass(frozen=True) class MovePiece` with fields:
   `from_pos: Position`, `to_pos: Position`.
4. Define `Command = Union[PlacePiece, MovePiece]` type alias.
5. Write `tests/unit/application/test_commands.py` verifying immutability
   and equality.

**Test cases to cover:**

- `PlacePiece` and `MovePiece` are immutable.
- Two instances with same field values are `==`.

---

#### TASK-302: Implement Event Bus and domain events

**User story:** US-302  
**Module:** `src/application/event_bus.py`, `src/application/events.py`  
**Depends on:** TASK-104

**Input:** `system_design.md §7`  
**Output:** Publish/subscribe Event Bus with all 8 event types

**Steps:**

1. Create `src/application/events.py`. Define all 8 frozen event dataclasses:
   - `PiecePlaced(pos, piece)`
   - `PieceMoved(from_pos, to_pos, piece)`
   - `CombatResolved(attacker, defender, winner: PlayerSide | None)`
   - `TurnChanged(active_player: PlayerSide)`
   - `GameOver(winner: PlayerSide | None, reason: str)`
   - `InvalidMove(player: PlayerSide, move: Move, reason: str)`
   - `GameSaved(filepath: str)`
   - `GameLoaded(game_state: GameState)`
2. Create `src/application/event_bus.py`.
3. Define `EventBus` class with:
   - `subscribe(event_type: type, callback: Callable) -> None`
   - `unsubscribe(event_type: type, callback: Callable) -> None`
   - `publish(event: Any) -> None` (dispatches to all registered callbacks
     for the event type; catches and logs exceptions per callback)
4. Write `tests/unit/application/test_event_bus.py`.

**Test cases to cover:**

- Subscriber receives event exactly once.
- No error when publishing to type with no subscribers.
- One failing subscriber does not block others.
- `unsubscribe` stops future delivery.

---

#### TASK-303: Implement Game Controller

**User story:** US-303  
**Module:** `src/application/game_controller.py`  
**Depends on:** TASK-301, TASK-302, TASK-202

**Input:** `system_design.md §4`  
**Output:** `GameController.submit_command()` routing to domain layer

**Steps:**

1. Create `src/application/game_controller.py`.
2. Define `GameController.__init__(initial_state, event_bus, rules_engine)`.
3. Implement `submit_command(cmd: Command) -> None`:
   - For `PlacePiece`: call `rules_engine.validate_placement()`. If valid,
     call `rules_engine.apply_placement()`, update `self._state`, publish
     `PiecePlaced`. If invalid, publish `InvalidMove`.
   - For `MovePiece`: call `rules_engine.validate_move()`. If valid, call
     `rules_engine.apply_move()`, update `self._state`, publish `PieceMoved`
     and (if combat) `CombatResolved`. If `GAME_OVER`, publish `GameOver`.
     If invalid, publish `InvalidMove`.
4. Expose `current_state: GameState` property (read-only).
5. Write `tests/unit/application/test_game_controller.py` using `pytest-mock`
   to mock `event_bus.publish` and verify correct events.

**Example:**

```python
controller.submit_command(MovePiece(from_pos=Pos(6,4), to_pos=Pos(5,4)))
mock_event_bus.publish.assert_called_once_with(PieceMoved(...))
assert controller.current_state.turn_number == 1
```

**Test cases to cover:**

- Valid move: state updated, `PieceMoved` published.
- Invalid move: state unchanged, `InvalidMove` published.
- Combat move: `CombatResolved` published.
- Flag capture: `GameOver` published.

---

## Sprint 7 (Week 7): Turn Manager, Game Loop, and Screen Manager

**Goal:** Full application layer runnable headlessly with turn alternation.

### Tasks

---

#### TASK-304: Implement Turn Manager

**User story:** US-304  
**Module:** `src/application/turn_manager.py`  
**Depends on:** TASK-303

**Input:** `system_design.md §2.2, §5`  
**Output:** `TurnManager` with AI dispatch

**Steps:**

1. Create `src/application/turn_manager.py`.
2. Define `TurnManager.__init__(game_controller, event_bus, ai_orchestrator)`.
3. Subscribe to `TurnChanged` events on the `event_bus`.
4. On `TurnChanged(player)`:
   - If `player.player_type in (AI_EASY, AI_MEDIUM, AI_HARD)`:
     submit AI move request to `ThreadPoolExecutor` → store `Future`.
5. Implement `collect_ai_result() -> None`:
   - If stored `Future.done()`, get the move and call
     `game_controller.submit_command(MovePiece(...))`.
   - If the move is rejected, retry up to 3 times.
   - After 3 failures, log `CRITICAL` error.
6. This method is called from the game loop's `update()` phase.
7. Write `tests/unit/application/test_turn_manager.py` with mocked AI.

**Test cases to cover:**

- `TurnChanged(BLUE)` triggers AI request when Blue is AI type.
- `TurnChanged(RED)` does nothing when Red is Human.
- AI future collected in `collect_ai_result()`.
- Retry logic on illegal AI move.

---

#### TASK-305: Implement Game Loop

**User story:** US-305  
**Module:** `src/application/game_loop.py`  
**Depends on:** TASK-303, TASK-304

**Input:** `system_design.md §3`  
**Output:** `GameLoop` running `process_input → update → render`

**Steps:**

1. Create `src/application/game_loop.py`.
2. Define `GameLoop.__init__(controller, renderer, clock, screen_manager)`.
3. Implement `run(max_frames: int | None = None) -> None`:
   ```python
   while running:
       self._process_input()
       self._update()
       self._render()
       self._clock.tick(FPS)
       if max_frames and frame_count >= max_frames:
           break
   ```
4. `_process_input()`: Poll `pygame.event.get()` (or mock in tests);
   pass to `screen_manager.current().handle_event()`.
5. `_update()`: Call `turn_manager.collect_ai_result()`;
   call `screen_manager.current().update(delta_time)`.
6. `_render()`: Call `renderer.render(controller.current_state)`.
7. Accept a `clock` abstraction (not directly `pygame.Clock`) for testability.
8. Write `tests/unit/application/test_game_loop.py` with mocked renderer.

**Test cases to cover:**

- Loop runs exactly `max_frames` iterations.
- `process_input → update → render` order never violated.
- No crash on 10 frames with no input (headless).

---

#### TASK-306: Implement Screen Manager

**User story:** US-306  
**Module:** `src/application/screen_manager.py`,
`src/presentation/screens/base.py`  
**Depends on:** TASK-305

**Input:** `screen_flow.md §4`  
**Output:** `ScreenManager` with push/pop/replace; `Screen` abstract base class

**Steps:**

1. Create `src/presentation/screens/base.py` with abstract `Screen` class:
   - Abstract methods: `on_enter(data: dict)`, `on_exit() -> dict`,
     `render(surface)`, `handle_event(event)`, `update(delta_time: float)`.
2. Create `src/application/screen_manager.py` with `ScreenManager`:
   - `push(screen, data={})`: calls `screen.on_enter(data)`; adds to stack.
   - `pop()`: calls `current.on_exit()`; removes from stack;
     calls previous screen's `on_enter(returned_data)`.
   - `replace(screen, data={})`: pops current (discarding return data);
     pushes new screen.
   - `current() -> Screen`: returns top of stack.
   - `render(surface)`: delegates to `current().render(surface)`.
   - `handle_event(event)`: delegates to `current().handle_event(event)`.
3. Write `tests/unit/application/test_screen_manager.py`.

**Test cases to cover:**

- `push/pop` stack LIFO order.
- `on_exit()` data passed to `on_enter()` of previous screen.
- `replace()` swaps top of stack without growing it.

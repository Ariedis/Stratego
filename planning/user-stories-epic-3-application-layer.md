# EPIC-3: Application Layer – User Stories

**Epic:** EPIC-3  
**Phase:** 3  
**Specification refs:** [`system_design.md §2.2, §3, §4, §5, §6, §7`](../specifications/system_design.md),
[`screen_flow.md §4`](../specifications/screen_flow.md)

---

## US-301: Command Objects

**Epic:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.2`](../specifications/system_design.md)

**As a** developer,  
**I want** all player actions encoded as immutable `Command` value objects,  
**so that** actions are self-describing, testable in isolation, and support
future undo/redo without mutable state.

### Acceptance Criteria

- [ ] **AC-1:** Given `PlacePiece(piece=scout, pos=Position(6,4))`, When
      attempting mutation (`cmd.pos = Position(7,4)`), Then `FrozenInstanceError`.
- [ ] **AC-2:** Given `MovePiece(from_pos=Position(6,4), to_pos=Position(5,4))`,
      When compared to an identical instance, Then `==` returns `True`.
- [ ] **AC-3:** Given a command, When `repr(cmd)`, Then the output includes
      all field names and values (dataclass default repr).

### Example

```python
cmd = MovePiece(from_pos=Position(6, 4), to_pos=Position(5, 4))
assert cmd.from_pos == Position(6, 4)
# Immutability
with pytest.raises(FrozenInstanceError):
    cmd.from_pos = Position(9, 9)
```

### Definition of Done

- [ ] `src/application/commands.py` defines `PlacePiece` and `MovePiece` as
      `frozen=True` dataclasses.
- [ ] `tests/unit/application/test_commands.py` verifies immutability and equality.

### Out of Scope

- Command routing / execution (US-303).

---

## US-302: Event Bus

**Epic:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §7`](../specifications/system_design.md)

**As a** developer,  
**I want** a publish/subscribe Event Bus that decouples the domain layer from
the UI and AI layers,  
**so that** the game controller can emit typed events and any number of
listeners (renderer, logger, AI) can react without the domain knowing about them.

### Acceptance Criteria

- [ ] **AC-1:** Given a subscriber registered for `PieceMoved`, When
      `event_bus.publish(PieceMoved(...))` is called, Then the subscriber
      callback is invoked exactly once.
- [ ] **AC-2:** Given no subscribers for `CombatResolved`, When published,
      Then no error is raised.
- [ ] **AC-3:** Given two subscribers for `TurnChanged`, When one raises an
      exception, Then the other subscriber still receives the event (error is
      logged, not re-raised).
- [ ] **AC-4:** Given `event_bus.unsubscribe(event_type, callback)`, When the
      event is published again, Then the callback is not invoked.
- [ ] **AC-5:** All eight event types from `system_design.md §7` are defined
      as frozen dataclasses.

### Example

```python
received = []
event_bus.subscribe(PieceMoved, lambda e: received.append(e))
event_bus.publish(PieceMoved(from_pos=Pos(6,4), to_pos=Pos(5,4), piece=scout))
assert len(received) == 1
```

### Definition of Done

- [ ] `src/application/event_bus.py` implements `subscribe`, `unsubscribe`,
      and `publish`.
- [ ] All 8 event types defined in `src/application/events.py`.
- [ ] `tests/unit/application/test_event_bus.py` covers all AC scenarios.

### Out of Scope

- Game Loop integration (US-305).

---

## US-303: Game Controller

**Epic:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §4`](../specifications/system_design.md)

**As a** developer,  
**I want** a Game Controller that accepts commands, validates them through the
rules engine, updates game state, and publishes domain events,  
**so that** the presentation layer only needs to submit commands and subscribe
to events, with zero game-logic coupling.

### Acceptance Criteria

- [ ] **AC-1:** Given a valid `MovePiece` command, When
      `game_controller.submit_command(cmd)`, Then a new `GameState` is stored,
      `PieceMoved` event is published, and the old state is unchanged.
- [ ] **AC-2:** Given an invalid `MovePiece` (e.g., moving to a lake),
      When `submit_command(cmd)`, Then `InvalidMove` event is published and
      the state is not updated.
- [ ] **AC-3:** Given a move that results in combat, When `submit_command(cmd)`,
      Then `CombatResolved` event is published with correct attacker/defender.
- [ ] **AC-4:** Given a move that captures the Flag, When `submit_command(cmd)`,
      Then `GameOver` event is published with the correct winner.

### Example

```python
controller = GameController(initial_state, event_bus, rules_engine)
controller.submit_command(MovePiece(from_pos=Pos(6,4), to_pos=Pos(5,4)))
assert controller.current_state.turn_number == 1
```

### Definition of Done

- [ ] `src/application/game_controller.py` implements `submit_command()` and
      exposes `current_state`.
- [ ] `tests/unit/application/test_game_controller.py` covers all AC scenarios
      using `pytest-mock` to mock the Event Bus.

### Out of Scope

- Turn rotation (US-304).
- AI invocation (US-304).

---

## US-304: Turn Manager

**Epic:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.2, §5`](../specifications/system_design.md)

**As a** player,  
**I want** the turn manager to alternate turns between players and automatically
request a move from the AI when it is the AI's turn,  
**so that** the game progresses correctly and human players cannot take
consecutive turns.

### Acceptance Criteria

- [ ] **AC-1:** Given Red makes a valid move, When the state updates,
      Then `active_player` becomes `PlayerSide.BLUE` and `TurnChanged(BLUE)`
      is published.
- [ ] **AC-2:** Given it is the AI's turn (Blue is `PlayerType.AI_HARD`),
      When `TurnChanged(BLUE)` fires, Then
      `ai_orchestrator.request_move(state, difficulty=HARD)` is called
      asynchronously.
- [ ] **AC-3:** Given the AI future completes, When `update()` collects it,
      Then the AI's `Move` is submitted to `GameController` automatically.
- [ ] **AC-4:** Given the AI returns an illegal move, When the controller
      rejects it, Then the orchestrator retries up to 3 times before logging
      a critical error.

### Example

> Player 1 (Red, Human) clicks a piece and moves it. Turn manager alternates
> to Player 2 (Blue, AI_MEDIUM). AI orchestrator is called asynchronously;
> within < 500 ms it returns a `Move` which is submitted to the controller.

### Definition of Done

- [ ] `src/application/turn_manager.py` implements turn alternation and AI
      dispatch.
- [ ] `tests/unit/application/test_turn_manager.py` mocks AI orchestrator
      and verifies turn alternation.

### Out of Scope

- AI search algorithm (EPIC-5).

---

## US-305: Game Loop

**Epic:** EPIC-3  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §3`](../specifications/system_design.md)

**As a** developer,  
**I want** the game loop to run at a consistent 60 FPS, processing input,
updating state, and rendering each frame,  
**so that** animations are smooth and AI thinking is bounded within the
configured time limit without blocking the main thread.

### Acceptance Criteria

- [ ] **AC-1:** Given the game loop runs for 60 iterations, When timing is
      measured, Then elapsed time is approximately 1.0 s (± 50 ms at 60 FPS).
- [ ] **AC-2:** Given the loop calls `process_input()`, `update()`, `render()`
      in that exact order, When traced, Then the sequence is never violated.
- [ ] **AC-3:** Given a `TerminalRenderer` (headless), When the loop runs for
      10 frames without input, Then no exception is raised.
- [ ] **AC-4:** Given an AI future that takes 800 ms to complete, When the
      loop runs, Then the result is collected in the next `update()` after
      completion and the loop never blocks for > 1 frame's duration on AI.

### Example

```python
loop = GameLoop(controller, terminal_renderer, clock_mock)
loop.run(max_frames=60)
assert clock_mock.tick_count == 60
```

### Definition of Done

- [ ] `src/application/game_loop.py` implements the three-phase loop.
- [ ] `tests/unit/application/test_game_loop.py` uses mocked renderer and
      clock to verify loop invariants.

### Out of Scope

- pygame rendering (EPIC-4).

---

## US-306: Screen Manager

**Epic:** EPIC-3  
**Priority:** Should Have  
**Specification refs:** [`screen_flow.md §4`](../specifications/screen_flow.md)

**As a** developer,  
**I want** a Screen Manager that maintains a stack of screens with push/pop/replace
operations and passes data between screens via `on_exit()` / `on_enter(data)`,  
**so that** screen transitions are predictable, data is not lost between screens,
and screens can be tested independently.

### Acceptance Criteria

- [ ] **AC-1:** Given `screen_manager.push(start_game_screen)`, When
      `screen_manager.current()`, Then returns `start_game_screen`.
- [ ] **AC-2:** Given a stack `[MainMenu, StartGame]`, When `pop()`, Then stack
      is `[MainMenu]` and `MainMenu.on_enter(data)` is called with
      `StartGame.on_exit()` return value.
- [ ] **AC-3:** Given `replace(playing_screen)`, When called on
      `[MainMenu, Setup]`, Then stack becomes `[MainMenu, Playing]`
      (avoids memory accumulation from deep stacks).

### Definition of Done

- [ ] `src/application/screen_manager.py` implements `push`, `pop`, `replace`,
      `current`, `render`, `handle_event`.
- [ ] `Screen` abstract base class defined in `src/presentation/screens/base.py`.
- [ ] `tests/unit/application/test_screen_manager.py` covers all AC scenarios.

### Out of Scope

- Concrete screen implementations (EPIC-4).

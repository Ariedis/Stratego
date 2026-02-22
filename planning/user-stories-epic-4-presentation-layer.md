# EPIC-4: Presentation Layer – User Stories

**Epic:** EPIC-4  
**Phase:** 4  
**Specification refs:** [`screen_flow.md`](../specifications/screen_flow.md),
[`system_design.md §2.4`](../specifications/system_design.md),
[`game_components.md §3.2`](../specifications/game_components.md)

---

## US-401: pygame Renderer and Board Display

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.4`](../specifications/system_design.md)

**As a** player,  
**I want** to see the Stratego board rendered as a 10×10 grid with lake
squares visually distinguished and pieces displayed at their correct positions,  
**so that** the game state is always clear and I can plan my moves visually.

### Acceptance Criteria

- [ ] **AC-1:** Given a `GameState` with a piece at `Position(6,4)`, When the
      renderer draws the board, Then a piece sprite is visible at grid cell
      `(6,4)` and no other cell shows that piece.
- [ ] **AC-2:** Given lake squares at `(4,2)`, `(4,3)`, `(5,2)`, `(5,3)`,
      `(4,6)`, `(4,7)`, `(5,6)`, `(5,7)`, When rendered, Then those 8 cells
      are drawn with the lake texture (visually distinct from normal squares).
- [ ] **AC-3:** Given a 1024×768 window, When the board is rendered, Then all
      100 squares fit within the board area without overflow.
- [ ] **AC-4:** Given `pygame.display.set_mode` returns a surface, When
      `renderer.render(game_state)` is called, Then no exception is raised.

### Example

> Board occupies the left 75 % of the 1024×768 window. Side panel occupies
> the remaining 25 %. Each grid cell is approximately 70×70 px.

### Definition of Done

- [ ] `src/presentation/pygame_renderer.py` implements `render(game_state)`.
- [ ] `src/presentation/sprite_manager.py` loads and caches Classic piece
      images.
- [ ] `tests/unit/presentation/test_pygame_renderer.py` uses a mocked
      `pygame.Surface` to verify sprite positioning without a real display.

### Out of Scope

- Fog-of-war (US-403).
- Custom army images (EPIC-7).

---

## US-402: Input Handler

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`system_design.md §2.4`](../specifications/system_design.md)

**As a** player,  
**I want** my mouse clicks to be translated into abstract game actions
(select piece, move piece, deselect),  
**so that** the game responds correctly to my input and the presentation layer
is the only module that handles raw OS events.

### Acceptance Criteria

- [ ] **AC-1:** Given a left-click on grid cell `(6,4)` that contains a Red
      piece while it is Red's turn, When `input_handler.process(event)`, Then
      `SelectPiece(pos=Position(6,4))` is emitted.
- [ ] **AC-2:** Given a piece is selected and a left-click on `(5,4)`,
      When processed, Then `MovePiece(from_pos=Pos(6,4), to_pos=Pos(5,4))`
      command is submitted to the controller.
- [ ] **AC-3:** Given a right-click anywhere, When processed, Then any current
      selection is cleared.
- [ ] **AC-4:** Given a click on a Blue piece while it is Red's turn,
      When processed, Then no command is submitted and the piece is not selected.
- [ ] **AC-5:** Given a `pygame.QUIT` event, When processed, Then the game
      loop exits cleanly.

### Example

```
Player clicks Red Scout at (6,4) → SelectPiece event → Scout highlighted
Player clicks (3,4) → MovePiece(from=(6,4), to=(3,4)) submitted → rules engine validates
```

### Definition of Done

- [ ] `src/presentation/input_handler.py` implements `process(pygame_event)`
      and returns `InputEvent | None`.
- [ ] `tests/unit/presentation/test_input_handler.py` uses `pytest-mock` to
      simulate `pygame.event.Event` objects.

### Out of Scope

- Drag-and-drop for Setup Screen (US-405).

---

## US-403: Fog of War

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §3.2`](../specifications/game_components.md)

**As a** player,  
**I want** to see my own pieces with their ranks visible but my opponent's
unrevealed pieces shown face-down,  
**so that** the hidden-information aspect of Stratego is preserved and the
game is fair.

### Acceptance Criteria

- [ ] **AC-1:** Given a Blue piece with `revealed=False`, When the board is
      rendered from Red's perspective, Then the piece is shown as a face-down
      (hidden) sprite with no rank indicator.
- [ ] **AC-2:** Given a Blue piece with `revealed=True` (post-combat),
      When rendered from Red's perspective, Then the piece rank is visible.
- [ ] **AC-3:** Given Red's own pieces, When rendered from Red's perspective,
      Then all ranks are always visible regardless of `revealed` flag.
- [ ] **AC-4:** Given a unit test that renders the board from Blue's
      perspective, When checking Red's unrevealed pieces, Then no rank
      information is present in the rendered output.

### Example

> Turn 1: Blue Spy at `(2,3)` has `revealed=False`. Red's renderer shows a
> plain blue tile. After Red attacks and combat occurs, `revealed=True` and
> Red's renderer now shows the Spy rank symbol.

### Definition of Done

- [ ] Renderer accepts a `viewing_player: PlayerSide` parameter.
- [ ] Fog-of-war filter applied in renderer, not in domain layer.
- [ ] `tests/unit/presentation/test_fog_of_war.py` asserts hidden/revealed
      logic from both perspectives.

### Out of Scope

- AI probability tracking for unrevealed pieces (EPIC-5).

---

## US-404: Main Menu Screen

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`screen_flow.md §3.1`](../specifications/screen_flow.md)

**As a** player,  
**I want** a main menu with clearly labelled buttons for Start Game, Continue,
Load Game, Settings, and Quit,  
**so that** I can navigate to any part of the game from a single entry point.

### Acceptance Criteria

- [ ] **AC-1:** Given the application starts with no save files, When the main
      menu is displayed, Then the **Continue** button is visually greyed out
      and non-clickable.
- [ ] **AC-2:** Given a save file exists, When the main menu is displayed,
      Then the **Continue** button is active and clicking it loads the most
      recent save and navigates to `PlayingScreen`.
- [ ] **AC-3:** Given clicking **Start Game**, When the screen transitions,
      Then `StartGameScreen` is pushed with no data.
- [ ] **AC-4:** Given clicking **Quit**, When triggered, Then
      `pygame.quit()` is called and the application exits cleanly.

### Definition of Done

- [ ] `src/presentation/screens/main_menu_screen.py` implements all buttons.
- [ ] `MainMenuScreen.on_enter()` queries `JsonRepository.get_most_recent_save()`
      to control Continue button state.

### Out of Scope

- Settings persistence (US-411).

---

## US-405: Setup Screen

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`screen_flow.md §3.6`](../specifications/screen_flow.md)

**As a** player,  
**I want** to drag and drop my 40 pieces from a tray onto my setup zone, with
Auto-arrange and Clear buttons, and a Ready button that activates only when
all pieces are placed,  
**so that** I can customise my army arrangement before each game.

### Acceptance Criteria

- [ ] **AC-1:** Given the Setup Screen opens, When displayed, Then all 40
      pieces appear in the piece tray sorted by rank.
- [ ] **AC-2:** Given dragging a piece to a valid setup square (Red: rows 6–9),
      When dropped, Then the piece snaps to the nearest valid grid cell.
- [ ] **AC-3:** Given dragging a piece to an invalid square (e.g., row 4 or a
      lake), When dropped, Then the piece returns to the tray with a visual
      error indicator.
- [ ] **AC-4:** Given clicking **Auto-arrange**, When triggered, Then all 40
      pieces are placed randomly in valid positions within 100 ms.
- [ ] **AC-5:** Given all 40 pieces placed, When the **Ready** button is
      clicked, Then `SetupScreen.on_exit()` returns the initial `GameState`
      and `PlayingScreen` is pushed.
- [ ] **AC-6:** Given fewer than 40 pieces placed, When **Ready** is clicked,
      Then an error message displays and no transition occurs.

### Example

> Player drags their Flag to `Position(9,0)` (back-left corner of Red's zone).
> Piece snaps to `(9,0)`. Piece tray now shows 39 remaining pieces.

### Definition of Done

- [ ] `src/presentation/screens/setup_screen.py` implements drag-and-drop,
      Auto-arrange, Clear, and Ready.
- [ ] `tests/unit/presentation/test_setup_screen.py` tests tray state after
      placement and Auto-arrange.

### Out of Scope

- 2-player local handoff between setup turns (Could Have for v1.0).

---

## US-406: Playing Screen

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`screen_flow.md §3.7`](../specifications/screen_flow.md)

**As a** player,  
**I want** the Playing Screen to show the full board, a side panel with game
info, and controls for saving and quitting,  
**so that** I have all the information I need during a game and can manage
my session.

### Acceptance Criteria

- [ ] **AC-1:** Given `TurnChanged(RED)` event fires, When side panel updates,
      Then active player indicator shows "Red's Turn".
- [ ] **AC-2:** Given a combat occurs, When `CombatResolved` event fires,
      Then both pieces' ranks are briefly highlighted (flash for 0.75 s)
      before settling to their final state.
- [ ] **AC-3:** Given an invalid move, When `InvalidMove` event fires,
      Then the selected piece is outlined in red for 1.5 s and an error
      message appears in the side panel.
- [ ] **AC-4:** Given clicking **Save Game**, When triggered, Then
      `JsonRepository.save(current_state)` is called and a "Saved" toast
      notification displays for 2 s.
- [ ] **AC-5:** Given clicking **Quit to Menu**, When triggered, Then an
      autosave is performed and `MainMenuScreen` is loaded.

### Definition of Done

- [ ] `src/presentation/screens/playing_screen.py` subscribes to all events
      listed in `screen_flow.md §3.7`.
- [ ] Board renders correctly after every state change.

### Out of Scope

- Undo/redo (v2.0).
- AI thinking indicator (Could Have).

---

## US-407: Game Over Screen

**Epic:** EPIC-4  
**Priority:** Must Have  
**Specification refs:** [`screen_flow.md §3.8`](../specifications/screen_flow.md)

**As a** player,  
**I want** to see a Game Over screen showing the winner, winning condition, and
total turn count, with options to play again, return to main menu, or quit,  
**so that** the game session ends gracefully with clear outcome information.

### Acceptance Criteria

- [ ] **AC-1:** Given Red wins by flag capture on turn 47, When `GameOverScreen`
      opens, Then it displays "Red wins!", "Flag captured", "47 turns".
- [ ] **AC-2:** Given clicking **Play Again**, When triggered, Then
      `StartGameScreen` is pushed.
- [ ] **AC-3:** Given clicking **Main Menu**, When triggered, Then the screen
      stack resets to `MainMenuScreen`.

### Definition of Done

- [ ] `src/presentation/screens/game_over_screen.py` displays winner, condition,
      and turn count.
- [ ] All three buttons navigate correctly.

---

## US-408: Terminal Renderer

**Epic:** EPIC-4  
**Priority:** Should Have  
**Specification refs:** [`system_design.md §2.4`](../specifications/system_design.md)

**As a** developer,  
**I want** a Terminal Renderer that prints an ASCII representation of the board,  
**so that** automated tests and CI environments can validate game state without
a display server.

### Acceptance Criteria

- [ ] **AC-1:** Given any `GameState`, When `TerminalRenderer.render(state)`,
      Then a valid 10-row, 10-column ASCII grid is printed to stdout with no
      exception.
- [ ] **AC-2:** Given a piece at `(3,5)`, When rendered, Then the piece rank
      abbreviation appears at column 5, row 3 of the printed grid.
- [ ] **AC-3:** Given lake squares, When rendered, Then they display as `~~`.

### Definition of Done

- [ ] `src/presentation/terminal_renderer.py` implements `render(game_state)`.
- [ ] Used in all unit tests that need board output without pygame.

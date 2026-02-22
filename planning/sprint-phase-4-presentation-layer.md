# Sprint Plan – Phase 4: Presentation Layer

**Phase:** 4  
**Duration:** 3 weeks (Sprints 8–10)  
**Exit criteria:** Complete human-vs-human game playable through the pygame UI with fog-of-war  
**Epic:** EPIC-4  
**Specification refs:** [`screen_flow.md`](../specifications/screen_flow.md),
[`system_design.md §2.4`](../specifications/system_design.md),
[`game_components.md §3.2`](../specifications/game_components.md)

---

## Sprint 8 (Week 8): Renderer and Input Handler

**Goal:** Board renders correctly; mouse input translates to commands.

### Tasks

---

#### TASK-401: Implement Terminal Renderer

**User story:** US-408  
**Module:** `src/presentation/terminal_renderer.py`  
**Depends on:** TASK-104

**Input:** `GameState`  
**Output:** ASCII board printed to stdout

**Steps:**

1. Create `src/presentation/terminal_renderer.py`.
2. Implement `TerminalRenderer.render(state: GameState, viewing_player: PlayerSide) -> None`:
   - Print a 10-row × 10-column ASCII grid.
   - Each cell: 4 characters wide.
   - Lake squares: `" ~~ "`.
   - Empty squares: `" .. "`.
   - Friendly pieces: rank abbreviation (e.g., `" M10"` for Marshal,
     `" SPY"` for Spy, `" BMB"` for Bomb).
   - Opponent unrevealed pieces: `" [?]"`.
   - Opponent revealed pieces: rank abbreviation with marker (e.g., `"[M ]"`)
3. Write `tests/unit/presentation/test_terminal_renderer.py`.

**Test cases to cover:**

- Lakes shown as `~~`.
- Own pieces show rank.
- Opponent unrevealed pieces show `[?]`.
- Opponent revealed pieces show rank.

---

#### TASK-402: Implement Sprite Manager (Classic)

**User story:** US-401  
**Module:** `src/presentation/sprite_manager.py`  
**Depends on:** TASK-104

**Input:** `assets/pieces/` folder structure  
**Output:** `SpriteManager` loading Classic piece images

**Steps:**

1. Create `src/presentation/sprite_manager.py`.
2. Define `SpriteManager.__init__(asset_dir: Path)`.
3. Implement `preload_classic() -> None`: loads all 12 rank images from
   `assets/pieces/<rank_lower>/` into a `dict[Rank, pygame.Surface]` cache.
4. Implement `get_surface(rank: Rank, owner: PlayerSide, revealed: bool) -> pygame.Surface`:
   - If `revealed=False` and owner is the opponent: return hidden-piece surface.
   - Otherwise return the rank-specific surface.
5. Create placeholder assets directory `assets/pieces/` with one PNG per rank
   (can be solid colour placeholders for now).
6. Write `tests/unit/presentation/test_sprite_manager.py` using mocked pygame
   (no real display required).

**Test cases to cover:**

- Returns correct surface per rank.
- Returns hidden surface for unrevealed opponent pieces.

---

#### TASK-403: Implement pygame Renderer

**User story:** US-401  
**Module:** `src/presentation/pygame_renderer.py`  
**Depends on:** TASK-402

**Input:** `GameState`, `viewing_player`  
**Output:** pygame surface drawn

**Steps:**

1. Create `src/presentation/pygame_renderer.py`.
2. Implement `PygameRenderer.__init__(screen: pygame.Surface, sprite_manager: SpriteManager)`.
3. Implement `render(state: GameState, viewing_player: PlayerSide) -> None`:
   - Calculate cell size from screen dimensions.
   - Draw board background.
   - Draw each of 100 squares (lake texture or normal).
   - For each non-empty square, call `sprite_manager.get_surface()` and
     `blit` at the correct pixel position.
   - Apply fog-of-war: pass `revealed` flag to `get_surface()` so opponent
     unrevealed pieces are hidden.
4. Write `tests/unit/presentation/test_pygame_renderer.py` with mocked
   `pygame.Surface.blit`.

**Test cases to cover:**

- Piece at `(6,4)` is blitted at the correct pixel coordinates.
- Lake squares use the lake texture surface.
- Opponent unrevealed pieces use the hidden surface.

---

#### TASK-404: Implement Input Handler

**User story:** US-402  
**Module:** `src/presentation/input_handler.py`  
**Depends on:** TASK-403

**Input:** `pygame.event.Event` objects  
**Output:** `InputEvent` objects or `Command` dispatched to controller

**Steps:**

1. Create `src/presentation/input_handler.py`.
2. Define `InputEvent` dataclasses: `ClickEvent(pos: Position)`,
   `RightClickEvent()`, `QuitEvent()`.
3. Implement `InputHandler.process(pygame_event, current_state, viewing_player) -> InputEvent | None`:
   - `MOUSEBUTTONDOWN` button 1: convert pixel position to grid `Position`;
     return `ClickEvent(pos)`.
   - `MOUSEBUTTONDOWN` button 3: return `RightClickEvent()`.
   - `QUIT`: return `QuitEvent()`.
4. Implement click-to-command logic in `PlayingScreen` (not in InputHandler –
   InputHandler only converts events to grid positions).
5. Write `tests/unit/presentation/test_input_handler.py`.

**Test cases to cover:**

- Left-click at pixel `(100, 100)` maps to correct grid `Position`.
- Right-click returns `RightClickEvent`.
- QUIT event returns `QuitEvent`.

---

## Sprint 9 (Week 9): Core Screens

**Goal:** Main Menu, Setup, Playing, and Game Over screens functional.

### Tasks

---

#### TASK-405: Implement Main Menu Screen

**User story:** US-404  
**Module:** `src/presentation/screens/main_menu_screen.py`  
**Depends on:** TASK-306

**Steps:**

1. Implement `MainMenuScreen(Screen)`.
2. `on_enter(data)`: Query `JsonRepository.get_most_recent_save()`. Disable
   Continue button if `None`.
3. Render background image and 5 `pygame_gui.UIButton` elements:
   Start Game, Continue, Load Game, Settings, Quit.
4. `handle_event()`: Route button clicks to `screen_manager.push()` or
   `screen_manager.replace()` per `screen_flow.md §3.1`.
5. Quit button calls `pygame.event.post(pygame.event.Event(pygame.QUIT))`.

---

#### TASK-406: Implement Setup Screen

**User story:** US-405  
**Module:** `src/presentation/screens/setup_screen.py`  
**Depends on:** TASK-404

**Steps:**

1. Implement `SetupScreen(Screen)` with `on_enter(data)` receiving
   `{player1_army, player2_army, game_mode, ai_difficulty}`.
2. Render the board (greyed out except setup zone) and a piece tray panel.
3. Implement drag-and-drop:
   - `MOUSEBUTTONDOWN` on a piece in the tray: start drag.
   - `MOUSEBUTTONUP` on a valid setup square: `apply_placement` via controller;
     remove piece from tray.
   - `MOUSEBUTTONUP` on invalid square: return piece to tray.
4. **Auto-arrange** button: Generate random valid placement using a helper
   function; submit all 40 `PlacePiece` commands.
5. **Clear** button: Remove all placed pieces back to tray.
6. **Ready** button (enabled only when tray is empty): Call `on_exit()` to
   pass the initial `GameState` to `PlayingScreen`.
7. In 2-player mode, after Player 1 clicks Ready, show a "hand off" screen
   before Player 2 places.

---

#### TASK-407: Implement Playing Screen

**User story:** US-406  
**Module:** `src/presentation/screens/playing_screen.py`  
**Depends on:** TASK-403, TASK-404

**Steps:**

1. Implement `PlayingScreen(Screen)` subscribing to:
   `PieceMoved`, `CombatResolved`, `TurnChanged`, `GameOver`, `InvalidMove`.
2. On `PieceMoved`: Re-render the board.
3. On `CombatResolved`: Flash both pieces' squares for 0.75 s then update.
4. On `TurnChanged`: Update side panel active-player indicator.
5. On `InvalidMove`: Outline selected piece in red for 1.5 s; show error in
   side panel.
6. On `GameOver`: Push `GameOverScreen` with `{winner, winning_condition, final_state}`.
7. Implement click handling: first click selects piece (highlight);
   second click on valid square submits `MovePiece`; right-click deselects.
8. Save Game button: call `JsonRepository.save()` then show toast notification.
9. Quit to Menu button: autosave then `screen_manager.replace(MainMenuScreen)`.

---

#### TASK-408: Implement Game Over Screen

**User story:** US-407  
**Module:** `src/presentation/screens/game_over_screen.py`  
**Depends on:** TASK-306

**Steps:**

1. Implement `GameOverScreen(Screen)`.
2. `on_enter(data)`: Extract `winner`, `winning_condition`, `turn_count`
   from data dict.
3. Display: `"<Winner> wins!"` or `"Draw!"`, winning condition string,
   `"Turn <N>"`.
4. Buttons: Play Again → `screen_manager.push(StartGameScreen)`;
   Main Menu → `screen_manager.replace(MainMenuScreen)`; Quit → pygame exit.

---

## Sprint 10 (Week 10): Secondary Screens and Integration

**Goal:** Start Game, Load Game, and Settings screens; end-to-end play test.

### Tasks

---

#### TASK-409: Implement Start Game Screen

**User story:** US-409 (F-4.9)  
**Module:** `src/presentation/screens/start_game_screen.py`  
**Depends on:** TASK-306

**Steps:**

1. Implement `StartGameScreen(Screen)`.
2. Two-player / vs AI toggle using `pygame_gui.UISelectionList` or radio
   buttons.
3. AI difficulty selector (Easy/Medium/Hard): shown only when vs AI selected;
   animate in/out on toggle.
4. Confirm → push `ArmySelectScreen` with `{game_mode, ai_difficulty}`.
5. Back → `screen_manager.pop()`.

---

#### TASK-410: Implement Load Game Screen

**User story:** F-4.10  
**Module:** `src/presentation/screens/load_game_screen.py`  
**Depends on:** TASK-306

**Steps:**

1. Implement `LoadGameScreen(Screen)`.
2. `on_enter()`: List all save files newest-first; populate
   `pygame_gui.UIScrollingContainer`.
3. Each entry shows filename, date/time, turn number.
4. Load button: `json_repository.load(selected)` → push `PlayingScreen(game_state)`.
5. Delete button: confirmation dialog → delete file → refresh list.
6. Back → `screen_manager.pop()`.
7. Empty-state message if no saves exist.

---

#### TASK-411: Implement Settings Screen

**User story:** F-4.11  
**Module:** `src/presentation/screens/settings_screen.py`  
**Depends on:** TASK-602 (Config)

**Steps:**

1. Implement `SettingsScreen(Screen)`.
2. Display all settings from `system_design.md §8`:
   Resolution dropdown, Fullscreen toggle, FPS cap slider (30–144),
   Sound effects toggle + volume slider, Music toggle + volume slider,
   Army mod folder picker.
3. Apply button: `Config.save(updated_config)`; return to MainMenu.
4. Reset to Defaults button: restore factory config values.
5. Back button: discard changes; return to MainMenu.

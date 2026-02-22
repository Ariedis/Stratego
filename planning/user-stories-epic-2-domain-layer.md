# EPIC-2: Domain Layer – Core Game Rules – User Stories

**Epic:** EPIC-2  
**Phase:** 2  
**Specification refs:** [`game_components.md`](../specifications/game_components.md),
[`data_models.md`](../specifications/data_models.md)

---

## US-201: Board Construction

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §2`](../specifications/game_components.md),
[`data_models.md §3.6`](../specifications/data_models.md)

**As a** developer,  
**I want** `Board` to correctly represent a 10×10 grid with lake squares,
neighbour queries, and setup-zone boundaries,  
**so that** movement validation and rendering can rely on a single authoritative
board model.

### Acceptance Criteria

- [ ] **AC-1:** Given `Board.create_empty()`, When checking lake positions,
      Then exactly 8 squares are lakes: `(4,2)`, `(4,3)`, `(5,2)`, `(5,3)`,
      `(4,6)`, `(4,7)`, `(5,6)`, `(5,7)`.
- [ ] **AC-2:** Given `board.neighbours(Position(5,5))`, When called, Then
      returns exactly 4 positions: `(4,5)`, `(6,5)`, `(5,4)`, `(5,6)`.
- [ ] **AC-3:** Given `board.neighbours(Position(0,0))`, When called, Then
      returns exactly 2 positions: `(1,0)`, `(0,1)`.
- [ ] **AC-4:** Given `board.is_in_setup_zone(Position(7,3), PlayerSide.RED)`,
      When called, Then `True` (Red rows 6–9).
- [ ] **AC-5:** Given `board.is_in_setup_zone(Position(4,3), PlayerSide.RED)`,
      When called, Then `False` (row 4 is not in Red's zone).

### Example

```python
board = Board.create_empty()
assert board.is_lake(Position(4, 2)) is True
assert board.is_lake(Position(4, 4)) is False   # between the two lakes
assert len(board.neighbours(Position(0, 0))) == 2
```

### Definition of Done

- [ ] `src/domain/board.py` implements all methods.
- [ ] `tests/unit/domain/test_board.py` covers all lake positions,
      corner/edge neighbours, and setup zone checks.

### Out of Scope

- Piece placement on the board (done in setup phase logic).

---

## US-202: Normal Piece Movement Validation

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §4.1, §4.3, §4.4`](../specifications/game_components.md)

**As a** player,  
**I want** the rules engine to reject illegal moves for normal pieces and
immovable pieces,  
**so that** I cannot accidentally place pieces on lakes, friendly squares, or
violate the two-square rule.

### Acceptance Criteria

- [ ] **AC-1:** Given a Sergeant at `(5,5)`, When moved to `(5,6)` (1 square
      right), Then `ValidationResult.OK`.
- [ ] **AC-2:** Given a Sergeant at `(5,5)`, When moved to `(5,7)` (2 squares),
      Then `ValidationResult.INVALID` (too far).
- [ ] **AC-3:** Given a Sergeant at `(5,5)`, When moved diagonally to `(6,6)`,
      Then `ValidationResult.INVALID`.
- [ ] **AC-4:** Given a piece at `(4,1)`, When moved to the lake `(4,2)`,
      Then `ValidationResult.INVALID` (lake impassable).
- [ ] **AC-5:** Given a Bomb at `(9,9)`, When any move is attempted,
      Then `RulesViolationError` is raised with message containing "immovable".
- [ ] **AC-6:** Given a Flag at `(9,0)`, When any move is attempted,
      Then `RulesViolationError` is raised.
- [ ] **AC-7:** Given a Captain at `(5,5)` that moved `(5,5)↔(5,6)` twice,
      When it tries to move back to `(5,5)` a third time, Then
      `ValidationResult.INVALID` (two-square rule).

### Example

```python
# Two-square rule
state_1 = apply_move(state_0, Move(piece=captain, from_pos=Pos(5,5), to_pos=Pos(5,6)))
state_2 = apply_move(state_1, Move(piece=captain, from_pos=Pos(5,6), to_pos=Pos(5,5)))
result  = validate_move(state_2, Move(piece=captain, from_pos=Pos(5,5), to_pos=Pos(5,6)))
assert result == ValidationResult.INVALID  # two-square rule
```

### Definition of Done

- [ ] `src/domain/rules_engine.py` implements `validate_move()` and `apply_move()`.
- [ ] `tests/unit/domain/test_rules_engine.py` covers all AC scenarios with
      parametrised tests.

### Out of Scope

- Scout movement (US-203).
- Combat resolution (US-204).

---

## US-203: Scout Movement

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §4.2`](../specifications/game_components.md)

**As a** player,  
**I want** a Scout to move any number of squares in a single orthogonal
direction and stop at the first enemy piece it encounters,  
**so that** I can use Scouts for long-range reconnaissance and attacks.

### Acceptance Criteria

- [ ] **AC-1:** Given a Scout at `(6,4)` with an empty column above it to `(2,4)`,
      When moved to `(2,4)`, Then `ValidationResult.OK`.
- [ ] **AC-2:** Given a Scout at `(6,4)` with a friendly piece at `(4,4)`,
      When moved to `(3,4)` (past the friendly piece), Then
      `ValidationResult.INVALID` (blocked).
- [ ] **AC-3:** Given a Scout at `(6,4)` with an enemy piece at `(4,4)`,
      When moved to `(4,4)`, Then `ValidationResult.OK` (attack) and combat
      is triggered.
- [ ] **AC-4:** Given a Scout at `(6,4)` with an enemy piece at `(4,4)`,
      When moved to `(3,4)` (through the enemy), Then `ValidationResult.INVALID`
      (cannot jump over enemy).
- [ ] **AC-5:** Given a Scout at `(5,5)`, When moved diagonally to `(3,3)`,
      Then `ValidationResult.INVALID` (diagonal not allowed for Scouts either).
- [ ] **AC-6:** Given a Scout attempting to cross lake `(4,2)–(5,3)`, When
      the path includes a lake square, Then `ValidationResult.INVALID`.

### Example

```python
# Long-range move
result = validate_move(state, Move(scout, from_pos=Pos(6,4), to_pos=Pos(2,4)))
assert result == ValidationResult.OK
```

### Definition of Done

- [ ] `rules_engine.py` handles Scout rank specially in movement validation.
- [ ] `tests/unit/domain/test_rules_engine.py` includes a dedicated Scout
      test class with parametrised direction tests (up, down, left, right).

### Out of Scope

- Normal piece movement (US-202).

---

## US-204: Combat Resolution

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §5`](../specifications/game_components.md)

**As a** player,  
**I want** the combat resolver to correctly apply all Stratego combat rules
including special cases,  
**so that** game outcomes are accurate and pieces are removed or retained as
per the official rules.

### Acceptance Criteria

- [ ] **AC-1 (Attacker wins):** Given Sergeant (rank 4) attacks Miner (rank 3),
      When resolved, Then Miner removed; Sergeant occupies the square.
- [ ] **AC-2 (Defender wins):** Given Spy (rank 1) attacks Captain (rank 6),
      When resolved, Then Spy removed; Captain stays.
- [ ] **AC-3 (Draw):** Given Colonel (rank 8) attacks Colonel (rank 8),
      When resolved, Then both removed.
- [ ] **AC-4 (Spy kills Marshal):** Given Spy attacks Marshal,
      When resolved, Then Marshal removed; Spy occupies the square.
- [ ] **AC-5 (Marshal kills Spy):** Given Marshal attacks Spy,
      When resolved, Then Spy removed; Marshal occupies (normal rank comparison).
- [ ] **AC-6 (Miner defuses Bomb):** Given Miner attacks Bomb,
      When resolved, Then Bomb removed; Miner occupies the square.
- [ ] **AC-7 (Piece loses to Bomb):** Given Captain attacks Bomb,
      When resolved, Then Captain removed; Bomb stays.
- [ ] **AC-8 (Flag capture):** Given any piece attacks Flag,
      When resolved, Then `GamePhase.GAME_OVER` and correct winner.
- [ ] **AC-9 (Revelation):** After any combat, Both pieces have `revealed=True`
      in the new `GameState`.
- [ ] **AC-10 (Spy defends):** Given Marshal attacks Spy (Spy is defending),
      When resolved, Then Spy removed; Marshal wins (Spy's special rule only
      applies when Spy initiates).

### Example

```python
result = resolve_combat(attacker=spy, defender=marshal)
assert result.outcome == CombatOutcome.ATTACKER_WINS
assert result.attacker_survived is True
assert result.defender_survived is False
```

### Definition of Done

- [ ] `src/domain/combat.py` implements all combat rules.
- [ ] `tests/unit/domain/test_combat.py` covers all 10 AC scenarios.
- [ ] Special cases (Spy/Marshal, Miner/Bomb, Flag) tested in both attacker
      and defender roles.

### Out of Scope

- Win condition detection (US-205).
- AI probability updates (EPIC-5).

---

## US-205: Win Condition Detection

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §6`](../specifications/game_components.md),
[`data_models.md §3.4`](../specifications/data_models.md)

**As a** player,  
**I want** the rules engine to detect all win conditions and transition the
game to `GAME_OVER` with the correct winner,  
**so that** the game ends correctly when a Flag is captured or a player has
no legal moves.

### Acceptance Criteria

- [ ] **AC-1:** Given Red attacks Blue's Flag, When combat resolved,
      Then `game_state.phase == GamePhase.GAME_OVER` and
      `game_state.winner == PlayerSide.RED`.
- [ ] **AC-2:** Given Blue has only Bombs and Flag remaining (no moveable pieces),
      When Red's turn ends, Then `game_state.phase == GamePhase.GAME_OVER`
      and `game_state.winner == PlayerSide.RED`.
- [ ] **AC-3:** Given `turn_number >= 3000`, When a move is applied,
      Then `game_state.phase == GamePhase.GAME_OVER` and
      `game_state.winner == None` (draw).
- [ ] **AC-4:** Given a normal mid-game state, When checking win conditions,
      Then `game_state.phase == GamePhase.PLAYING` (no false positives).

### Example

```python
state_with_blue_flag_captured = apply_move(state, attack_flag_move)
assert state_with_blue_flag_captured.phase == GamePhase.GAME_OVER
assert state_with_blue_flag_captured.winner == PlayerSide.RED
```

### Definition of Done

- [ ] `rules_engine.py` checks win conditions after every `apply_move()`.
- [ ] `tests/unit/domain/test_rules_engine.py` covers all 4 scenarios.

### Out of Scope

- Game Over screen rendering (EPIC-4).

---

## US-206: Setup Phase Validation

**Epic:** EPIC-2  
**Priority:** Must Have  
**Specification refs:** [`game_components.md §7`](../specifications/game_components.md)

**As a** player,  
**I want** the rules engine to reject piece placements outside my setup zone
and prevent the game from starting until both sides have placed all 40 pieces,  
**so that** setup is always valid before the game begins.

### Acceptance Criteria

- [ ] **AC-1:** Given Red tries to place a piece at `Position(3,5)` (Blue's
      zone), When validated, Then `ValidationResult.INVALID`.
- [ ] **AC-2:** Given Red places a piece at `Position(6,0)`, When validated,
      Then `ValidationResult.OK`.
- [ ] **AC-3:** Given Red places a piece on a lake square `(4,2)`,
      When validated, Then `ValidationResult.INVALID`.
- [ ] **AC-4:** Given both players have placed exactly 40 pieces,
      When `is_setup_complete()` is called, Then `True`.
- [ ] **AC-5:** Given Red has placed 39 pieces, When `is_setup_complete()`,
      Then `False`.

### Example

```python
result = validate_placement(state, PlacePiece(piece=flag, pos=Position(9,0)))
assert result == ValidationResult.OK  # Red's row 9 is valid

result = validate_placement(state, PlacePiece(piece=scout, pos=Position(2,0)))
assert result == ValidationResult.INVALID  # Row 2 is Blue's zone
```

### Definition of Done

- [ ] `rules_engine.py` implements `validate_placement()` and
      `is_setup_complete()`.
- [ ] `tests/unit/domain/test_rules_engine.py` covers setup zone boundaries
      for both players.

### Out of Scope

- UI drag-and-drop (EPIC-4).
- AI setup generation (EPIC-5).

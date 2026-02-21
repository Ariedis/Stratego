# Stratego – Game Components Specification

**Document type:** Game Components  
**Version:** 1.0  
**Author:** Software Architect (Python Game Specialist)  
**Status:** Approved  
**Depends on:** [`architecture_overview.md`](./architecture_overview.md)

---

## 1. Purpose

This document encodes the official Stratego rules into software component
definitions. Every rule, special behaviour, and edge case is named, described,
and mapped to the module responsible for enforcing it. Implementation teams
must treat this document as the authoritative source of truth for game logic.

---

## 2. The Board

### 2.1 Dimensions

- **10 × 10 grid** of squares, indexed as `(row, col)` where `(0, 0)` is the
  top-left from the perspective of Player 1 (Red).

### 2.2 Terrain

| Square type | Rows / Cols | Behaviour |
|---|---|---|
| Normal | All others | Pieces may occupy and traverse |
| Lake | `(4,2)`, `(4,3)`, `(5,2)`, `(5,3)` and `(4,6)`, `(4,7)`, `(5,6)`, `(5,7)` | Impassable; no piece may enter or cross |

### 2.3 Setup Zones

| Player | Rows available for initial piece placement |
|---|---|
| Player 1 (Red) | Rows 6–9 |
| Player 2 (Blue) | Rows 0–3 |

---

## 3. Pieces

### 3.1 Piece Inventory (40 pieces per player)

| Piece name | Rank | Count | Special ability |
|---|---|---|---|
| Marshal | 10 | 1 | Highest rank; loses to Spy |
| General | 9 | 1 | — |
| Colonel | 8 | 2 | — |
| Major | 7 | 3 | — |
| Captain | 6 | 4 | — |
| Lieutenant | 5 | 4 | — |
| Sergeant | 4 | 4 | — |
| Miner | 3 | 5 | Can defuse Bombs |
| Scout | 2 | 8 | Can move any number of squares in a straight line |
| Spy | 1 | 1 | Defeats the Marshal if Spy attacks first |
| Bomb | B | 6 | Immovable; defeats all attackers except Miner |
| Flag | F | 1 | Immovable; capturing it ends the game |

**Total: 40 pieces per player, 80 on the board.**

### 3.2 Visibility Rules

- A player always sees their own pieces (rank visible).
- Opponent pieces are **hidden** (rank concealed) until combat reveals them.
- After combat, both involved pieces become permanently revealed regardless
  of outcome.
- The `Piece` model carries a `revealed: bool` flag and visibility is
  determined per-player in the rendering layer.

---

## 4. Movement Rules

### 4.1 Normal Pieces

- Move **exactly one square** per turn, orthogonally (up, down, left, right).
- Cannot move diagonally.
- Cannot move onto a lake square.
- Cannot move onto a square occupied by a friendly piece.
- Cannot remain stationary (must move or attack).

### 4.2 Scout (Rank 2)

- May move **any number of squares** in a single orthogonal direction in one
  turn, like a rook in chess.
- Movement is blocked by lakes, friendly pieces, and enemy pieces (Scout
  stops on the enemy square and combat begins).
- A Scout **cannot** move and attack in the same turn if the target is
  more than one square away (rule clarification: this is standard; the Scout
  attacks the first enemy piece in its path).

### 4.3 Immovable Pieces

- **Bomb** and **Flag** may never move.
- Attempting to move them must be rejected at the rules-engine level with
  a clear error message.

### 4.4 The Two-Square Rule (optional/variant)

> A piece may not move back and forth between the same two squares on more
> than two consecutive turns, nor shuttle between the same row / column to
> create an infinite loop.

This rule prevents AI stalling. The rules engine tracks the last two moves per
piece and rejects patterns matching the rule.

---

## 5. Combat Resolution

### 5.1 General Principle

Combat occurs when a moving piece lands on a square occupied by an enemy piece.

| Outcome | Condition | Result |
|---|---|---|
| Attacker wins | Attacker rank > Defender rank | Defender removed; attacker occupies square |
| Defender wins | Defender rank > Attacker rank | Attacker removed; defender stays |
| Draw | Attacker rank == Defender rank | Both pieces removed |

### 5.2 Special Combat Interactions

| Attacker | Defender | Result | Rule |
|---|---|---|---|
| Any piece | Bomb | **Attacker loses** | Bombs defeat all attackers |
| Miner (3) | Bomb | **Attacker wins** | Miners defuse bombs |
| Spy (1) | Marshal (10) | **Attacker wins** | Spy's unique ability |
| Marshal (10) | Spy (1) | **Attacker wins** | Normal rank comparison |
| Spy (1) | Any non-Marshal | Spy **loses** | Spy is only rank-1 |
| Any piece | Flag | **Attacker wins** | Game ends immediately |

### 5.3 Combat Revelation

After any combat, both pieces' ranks are revealed to both players and remain
revealed for the rest of the game. This is a critical rule for AI opponent
design (see `ai_strategy.md`).

---

## 6. Win Conditions

A player **wins** when any of the following occur:

1. **Flag captured** – they move a piece onto the square occupied by the
   opponent's Flag.
2. **No legal moves** – the opponent has no pieces that can legally move
   (all remaining pieces are Bombs or the Flag), and the opponent has not
   captured the active player's Flag.

A game is a **draw** only in variants that allow it; the classic rules do not
formally define a draw, but implementations should include a maximum-turn
counter (e.g., 3 000 half-moves) to handle degenerate AI loops.

---

## 7. Setup Phase Rules

1. Each player places all 40 pieces in their setup zone before the game begins.
2. Pieces are placed face-down (hidden from opponent).
3. Player 1 places first; Player 2 places while Player 1's view is hidden
   (or simultaneously in a client-server implementation).
4. The Flag must be placed in the setup zone (cannot be placed in the
   opponent's half).
5. No restriction on how many of the same rank may occupy a single row or
   column during setup.

**Recommended AI Opening Book** (see `ai_strategy.md` for details):

> A common strong strategy documented by experienced Stratego players (e.g.,
> on *stratego.com* strategy guides) places the Flag in a back corner
> surrounded by Bombs, with Miners distributed in the middle rows to locate
> and defuse opponent Bombs.

---

## 8. Component Responsibility Map

| Rule / Behaviour | Enforced by module |
|---|---|
| Board boundary checks | `domain/board.py` |
| Lake passability | `domain/board.py` |
| Piece movement (normal + Scout) | `domain/rules_engine.py` |
| Immovable piece check | `domain/rules_engine.py` |
| Two-square rule | `domain/rules_engine.py` |
| Combat resolution table | `domain/combat.py` |
| Special combat interactions | `domain/combat.py` |
| Post-combat revelation | `domain/combat.py` |
| Win condition detection | `domain/rules_engine.py` |
| Setup zone validation | `domain/rules_engine.py` |
| Visibility filtering per-player | `presentation/pygame_renderer.py` |

---

## 9. Edge Cases and Known Complexity

| Edge case | Handling |
|---|---|
| Spy attacks Marshal while Spy is defending (not attacking) | Spy **loses** – the special rule only applies when Spy initiates the attack |
| Scout moves through a square previously occupied (now empty) | Allowed; rules engine checks current board state |
| Last Miner destroyed, Bombs remain around Flag | Game continues; those Bombs are effectively permanent barriers; opponent may still win if they can reach the flag another way |
| Both Flags captured simultaneously | Impossible in sequential turns; first capture wins |
| AI attempts illegal move | Rules engine rejects; AI orchestrator retries |

---

## 10. Related Documents

| Document | Purpose |
|---|---|
| [`architecture_overview.md`](./architecture_overview.md) | Architectural principles |
| [`data_models.md`](./data_models.md) | Domain model definitions |
| [`ai_strategy.md`](./ai_strategy.md) | How the AI uses these rules |

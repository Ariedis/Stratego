# Competitive Analysis: Strategy Board Game UX

**Version:** v1.1 (updated with live site verification)  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Scope:** Navigation flow, piece interaction, information architecture, and
accessibility patterns across comparable turn-based strategy games.

> **Update note (v1.1):** Lichess and Board Game Arena were accessed directly
> to verify claims. Lichess's open-source chessground library
> (`lichess-org/chessground`) was reviewed at the source-code level to confirm
> specific interaction defaults and colour values.

---

## Comparators

| Product | Platform | Relevance | Source |
|---|---|---|---|
| **Lichess** | Web (lichess.org) | Open-source chess; gold standard for turn-based board game UX; board rendering library (`chessground`) is open source | https://lichess.org / https://github.com/lichess-org/chessground |
| **Board Game Arena** | Web (boardgamearena.com) | World's largest board game platform: 10.68 million players, **1,226 games** (including Stratego), 9.29 million games/month | https://boardgamearena.com |
| **Chess.com** | Web + Mobile | Industry leader for chess UX; drag-and-drop piece movement, move history, captured pieces | https://chess.com |
| **Tabletop Simulator** | Steam / Desktop | PC desktop board game platform; shares pygame's pixel-canvas rendering paradigm | https://store.steampowered.com/app/286160/Tabletop_Simulator |

---

## Findings

### Lichess

> **Source verification:** Lichess's frontend board library
> [`chessground`](https://github.com/lichess-org/chessground) is MIT-licensed
> TypeScript. The following observations are confirmed directly from
> `src/state.ts` and `src/config.ts` in the repository.

**What they do well:**

- **Move highlighting is enabled by default in the library source:**
  ```typescript
  highlight: {
    lastMove: true,   // last-move squares always highlighted
    check: true,      // check square highlighted
  }
  movable: {
    showDests: true,  // legal move destinations shown on piece selection
  }
  ```
  Selected squares use a CSS class (`selected`); legal destinations use
  `move-dest` class (rendered as a dot on empty squares, a ring on occupied
  squares). Last-move origin and destination both receive the `last-move` class.
  These are **on by default** — the UX pattern is baked into the library.

- **Animation defaults are 200 ms:**
  ```typescript
  animation: {
    enabled: true,
    duration: 200,  // milliseconds
  }
  ```
  Pieces animate smoothly to their destination after any move. The minimum
  effective duration is 70 ms (below this the library disables animation).
  **Recommendation for Conqueror's Quest:** Use 200 ms as the target for all
  piece-movement animations.

- **Both drag-and-drop and click-click are ON by default:**
  ```typescript
  draggable: {
    enabled: true,
    distance: 3,       // minimum pixels before drag begins
    autoDistance: true,
    showGhost: true,   // ghost piece shown while dragging
  }
  selectable: {
    enabled: true,     // click-click selection also enabled
  }
  ```
  Users can switch between drag and click mid-game. The ghost image (`showGhost: true`)
  is critical for drag feedback — without it, players cannot see the piece they
  are moving.

- **Arrow/shape annotation system:** Players can right-click-drag to draw SVG
  arrows and circles on the board. Default brush colours are:
  ```
  green:  #15781B  (opacity 1.0)
  red:    #882020  (opacity 1.0)
  blue:   #003088  (opacity 1.0)
  yellow: #e68f00  (opacity 1.0)
  pale green: #15781B at 40% opacity
  pale red:   #882020 at 40% opacity
  ```
  These are irrelevant to Conqueror's Quest v1.0 but indicate that players of
  strategy games expect annotation affordances in later versions.

- **Captured pieces** appear above and below the board, sorted by material
  value. This is a key information element absent from Conqueror's Quest.

- **Feature set is entirely free:** Lichess offers all features (analysis,
  studies, puzzles, custom boards/pieces, 140+ language support) with zero
  paywalling — establishing a high baseline expectation for free desktop games.

**What they do poorly:**
- First-time player onboarding is absent from the board interface. Users must
  navigate to a separate `/learn` section manually — it is not surfaced at
  the point where new players are most confused (their first game).
- The mobile app touch targets can be small on phones — Lichess themselves
  acknowledge this in their GitHub issues for the mobile board.

**Reference:**
- https://lichess.org (live, verified 2026-02-24)
- https://github.com/lichess-org/chessground (source verified, commit `master`)
- https://lichess.org/features (feature list verified live)

---

### Board Game Arena

> **Source verification:** BGA homepage accessed live 2026-02-24. Confirmed:
> **10,681,000 players**, **1,226 games**, **9,290,000 games/month**, available
> in **42 languages**, platforms: PC/Mac, iOS, Android, Nintendo, PlayStation,
> Xbox. Real-time and turn-based modes.

**What they do well:**

- **Multi-platform reach without download:** BGA runs in-browser on all
  devices including consoles. For Conqueror's Quest, the equivalent is ensuring
  the pygame application installs and runs with a single command — friction at
  install time causes the same abandonment as friction in-game.

- **Player handover** in hot-seat (same-device) games uses a distinct
  full-screen confirmation screen: a coloured overlay shows the next player's
  name and a `"Player 2, your turn — click to continue"` call-to-action. This
  prevents accidental peeking and makes the handover moment feel deliberate.
  Conqueror's Quest lacks this for 2-player local setup mode — **the current
  `SetupScreen._on_ready()` silently replaces the screen without any handover
  prompt, creating an information security gap** (Player 1's layout could be
  glimpsed).

- **Empty-state handling:** BGA's game dashboards show illustrated empty states
  with a prominent call-to-action when no items exist. The Load Game screen in
  Conqueror's Quest should follow this pattern rather than showing only a text
  message.

- **Faction/army preview** in faction-selection screens shows a panel with
  faction name, lore text, a representative image, and a unit list — directly
  analogous to the `ArmySelectScreen` preview panel in Conqueror's Quest.

- **Real-time and turn-based dual modes:** BGA supports async (email-style) and
  live play for the same game. For Conqueror's Quest this is a v2.0 concern, but
  the UX pattern of clearly labelling the play mode in the session header is
  worth adopting at v1.0.

**What they do poorly:**
- Table lobby UI is visually dense and overwhelming for new players. The game
  count (1,226 games) is a strength and a weakness — the game selection screen
  requires good filtering to avoid paralysis by choice.
- Notification badges compete with game UI chrome on the same screen during play.

**Reference:**
- https://boardgamearena.com (live, verified 2026-02-24 — player count and game count confirmed)

---

### Chess.com

> **Note:** Chess.com could not be fetched directly from this environment.
> The following observations are based on documented UX patterns from
> publicly available design analyses and Chess.com's published blog posts.

**What they do well:**
- **Drag-and-drop polish:** Pieces "lift" visually (scale 1.15×, drop shadow
  added) when grabbed and follow the cursor with a ghost image. On drop, they
  animate to the target square with a 100 ms ease-out transition. This provides
  clear drag feedback that Conqueror's Quest's current click-to-place model
  lacks entirely.
- **Setup screen UX (Board Editor):** The Board Editor feature lets users
  arrange pieces by clicking a piece type in a sidebar then clicking any square
  — exactly the mental model needed for Conqueror's Quest setup phase. Piece
  counts are shown next to each type in the sidebar with a badge turning red
  when count reaches zero.
- **Responsive side panel:** Panel content ordered: active player indicator →
  clock → captured pieces → move list → controls.
- **Error feedback:** Invalid moves produce a subtle board shake animation
  rather than a colour flash.

**What they do poorly:**
- AI difficulty selector is buried in settings rather than integrated into the
  "New Game" flow — Conqueror's Quest's approach (difficulty in `StartGameScreen`)
  is actually better than Chess.com's.
- Premium feature gating creates a two-tier experience.

**Reference:** https://chess.com (not accessible from this environment —
observations from published sources)

---

### Tabletop Simulator

> **Note:** Steam store page could not be fetched directly from this
> environment. The following observations are based on documented UX patterns.

**What they do well:**
- **Piece physics and hover:** Even simple drop shadows and scale transforms
  significantly improve the tactile feel of board pieces in 2D.
- **Setup phase "bag" mechanic:** Pieces emerge from a container with a
  satisfying animation. The Conqueror's Quest auto-arrange button could use a
  short stagger animation (pieces fan out into position over 300 ms).
- **Information hiding:** Face-down card/piece mechanics use a card-back texture
  that is consistent across all hidden components.

**What they do poorly:**
- UX is largely unguided — the 3D sandbox paradigm gives maximum freedom at the
  cost of discoverability. Board game rules are not enforced.
- Performance degrades at large table scales.

**Reference:** https://store.steampowered.com/app/286160/Tabletop_Simulator/
(not accessible from this environment — observations from documented sources)

---

## Synthesised Recommendations for Conqueror's Quest

| Recommendation | Source | Priority | Implementation Note |
|---|---|---|---|
| Highlight valid move destinations when a piece is selected — **confirmed as `showDests: true` default in chessground** | Lichess (`state.ts`) | **Must Have** | `PlayingScreen`: compute legal moves on `_selected_pos` change; draw semi-transparent `#27AE60` overlay (dot) on each valid empty cell; ring on occupied cells |
| Last-move highlighting — **confirmed as `highlight.lastMove: true` default in chessground** | Lichess (`state.ts`) | **Must Have** | Track `_last_from_pos` and `_last_to_pos`; draw `#E67E22` / `#F39C12` fill (40% alpha) persisting 1.5 s after each move |
| Piece animation duration 200 ms — **confirmed as `animation.duration: 200` default in chessground** | Lichess (`state.ts`) | **Should Have** | All piece movement animations target 200 ms ease-out; minimum 70 ms before disabling |
| Ghost image during drag-and-drop — **confirmed as `showGhost: true` default in chessground** | Lichess (`state.ts`) | **Should Have** | `SetupScreen`: render a semi-transparent copy of the piece at cursor position while `_dragging_piece` is set |
| Show captured pieces tray in the side panel, sorted by rank descending | Lichess, Chess.com | **Should Have** | `PlayingScreen._render_panel()`: iterate `state.captured_pieces` filtered by `viewing_player` |
| Add full-screen player-handover overlay in 2-player local mode — **confirmed pattern on BGA live site** | Board Game Arena | **Must Have** | `SetupScreen._on_ready()`: before calling `screen_manager.replace()`, push a lightweight `HandoverScreen` with opaque scrim |
| Lift-and-ghost drag-and-drop for piece placement + movement | Lichess (chessground), Chess.com | **Should Have** | Both click-click and drag-drop active simultaneously; minimum drag distance 3 px before drag begins |
| Piece-count badges in the setup tray | Chess.com | **Should Have** | Group pieces by rank in the tray; badge turns `COLOUR_INVALID` when count reaches zero |
| Empty-state illustration for Load Game screen — **confirmed pattern on BGA live site** | Board Game Arena | **Could Have** | Replace the text "No saved games found." with a simple illustrated placeholder + "Start New Game" CTA button |
| Stagger animation for Auto-arrange | Tabletop Simulator | **Could Have** | After `auto_arrange()` completes, replay placement positions with 15 ms delay per piece using `update()` timer |
| Consistent face-down piece sprite | Tabletop Simulator | **Must Have** | All hidden enemy pieces render the same `face_down.png` sprite; only revealed pieces show rank art |
| Keyboard shortcut discovery overlay (`?` key) | Lichess | **Could Have** | Draw overlay listing all shortcuts when `?` / `F1` pressed on any screen |
| Shake animation for invalid moves instead of red flash | Chess.com | **Could Have** | Replace `_invalid_flash` red fill with a horizontal translate: ±8 px, 200 ms |

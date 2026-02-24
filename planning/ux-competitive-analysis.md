# Competitive Analysis: Strategy Board Game UX

**Version:** v1.0 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Scope:** Navigation flow, piece interaction, information architecture, and
accessibility patterns across comparable turn-based strategy games.

---

## Comparators

| Product | Platform | Relevance | Source |
|---|---|---|---|
| **Lichess** | Web (lichess.org) | Open-source chess; gold standard for turn-based board game UX; excellent accessibility and keyboard support | https://lichess.org |
| **Board Game Arena** | Web (boardgamearena.com) | Hosts 800+ board games including Stratego; direct design comparator | https://boardgamearena.com |
| **Chess.com** | Web + Mobile | Industry leader for chess UX; drag-and-drop piece movement, move history, captured pieces | https://chess.com |
| **Tabletop Simulator** | Steam / Desktop | PC desktop board game platform; shares pygame's pixel-canvas rendering paradigm | https://store.steampowered.com/app/286160/Tabletop_Simulator |

---

## Findings

### Lichess

**What they do well:**
- **Move highlighting** is the centrepiece of the UX: selected squares
  highlight in a warm yellow (`#F6F669`), legal destinations highlight in
  semi-transparent olive circles, and the last move highlights in both origin
  and destination. Players always know what is possible.
- **Keyboard shortcuts** are comprehensive: arrow keys navigate move history,
  `f` flips the board, `/` opens the search bar. All shortcuts are discoverable
  via a `?` overlay.
- **Accessibility:** WCAG AA compliant contrast on all UI chrome; board colours
  are user-selectable from 12 presets (helps colour-blind players distinguish
  sides); font size scales with browser zoom.
- **Captured pieces** appear in a tray above and below the board, sorted by
  material value. This is a key information element missing from Conqueror's
  Quest.
- **Status panel** is minimal: active player indicator, move clock (if timed),
  and a move list. Nothing extraneous.
- **Piece drag-and-drop** supports both click-click and drag-drop interaction
  models simultaneously, which accommodates both novice and expert habits.

**What they do poorly:**
- First-time player onboarding is absent — no tutorial overlay on the board
  interface. Users must find the "Learn" section manually.
- The mobile version has touch targets that are too small for the default board
  size on phones (60 × 60 px cells at 1280 px display width).

**Reference:** https://lichess.org (live) — see "Board" and "Accessibility"
sections of their preferences page.

---

### Board Game Arena

**What they do well:**
- **Player handover** in hot-seat (same-device) games uses a distinct
  full-screen confirmation screen: a coloured overlay shows the next player's
  name and a `"Player 2, your turn — click to continue"` call-to-action. This
  prevents accidental peeking and makes the handover moment feel deliberate.
  Conqueror's Quest lacks this for 2-player local setup mode.
- **Empty-state handling:** The "My games" dashboard shows a prominent
  illustrated empty state with a call-to-action button when no games exist,
  rather than a blank list. The spec's load game empty-state text should follow
  this pattern.
- **Army/faction preview** in games that support it (e.g. Pandemic, Scythe)
  shows a right-hand panel with faction lore, piece counts, and a sample
  artwork image — directly analogous to the `ArmySelectScreen` preview panel
  in Conqueror's Quest.
- **Settings persistence:** User preferences (sound volume, animation speed)
  are persisted to a user profile and applied on first load. No "Apply" step
  required — changes take effect immediately with an undo affordance.

**What they do poorly:**
- Table lobby UI is visually dense and overwhelming for new players.
- Notification badges compete with game UI chrome on the same screen.

**Reference:** https://boardgamearena.com — "Create a new game" and "Game
lobby" flows; "Blokus" or "Stratego" game sessions demonstrate the handover
screen.

---

### Chess.com

**What they do well:**
- **Drag-and-drop polish:** Pieces "lift" visually (scale 1.15×, drop shadow
  added) when grabbed and follow the cursor with a ghost image. On drop, they
  animate to the target square with a 100 ms ease-out transition. This provides
  clear drag feedback that Conqueror's Quest's current click-to-place model
  lacks entirely.
- **Setup screen UX:** The "Board Editor" feature lets users arrange pieces by
  clicking a piece type in a sidebar then clicking any square — exactly the
  mental model needed for Conqueror's Quest setup phase. Piece counts are shown
  next to each type in the sidebar with a badge turning red when count reaches
  zero.
- **Responsive side panel:** The side panel adapts gracefully from 1280 px to
  2560 px without layout breaks. Panel content is ordered: active player
  indicator → clock → captured pieces → move list → controls.
- **Error feedback:** Invalid moves produce a subtle board shake animation
  (10 px horizontal, 200 ms, ease-in-out) rather than a colour flash. Players
  perceive this as less punishing than a red highlight.

**What they do poorly:**
- The AI difficulty selector is buried in settings rather than integrated into
  the "New Game" flow. Conqueror's Quest's approach (difficulty in `StartGameScreen`)
  is actually better.
- Premium feature gating creates a two-tier experience that erodes trust.

**Reference:** https://chess.com — "Play vs Computer" flow and "Board Editor"
feature.

---

### Tabletop Simulator

**What they do well:**
- **Piece physics:** Pieces have 3D presence and respond to mouse hover with a
  subtle elevation. While Conqueror's Quest is 2D, this demonstrates that even
  simple drop shadows and scale transforms significantly improve the tactile
  feel of board pieces.
- **Setup phase:** Supports a "bag" mechanic — pieces emerge from a
  container with a satisfying animation. The Conqueror's Quest auto-arrange
  button could use a short stagger animation (pieces fan out into position over
  300 ms) to convey that the computer is "dealing" the army.
- **Information hiding:** Face-down card/piece mechanics are handled with a
  card-back texture that is consistent across all hidden components. Conqueror's
  Quest should adopt a consistent "face-down" piece sprite across all hidden
  enemy pieces.

**What they do poorly:**
- UX is largely unguided — the 3D sandbox paradigm gives maximum freedom at
  the cost of discoverability. Board game rules are not enforced, so players
  must self-police.
- Performance at large table scales degrades noticeably.

**Reference:** https://store.steampowered.com/app/286160/Tabletop_Simulator/

---

## Synthesised Recommendations for Conqueror's Quest

| Recommendation | Source | Priority | Implementation Note |
|---|---|---|---|
| Highlight valid move destinations when a piece is selected (olive/green circles or semi-transparent squares) | Lichess | **Must Have** | `PlayingScreen`: compute legal moves on `_selected_pos` change; draw semi-transparent `#27AE60` overlay on each valid cell |
| Show captured pieces tray in the side panel, sorted by rank descending | Lichess, Chess.com | **Should Have** | `PlayingScreen._render_panel()`: iterate `state.captured_pieces` filtered by `viewing_player` |
| Add full-screen player-handover overlay in 2-player local mode | Board Game Arena | **Must Have** | `SetupScreen._on_ready()`: before calling `screen_manager.replace()`, push a lightweight `HandoverScreen` |
| Lift-and-ghost drag-and-drop for piece placement | Chess.com | **Should Have** | `SetupScreen`: add `_dragging_piece` state; on `MOUSEBUTTONDOWN` start drag; on `MOUSEBUTTONUP` drop onto hovered cell |
| Piece-count badges in the setup tray | Chess.com | **Should Have** | Group pieces by rank in the tray; show `(3)` count badge next to each unique rank |
| Empty-state illustration for Load Game screen | Board Game Arena | **Could Have** | Replace the text "No saved games found." with a simple illustrated placeholder |
| Stagger animation for Auto-arrange | Tabletop Simulator | **Could Have** | After `auto_arrange()` completes, replay placement positions with 15 ms delay per piece using `update()` timer |
| Consistent face-down piece sprite | Tabletop Simulator | **Must Have** | All hidden enemy pieces should render the same `face_down.png` sprite regardless of rank; only revealed pieces show rank art |
| Keyboard shortcut discovery overlay (`?` key) | Lichess | **Could Have** | Draw an overlay listing all keyboard shortcuts when `?` / `F1` is pressed on any screen |
| Shake animation for invalid moves instead of red flash | Chess.com | **Could Have** | Replace `_invalid_flash` red fill with a horizontal translate animation: ±8 px over 200 ms |

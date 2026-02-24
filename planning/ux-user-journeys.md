# User Journey Maps: Conqueror's Quest

**Version:** v1.0 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-24

---

## Persona Definitions

### Persona A — "Alex" (Novice Player)
- **Age:** 22 | **Background:** Casual gamer; has never played Stratego before
- **Goal:** Learn the game and complete a first match against the AI
- **Device:** Desktop PC, 1920×1080, mouse-only interaction
- **Mental model:** Familiar with Chess at a very basic level; expects pieces to
  be clearly labelled and legal moves to be shown
- **Pain tolerance:** Low — if confused, will stop playing within 5 minutes

### Persona B — "Blake" (Experienced Player)
- **Age:** 35 | **Background:** Long-time Stratego player; knows all piece
  ranks, common openings, and bluff strategies
- **Goal:** Set up a custom army, play a fast game vs Hard AI, then review the
  outcome
- **Device:** Desktop PC, 2560×1440, keyboard and mouse
- **Mental model:** Knows exactly which pieces to place and where; wants
  keyboard shortcuts and minimal friction
- **Pain tolerance:** High for gameplay; low for UI friction (slow animations,
  missing shortcuts)

---

## Journey 1 — Alex: First Game vs Easy AI

**Persona:** Alex (Novice)  
**Goal:** Complete a first game against Easy AI  
**Scenario:** Alex downloads and launches Conqueror's Quest for the first time.
He has no saved games and does not know the piece ranks.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | Launches the application | Main Menu | 😐 Curious | Title says "STRATEGO" (old name?) not "Conqueror's Quest" | Match title to product name; add a subtitle tagline: "A Stratego-inspired strategy game" |
| 2 | Sees 5 buttons; "Continue" is greyed out | Main Menu | 😐 Neutral | No explanation for why Continue is greyed out | Show tooltip: "No saved game — start a new game first" |
| 3 | Clicks "Start Game" | Main Menu → Start Game | 🙂 Engaged | — | — |
| 4 | Sees "2 Players / vs AI" toggle | Start Game | 😐 Confused | "2 Players" could mean online; "vs AI" is clear | Rename to "Local 2-Player" |
| 5 | Selects "vs AI" | Start Game | 🙂 Engaged | Difficulty row appears suddenly — no animation | Animate difficulty row sliding down (200 ms) |
| 6 | Hovers over "Hard" | Start Game | 😐 Neutral | No tooltip — what does "Hard" mean in this game? | Implement difficulty tooltip from spec |
| 7 | Selects "Easy"; clicks "Confirm" | Start Game | 🙂 Engaged | **BUG: goes straight to Setup, skipping Army Select** | Fix navigation: go to ArmySelectScreen first |
| 8 | Arrives at Setup — sees a 10×10 board and a list of buttons | Setup | 😕 Confused | No instructions on which rows to use; "Pieces left: 40" tells nothing about which pieces | Add a highlighted overlay on valid placement rows (6–9 for Red) with label "Your setup zone" |
| 9 | Clicks "Auto [A]" to auto-arrange | Setup | 😊 Relieved | Pieces appear instantly with no animation | Add stagger animation: pieces fan out over 300 ms |
| 10 | Clicks "Ready [R]" | Setup | 🙂 Engaged | — | — |
| 11 | Game starts; it is Alex's turn | Playing | 😐 Confused | Pieces show no rank labels; he does not know which is which | Render rank abbreviations on friendly pieces |
| 12 | Clicks a piece | Playing | 😐 Confused | Yellow square highlight but no indication of where it can move | Implement valid-move highlighting |
| 13 | Clicks a valid destination | Playing | 🙂 Satisfied | Piece moves; AI takes a turn with no visual feedback | Show AI thinking indicator; highlight AI's moved piece |
| 14 | Attacks an AI piece; combat occurs | Playing | 😮 Surprised | Combat resolves instantly with a status message; no animation | Add combat reveal animation (both pieces flip face-up for 1 s) |
| 15 | Tries to move a Bomb accidentally | Playing | 😕 Frustrated | Error message: raw domain string, not readable | Map to "Bombs cannot move" |
| 16 | Plays to the end; flag captured | Playing → Game Over | 😊 Happy | — | — |
| 17 | Game Over screen — "Play Again" button | Game Over | 🙂 Engaged | **BUG: pressing "Play Again" returns to PlayingScreen (finished game)** | Fix to go to StartGameScreen |

**Key Opportunities from Alex's Journey:**
- Fix the `Play Again` navigation bug (severity-4)
- Add valid-move highlighting (severity-3)
- Add piece rank labels (severity-4)
- Add AI thinking feedback (severity-3)
- Add setup zone visual guide (severity-3)

---

## Journey 2 — Blake: Speed-Run vs Hard AI with Custom Army

**Persona:** Blake (Experienced)  
**Goal:** Set up a specific custom army, play vs Hard AI, review game statistics  
**Scenario:** Blake has used the app before. He has a saved game but wants
to start fresh with his preferred army layout.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | Launches the application | Main Menu | 🙂 Ready | "Continue" button is greyed out despite having saved games | Fix save-detection in `on_enter()` |
| 2 | Notices "Load Game" and "Settings" are both disabled | Main Menu | 😤 Frustrated | Promised features are not accessible | Implement both screens (or enable buttons once implemented) |
| 3 | Presses Enter to activate "Start Game" | Main Menu | 😤 Mildly frustrated | Enter key does nothing — mouse required | Add keyboard activation for focused buttons |
| 4 | Clicks "Start Game" | Main Menu → Start Game | 😐 Neutral | — | — |
| 5 | Selects "vs Computer" and "Hard" | Start Game | 🙂 Efficient | Good: toggle buttons work well, selection is clear | — |
| 6 | Presses Enter to confirm | Start Game | 😤 Frustrated | Enter key does nothing | Add `K_RETURN → _on_confirm()` |
| 7 | Clicks "Confirm" | Start Game | 😐 Neutral | **BUG: jumps to Setup, skipping Army Select** | Fix navigation |
| 8 | Arrives at Setup; presses A then R | Setup | 😊 Efficient | Keyboard shortcuts work well — A and R both work | — |
| 9 | Game starts; Blake wants to flip the board | Playing | 😕 Frustrated | No board-flip option | Add "Flip Board" toggle (F shortcut) |
| 10 | Moves pieces using click-click pattern | Playing | 🙂 Efficient | No drag-and-drop — slightly unnatural but usable | Add drag-and-drop as enhancement |
| 11 | AI moves with no visual indicator of where it moved from | Playing | 😐 Confused momentarily | No last-move highlighting for AI turns | Add last-move highlight |
| 12 | Wants to save mid-game | Playing | 😕 Frustrated | No "Save Game" button visible in the panel | Add Save Game button |
| 13 | Clicks "Quit to Menu" without confirming | Playing | 😤 Frustrated | No confirmation dialog; game state may be lost | Add quit confirmation with auto-save |
| 14 | Returns to Main Menu; "Continue" now enabled | Main Menu | 🙂 Satisfied | _(After fix)_ Continue button works correctly | — |

**Key Opportunities from Blake's Journey:**
- Keyboard navigation (Enter, Escape) throughout menus
- Save Game button in Playing panel
- Quit-to-menu confirmation dialog
- Board flip toggle
- Last-move highlight for AI turns

---

## Journey 3 — Blake: 2-Player Local Setup Handover

**Persona:** Blake (P1) + a friend (P2)  
**Goal:** Set up and play a 2-player local game  
**Scenario:** Blake and a friend are sitting at the same computer.

| Step | Action | Touchpoint | Emotional State | Pain Points | Opportunities |
|---|---|---|---|---|---|
| 1 | Blake selects "Local 2-Player" | Start Game | 🙂 Engaged | — | — |
| 2 | Blake arrives at Setup, places pieces | Setup | 🙂 Engaged | — | — |
| 3 | Blake clicks "Ready" | Setup | 😕 Concerned | Screen immediately replaces to Player 2's setup — Player 2 may see Player 1's arrangement for a moment | Add full-screen handover overlay BEFORE replacing screen |
| 4 | Handover screen shows "Player 1 has finished setup. Pass the device to Player 2." _(after fix)_ | Handover Overlay | 😊 Satisfied | Without this: Player 1's layout is briefly visible | `HandoverScreen`: opaque overlay, no board visible |
| 5 | Player 2 presses any key | Handover Overlay | 🙂 Ready | — | — |
| 6 | Player 2 arrives at their setup screen | Setup | 🙂 Engaged | No indication of which player is setting up | Add "Player 2 — Blue Army" heading in panel |
| 7 | Both players ready; game starts | Playing | 😊 Excited | — | — |

**Key Opportunities from Journey 3:**
- Player-handover overlay (critical for information hiding)
- Player identity label in Setup side panel

---

## Emotional Arc Summary

```
Alex (Novice):
  Launch → Confused → Engaged → Confused → Frustrated → Happy → Frustrated (bug)
  
  Low points: No piece labels, no move hints, Play Again bug
  High point: First successful move against AI

Blake (Experienced):
  Launch → Frustrated (disabled buttons) → Efficient → Frustrated (no KB nav) → Satisfied
  
  Low points: Missing keyboard shortcuts, no save button, no quit confirmation
  High point: Fast keyboard-driven setup phase
```

---

## Opportunities Summary (Prioritised)

| Opportunity | Persona(s) | Priority |
|---|---|---|
| Valid-move highlighting on piece selection | Alex | Must Have |
| Piece rank abbreviations on friendly tiles | Alex | Must Have |
| Fix Play Again navigation bug | Alex | Must Have |
| Player-handover overlay in 2-player mode | Both | Must Have |
| Keyboard navigation (Enter, Escape, Tab) | Blake | Should Have |
| AI thinking indicator | Alex | Should Have |
| Last-move highlight for AI turns | Alex, Blake | Should Have |
| Save Game button in Playing panel | Blake | Should Have |
| Quit-to-menu confirmation | Blake | Should Have |
| Setup zone visual guide (highlighted rows) | Alex | Should Have |
| Board flip toggle | Blake | Could Have |
| Drag-and-drop piece movement | Both | Could Have |

# UX Heuristics Evaluation: Conqueror's Quest

**Version:** v1.0 Draft  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Framework:** Nielsen's 10 Usability Heuristics  
**Scope:** All 8 screens defined in `specifications/screen_flow.md`

---

## Evaluation Method

Each of Nielsen's 10 heuristics is evaluated against every screen. Each
finding is rated for:
- **Severity:** 0 (cosmetic) → 4 (usability catastrophe)
- **Screen(s):** Which screen(s) are affected
- **Fix:** A specific, implementable change

---

## H1: Visibility of System Status

> The system should always keep users informed about what is going on, through
> appropriate feedback within reasonable time.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 1.1 | No visual indicator that a piece has been selected — only a yellow square highlight with no border or animation | 2 | Playing | Add a pulsing 2 px `#F1C40F` border around the selected cell (pulse: opacity 1.0 → 0.6 → 1.0, 800 ms loop) |
| 1.2 | Valid move destinations are not shown after piece selection — player must mentally calculate legal moves | 3 | Playing | Compute legal moves on selection; draw `#27AE60` semi-transparent fill (alpha 80) on each legal destination cell |
| 1.3 | After the AI makes a move, there is no visual indication of which piece moved or where it came from | 3 | Playing | Highlight the AI's `from_pos` cell in `#E67E22` and `to_pos` cell in `#F39C12` for 1.5 s after each AI turn |
| 1.4 | Status messages in the side panel (`_status_message`) use the raw enum value (e.g. `"RED's move"`) rather than a friendly player name | 2 | Playing | Replace with `"Red Army's move"` or the player's configured name |
| 1.5 | No loading/thinking indicator when the AI is computing its move — the game appears frozen | 3 | Playing | Display `"AI is thinking…"` with an animated ellipsis in the status area during AI turns |
| 1.6 | The Setup screen's "Pieces left" counter does not indicate which specific ranks still need to be placed | 2 | Setup | Show a breakdown by rank: `"Miners: 3  Scouts: 5  …"` or a mini-grid of remaining pieces |
| 1.7 | The `Continue` button is always greyed out — there is no message explaining why (no saves exist) or how to create one | 3 | Main Menu | When no saves exist, show a tooltip `"No saved game — start a new game first"` on hover; enable the button when a save exists |

---

## H2: Match Between System and Real World

> The system should speak the users' language, with words, phrases and concepts
> familiar to the user.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 2.1 | `"2 Players"` toggle label does not clarify local/same-device play; players may expect online multiplayer | 2 | Start Game | Rename to `"Local 2-Player"` to set accurate expectations |
| 2.2 | `"vs AI"` label should match the domain — Stratego players know the opponent as "computer" or "bot"; "vs AI" is acceptable but `"vs Computer"` is more universally understood | 1 | Start Game | Change label to `"vs Computer"` |
| 2.3 | "Auto-arrange" is a UX label; the Stratego community calls it "random placement" | 1 | Setup | Change label to `"Random Setup"` to match community terminology |
| 2.4 | "Winning condition" on the Game Over screen shows a raw string (e.g. `"flag_captured"`) not a human sentence | 3 | Game Over | Map condition strings: `flag_captured` → `"Flag captured!"`, `no_legal_moves` → `"Opponent has no moves left"` |
| 2.5 | `"RED wins!"` uses `PlayerSide.value` directly — not a friendly name | 2 | Game Over | Use `"Red Army wins!"` or support user-configured player names |

---

## H3: User Control and Freedom

> Users often choose system functions by mistake and will need a clearly marked
> "emergency exit" to leave the unwanted state.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 3.1 | No "Undo" button is rendered in the Playing screen even though the spec lists it as conditional on settings | 2 | Playing | Render the "Undo" button when the `undo_enabled` setting is `True`; wire it to a `UndoLastMove` command |
| 3.2 | The "Abandon" button in Setup is only accessible via the `Q` keyboard shortcut — it is not rendered | 3 | Setup | Add a visible `"Abandon"` button in the side panel between "Clear" and "Ready" |
| 3.3 | Quitting from `PlayingScreen` calls `pop()` once, leaving `SetupScreen` on the stack — subsequent Back presses may reveal the mid-game setup screen | 2 | Playing | Replace `pop()` with `screen_manager.replace(MainMenuScreen(...))` or pop until the stack contains only `MainMenuScreen` |
| 3.4 | Deleting a save file on `LoadGameScreen` is not implemented — no confirmation dialog defined | 3 | Load Game | When "Delete" is clicked, push a modal overlay: `"Delete save from [date]? This cannot be undone. [Cancel] [Delete]"` |
| 3.5 | Settings changes are discarded silently on "Back" with no confirmation | 2 | Settings | If changes are pending, show confirmation: `"Discard unsaved changes? [Keep Editing] [Discard]"` |

---

## H4: Consistency and Standards

> Users should not have to wonder whether different words, situations, or
> actions mean the same thing.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 4.1 | Button sizes are inconsistent: Main Menu uses 280×52 px, Start Game uses 200×48 px nav buttons and 160×48 px nav buttons, Setup uses 160×40 px | 2 | All | Standardise on a button size system: Large (240×52 px), Medium (160×48 px), Small (120×40 px) — see Visual Style Guide |
| 4.2 | Border-radius is 8 px on some buttons and 6 px on others | 1 | All | Standardise on `border_radius=8` across all buttons |
| 4.3 | The "selected" state for toggle buttons (game mode, difficulty) uses `#3C8C50` (green); the primary action button (Confirm) uses `#324664` (blue) — conflicting semantics | 2 | Start Game | Reserve green for "selected/active state"; use `#2980B9` (blue) for primary action buttons |
| 4.4 | "Back" and "Confirm" are reversed in position relative to platform conventions: "Confirm" should be on the right (primary action), "Back" on the left | 2 | Start Game | Swap positions: "Back" left, "Confirm" right |
| 4.5 | Game Over screen buttons are in order "Play Again / Main Menu / Quit" but should be "Main Menu / Play Again / Quit" (least→most commitment from left→right) | 1 | Game Over | Reorder: "Main Menu" left, "Play Again" centre, "Quit" right |

---

## H5: Error Prevention

> Even better than good error messages is a careful design which prevents a
> problem from occurring in the first place.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 5.1 | The "Ready" button is available immediately (just disabled) but there is no visual affordance explaining why it is disabled | 2 | Setup | Show `"Place all 40 pieces to continue"` as a subtitle below the pieces counter |
| 5.2 | Clicking outside the board or setup zone gives no feedback — pieces silently fail to place | 3 | Setup | When a click lands outside the valid setup zone, flash the clicked cell `#E74C3C` for 0.5 s with label `"Place pieces in your rows (6–9)"` |
| 5.3 | AI difficulty tooltips are listed in the spec but not implemented — players may select "Hard" accidentally | 2 | Start Game | On hover over each difficulty button, show a tooltip: Easy = `"Makes random moves occasionally"`, Medium = `"Balanced challenge"`, Hard = `"Plays near-optimally"` |
| 5.4 | No confirmation when leaving a game mid-play via "Quit to Menu" — progress is lost | 3 | Playing | Show a confirmation dialog: `"Quit to menu? Your game will be auto-saved. [Stay] [Quit & Save]"` |

---

## H6: Recognition Rather Than Recall

> Minimise the user's memory load by making objects, actions, and options
> visible.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 6.1 | Piece ranks are not visible on the board — players must remember what they placed where | 4 | Playing, Setup | Render the rank number (or a 2-letter abbreviation: `Ma`, `Ge`, `Sp`, `Fl`, `Bm`) inside each friendly piece tile |
| 6.2 | The side panel shows a plain "Turn N" counter but no per-player move history | 2 | Playing | Add a scrollable last-5-moves history in the panel: `"RED: E4→E5"`, `"BLUE: D6→D5"` |
| 6.3 | Keyboard shortcuts (A, C, R, Q) are shown inline with button labels (`"Auto [A]"`) — good; maintain this pattern on all screens | 0 | Setup | No change needed — this is a best practice; replicate on all screens |
| 6.4 | Army name in `ArmySelectScreen` is not carried through to the setup or playing screen — players cannot confirm which army they chose | 2 | Setup, Playing | Show army name as a subtitle in the side panel: `"Classic Army"` or `"[Custom army name]"` |

---

## H7: Flexibility and Efficiency of Use

> Accelerators — unseen by the novice user — may speed up interaction for the
> expert user.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 7.1 | No global keyboard shortcuts for navigation (Escape to go back, Enter to confirm) | 2 | All | Add `K_ESCAPE → _on_back()` and `K_RETURN → _on_confirm()` on all screens that have a Back/Confirm pair |
| 7.2 | No Tab/Shift-Tab focus traversal — mouse-only navigation | 2 | All | Implement a `_focused_button_index` state variable; Tab increments it, Enter activates; draw a 2 px `#F39C12` outline on the focused button |
| 7.3 | Auto-arrange exists but no option to save/recall named layouts | 1 | Setup | **Could Have** — add a "Save Layout" / "Load Layout" option in a future sprint; mark as backlog item |
| 7.4 | No way to flip the board perspective in the Playing screen | 1 | Playing | Add a `"Flip Board"` toggle in the side panel (`F` shortcut); swap `viewing_player` |

---

## H8: Aesthetic and Minimalist Design

> Dialogues should not contain irrelevant or rarely needed information.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 8.1 | Background colour `(20, 30, 48)` is identical across all screens — menus feel identical to the game board | 1 | All | Use `(20, 30, 48)` for menus and a slightly warmer `(25, 35, 52)` with a subtle wood-grain or linen texture for the board background |
| 8.2 | The side panel is 25 % of the window — very wide for the content it holds (3 labels + 1 button) | 2 | Playing, Setup | Reduce to 20 % (`_BOARD_FRACTION = 0.80`) and add the captured pieces tray and move history to fill the space meaningfully |
| 8.3 | Game Over screen uses only the upper third for content, leaving large empty space below the reason text | 1 | Game Over | Add a replay of the last 5 moves or a "Replay game" section in the empty space (Could Have) |
| 8.4 | No visual separation between the game title and menu buttons on the Main Menu — the title floats disconnected | 1 | Main Menu | Add a 1 px `#4A6741` horizontal rule below the title, with 24 px margin |

---

## H9: Help Users Recognise, Diagnose, and Recover from Errors

> Error messages should be expressed in plain language (no codes), precisely
> indicate the problem, and constructively suggest a solution.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 9.1 | Invalid-move error message shows the raw domain reason string (e.g. `"InvalidMove(reason='piece_blocked')"`) | 3 | Playing | Map domain reason codes to human messages: `piece_blocked` → `"That path is blocked"`, `wrong_turn` → `"It is not your turn"`, `immovable_piece` → `"Bombs and Flags cannot move"` |
| 9.2 | No error handling for corrupt save files — `LoadGameScreen` has no defined error state | 3 | Load Game | If a save file fails to parse, show: `"Save file is corrupted and cannot be loaded. [Delete] [Cancel]"` |
| 9.3 | The `_on_play_again()` method in `GameOverScreen` calls `pop()` which returns to `PlayingScreen` (a finished game) not `StartGameScreen` | 4 | Game Over | Replace `pop()` with explicit navigation to `StartGameScreen` using `screen_manager.replace()` |

---

## H10: Help and Documentation

> Even though it is better if the system can be used without documentation,
> it may be necessary to provide help and documentation.

| # | Finding | Severity | Screen | Fix |
|---|---|---|---|---|
| 10.1 | No tutorial, help overlay, or rules reference anywhere in the game | 3 | All | Add a `"How to Play"` button to the Main Menu that pushes a scrollable `RulesScreen` with the key rules from `game_components.md` |
| 10.2 | AI difficulty descriptions are missing — players cannot make an informed choice | 2 | Start Game | Implement the difficulty tooltips as specified in `screen_flow.md §3.2` |
| 10.3 | The two-square rule (anti-stalling) is not communicated to players — they will experience a mysterious "invalid move" | 2 | Playing | Add to the invalid-move message: `"You cannot move this piece back and forth on consecutive turns (two-square rule)"` |

---

## Summary Severity Heatmap

| Screen | Sev 4 | Sev 3 | Sev 2 | Sev 1 | Total |
|---|---|---|---|---|---|
| Main Menu | 0 | 2 | 1 | 1 | 4 |
| Start Game | 0 | 1 | 4 | 2 | 7 |
| Army Select | — | — | — | — | _not yet implemented_ |
| Load Game | 0 | 2 | 0 | 0 | 2 |
| Settings | 0 | 0 | 1 | 0 | 1 |
| Setup | 0 | 3 | 2 | 0 | 5 |
| Playing | 1 | 5 | 4 | 1 | 11 |
| Game Over | 1 | 1 | 1 | 1 | 4 |
| **Totals** | **2** | **14** | **13** | **5** | **34** |

**Highest-risk screen: `PlayingScreen`** — 1 severity-4 and 5 severity-3
issues make it the most urgent target for improvements.

---

## Recommended Fix Order (Quick Wins First)

1. **Fix `_on_play_again()` navigation bug** (30 min) — one-line change
2. **Enable Continue button via save-file check** (1 hour) — wire existing API
3. **Add "Abandon" button to Setup panel** (30 min) — copy button render pattern
4. **Render rank abbreviations on friendly pieces** (2 hours) — draw text on cell
5. **Add valid-move highlighting** (3 hours) — query rules engine for legal moves
6. **Map error code strings to readable messages** (1 hour) — add a lookup dict
7. **Add player-handover overlay** (2 hours) — create `HandoverScreen` class
8. **Add Save Game button to Playing panel** (1 hour) — extend `_render_panel()`
9. **Add captured pieces tray** (3 hours) — parse `state` for revealed captures
10. **Add AI thinking indicator** (1 hour) — subscribe to AI start/end events

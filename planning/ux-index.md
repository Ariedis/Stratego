# Conqueror's Quest – UX Documentation Index

**Version:** v1.0  
**Author:** Senior UX Designer  
**Date:** 2026-02-24  
**Status:** Draft – ready for developer review

---

## Purpose

This directory contains the complete UX design artefacts for *Conqueror's Quest*
(the Stratego implementation). Every document here is **actionable**: each
recommendation includes a specific change with enough detail for a developer or
artist to implement it without further clarification.

> **Note for developers:** All UX documents are located in `/planning/` with a
> `ux-` prefix. A dedicated `/ux/` directory should be created as part of
> repository housekeeping (see improvement #11 below).

---

## Document Index

| Document | Contents |
|---|---|
| [ux-competitive-analysis.md](./ux-competitive-analysis.md) | Survey of Lichess, Board Game Arena, Chess.com, and Tabletop Simulator |
| [ux-heuristics-evaluation.md](./ux-heuristics-evaluation.md) | Nielsen's 10 heuristics evaluation of all 8 screens with actionable improvements |
| [ux-visual-style-guide.md](./ux-visual-style-guide.md) | Colour palette, typography, spacing system, component library |
| [ux-user-journeys.md](./ux-user-journeys.md) | Journey maps for novice and experienced player personas |
| [ux-accessibility.md](./ux-accessibility.md) | WCAG 2.1 AA contrast ratios, keyboard nav, screen-reader labels |
| [ux-wireframe-main-menu.md](./ux-wireframe-main-menu.md) | `MainMenuScreen` wireframe + interaction spec |
| [ux-wireframe-start-game.md](./ux-wireframe-start-game.md) | `StartGameScreen` wireframe + interaction spec |
| [ux-wireframe-army-select.md](./ux-wireframe-army-select.md) | `ArmySelectScreen` wireframe + interaction spec |
| [ux-wireframe-load-game.md](./ux-wireframe-load-game.md) | `LoadGameScreen` wireframe + interaction spec |
| [ux-wireframe-settings.md](./ux-wireframe-settings.md) | `SettingsScreen` wireframe + interaction spec |
| [ux-wireframe-setup.md](./ux-wireframe-setup.md) | `SetupScreen` wireframe + interaction spec |
| [ux-wireframe-playing.md](./ux-wireframe-playing.md) | `PlayingScreen` wireframe + interaction spec |
| [ux-wireframe-game-over.md](./ux-wireframe-game-over.md) | `GameOverScreen` wireframe + interaction spec |

---

## Top 10 Actionable Improvements (MoSCoW)

The following is a prioritised summary. Full rationale and implementation
details are in [ux-heuristics-evaluation.md](./ux-heuristics-evaluation.md).

| # | Improvement | Priority | Screen(s) | Effort |
|---|---|---|---|---|
| 1 | Enable the **Continue** button by wiring `JsonRepository.get_most_recent_save()` to `MainMenuScreen.on_enter()` — currently hardcoded `disabled: True` | **Must Have** | Main Menu | Small |
| 2 | Fix **Play Again** navigation — `_on_play_again()` calls `pop()` which returns to `PlayingScreen`, not `StartGameScreen` as the spec requires | **Must Have** | Game Over | Small |
| 3 | Implement the missing **ArmySelectScreen** — `StartGameScreen._on_confirm()` skips army selection and jumps directly to `SetupScreen` | **Must Have** | Start Game → Army Select | Medium |
| 4 | Add **valid-move highlighting** — when a piece is selected, highlight legal destination squares in `#27AE60` (green) and illegal squares in `#E74C3C` (red) | **Must Have** | Playing | Medium |
| 5 | Add **player-handover overlay** — in 2-player local mode, display a full-screen `"Pass device to Player 2 – press any key to continue"` confirmation before Player 2's setup | **Must Have** | Setup | Small |
| 6 | Implement **LoadGameScreen** — currently a disabled stub; players who click "Load Game" receive no feedback | **Should Have** | Main Menu → Load Game | Medium |
| 7 | Implement **SettingsScreen** — currently a disabled stub; resolution, fullscreen, audio, and mod-folder settings are all inaccessible | **Should Have** | Main Menu → Settings | Medium |
| 8 | Add a **captured pieces tray** to the Playing screen side panel showing opponent pieces revealed through combat, sorted by rank descending | **Should Have** | Playing | Small |
| 9 | Add a **"Save Game"** button to the Playing screen controls bar — present in the spec but absent from the rendered panel | **Should Have** | Playing | Small |
| 10 | Add **keyboard navigation** — Tab/Shift-Tab cycles focus, Enter activates, Escape invokes Back; display focus ring `outline: 3px solid #F39C12` | **Should Have** | All menus | Medium |

---

## Critical Bugs Found During UX Review

The following issues are bugs (not UX improvements) discovered during the
review — they should be fixed before the UX polish pass:

| Bug | Location | Severity |
|---|---|---|
| `Continue` button is hardcoded `disabled: True` regardless of save files | `main_menu_screen.py:185` | High |
| `_on_play_again()` calls `pop()` returning to `PlayingScreen` instead of `StartGameScreen` | `game_over_screen.py:241` | High |
| `_on_confirm()` on `StartGameScreen` calls `game_context.start_new_game()` which bypasses `ArmySelectScreen` | `start_game_screen.py:283` | High |
| `ArmySelectScreen` class does not exist in `src/presentation/screens/` | — | High |
| `LoadGameScreen` class does not exist in `src/presentation/screens/` | — | Medium |
| `SettingsScreen` class does not exist in `src/presentation/screens/` | — | Medium |
| Side panel "Save Game" button missing from `PlayingScreen` render | `playing_screen.py:335` | Medium |
| `SetupScreen` renders no "Abandon" button — only reachable via `Q` key | `setup_screen.py:200` | Low |

---

## Specification References

- [`specifications/screen_flow.md`](../specifications/screen_flow.md)
- [`specifications/architecture_overview.md`](../specifications/architecture_overview.md)
- [`specifications/game_components.md`](../specifications/game_components.md)

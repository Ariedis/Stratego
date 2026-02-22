# ADR-006: Custom Army Mod System – JSON Folder Format

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

*Conqueror's Quest* must allow players to upload custom armies with a name,
custom unit display names, and custom piece images (potentially animated GIFs,
with multiple images per unit type chosen at random each game).

We need to decide:

1. The **on-disk format** for a mod (how files are organised and described).
2. The **manifest format** (how metadata and unit names are declared).
3. How **multiple images per unit type** are stored and selected.

---

## Decision

**Use a self-contained folder-based mod with a JSON manifest (`army.json`).**

Each mod is a directory placed in a user-configurable mods folder. The
directory contains:

- `army.json` – metadata and unit name overrides.
- `images/<rank>/` sub-directories containing one or more image files per rank.

Image selection at game start: all valid images in a rank's sub-directory are
collected; one is chosen at random and used for the whole session.

---

## Rationale

### Why a folder, not a single archive file?

| Criterion | Folder | ZIP / custom archive |
|---|---|---|
| Human-readable | ✅ Images and JSON browsable in file explorer | ❌ Requires extraction tool |
| Easy to author | ✅ Drop files in, edit JSON in any text editor | ❌ Requires re-packaging |
| Easy to validate at load time | ✅ Incremental file-by-file reading | ⚠️ Must extract to validate |
| Cross-platform path handling | ✅ OS-native paths | ⚠️ ZIP internal path separators vary |

For a v1.0 desktop application aimed at hobbyist modders, the lowest barrier
to entry matters most. A folder is universally understandable.

> **Precedent:** *Dwarf Fortress* raw mods, *Battle for Wesnoth* unit packs,
> and *OpenTTD* NewGRF content all use folder/file-based mod structures that
> players can inspect and edit without special tools.

### Why JSON for the manifest, not TOML or YAML?

- JSON is already the persistence format (ADR-004); no new parsing library needed.
- Python's standard-library `json` module is used, keeping dependencies minimal.
- JSON is universally understood by modders.
- YAML was considered but rejected: YAML's indentation-sensitivity causes
  hard-to-debug authoring errors; not worth the marginal readability gain.
- TOML was considered but rejected: Python 3.11+ standard `tomllib` is
  read-only (no write support), and TOML offers no significant advantage over
  JSON for a small manifest.

### Why random image selection per session, not per piece?

Choosing one image per **rank per session** (rather than per piece instance)
ensures all pieces of the same rank look identical within a game. This is
important for gameplay clarity: players must be able to visually distinguish
their own pieces by rank. Per-piece random selection would produce a confusing
board where two Scouts look different from each other.

### Why sub-directories per rank rather than filename conventions?

Grouping images under `images/<rank>/` is more scalable and requires no
filename-parsing logic. Adding a new image for a rank is as simple as dropping
a file in the right folder. Filename conventions (e.g., `marshal_1.png`,
`marshal_2.png`) would require parsing and could conflict with user-chosen
names.

---

## Alternatives Considered

| Alternative | Outcome |
|---|---|
| Single ZIP archive per mod | Rejected: higher barrier for modders; no significant advantage at v1.0 scale |
| YAML manifest | Rejected: indentation sensitivity; no standard library support without `PyYAML` dependency |
| SQLite database for mod metadata | Rejected: massive overkill; binary format; not human-editable |
| Hard-coded army variants in source code | Rejected: does not allow player-created mods at all |

---

## Consequences

- A new `src/infrastructure/mod_loader.py` module is required.
- `src/presentation/sprite_manager.py` must be extended to:
  - Collect all images in a rank sub-directory.
  - Randomly select one image per rank at game start.
  - Support animated GIF extraction (frame list stored in `ActiveArmyAssets`).
- The mod folder path is user-configurable in `config.yaml` (default:
  `~/.conquestquest/mods/`).
- The game ships with a built-in "Classic" army that cannot be overwritten.
- Invalid mods are skipped with a warning; they do not crash the application.
- Future v2.0 work may add ZIP support as an optional import step that
  auto-extracts to the mods folder, without changing the runtime format.

# Conqueror's Quest – Custom Armies (Mod System) Specification

**Document type:** Feature Specification  
**Version:** 1.0  
**Author:** Software Architect (Python Game Specialist)  
**Status:** Approved  
**Depends on:** [`architecture_overview.md`](./architecture_overview.md), [`data_models.md`](./data_models.md)

---

## 1. Purpose

This document specifies the **Custom Army Mod System** for *Conqueror's Quest*.
It defines what a mod contains, the on-disk format, how mods are discovered and
loaded at runtime, and how the game uses custom names and images during play.

---

## 2. Feature Overview

Players may create and share custom armies. Each army mod can override:

| Override | Description |
|---|---|
| **Army name** | The display name for the army (e.g., "Dragon Horde") |
| **Unit display name** | A custom label per rank type (e.g., Marshal → "Dragon Lord") |
| **Unit images** | One or more image files per rank; the game picks one at random at game start |

All other game rules (ranks, combat, movement) remain identical to the Classic
Stratego rules. Mods affect only presentation; the domain layer is unchanged.

---

## 3. Mod Directory Structure

Each army mod is a **self-contained folder** placed inside the user's
configured mod directory (default: `~/.conquestquest/mods/`).

```
mods/
└── dragon_horde/                  ← folder name = mod ID (snake_case, unique)
    ├── army.json                  ← manifest (required)
    └── images/                    ← piece images (optional; falls back to built-in)
        ├── marshal/
        │   ├── dragon_lord_1.png
        │   ├── dragon_lord_2.gif
        │   └── dragon_lord_3.png
        ├── general/
        │   └── warlord.png
        ├── spy/
        │   └── shadow.png
        └── flag/
            └── banner.gif
```

### Folder naming rules

- Must be a valid directory name (no spaces; use underscores).
- The folder name is used as the internal mod ID.
- Names must be unique within the mod directory; duplicate IDs cause the second
  mod to be skipped with a warning logged.

---

## 4. Army Manifest – `army.json`

The manifest is a JSON file that describes the army and maps each rank to
custom names and (optionally) image paths.

### 4.1 Schema

```json
{
  "mod_version": "1.0",
  "army_name": "Dragon Horde",
  "author": "PlayerOne",
  "description": "A fire-breathing army from the Eastern Mountains.",
  "units": {
    "MARSHAL":    { "display_name": "Dragon Lord" },
    "GENERAL":    { "display_name": "Warlord" },
    "COLONEL":    { "display_name": "Champion",     "display_name_plural": "Champions" },
    "MAJOR":      { "display_name": "Knight" },
    "CAPTAIN":    { "display_name": "Rider" },
    "LIEUTENANT": { "display_name": "Scout Rider" },
    "SERGEANT":   { "display_name": "Footman" },
    "MINER":      { "display_name": "Saboteur" },
    "SCOUT":      { "display_name": "Skirmisher" },
    "SPY":        { "display_name": "Shadow" },
    "BOMB":       { "display_name": "Fire Trap" },
    "FLAG":       { "display_name": "Banner" }
  }
}
```

### 4.2 Field Definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `mod_version` | string | Yes | Manifest schema version; used for forward-compatibility checks |
| `army_name` | string | Yes | Human-readable army name; shown in Army Select and Setup screens |
| `author` | string | No | Creator attribution |
| `description` | string | No | Short description shown in the army preview panel |
| `units` | object | Yes | Map of `Rank` enum name → unit customisation object |
| `units[rank].display_name` | string | Yes (per rank) | Custom name for this unit type |
| `units[rank].display_name_plural` | string | No | Plural form for multi-count pieces; defaults to `display_name + "s"` |

**Missing rank entries:** If a rank is omitted from `units`, the built-in
Classic name for that rank is used. Partially defined mods are valid.

### 4.3 Validation Rules

| Rule | Error behaviour |
|---|---|
| `army_name` must be 1–64 characters | Mod rejected; warning logged |
| `display_name` must be 1–32 characters | Fallback to Classic name; warning logged |
| `mod_version` must be `"1.0"` | Mod rejected; error logged |
| Unknown rank keys in `units` are ignored | Warning logged |
| JSON parse failure | Mod rejected; error logged |

---

## 5. Image Resolution

When the game needs to display a piece, the `SpriteManager` resolves the image
using the following priority order:

```
1. Mod images folder:   mods/<mod_id>/images/<rank_lower>/
2. Built-in assets:     assets/pieces/<rank_lower>/
```

Within the mod's images folder for a given rank, **all valid image files are
collected into a pool**. At the start of each game session, one image is drawn
at random from the pool and used for every piece of that rank for the entire
session. This ensures visual consistency within a game (all Marshals look the
same) while allowing variety across games.

### 5.1 Supported Image Formats

| Format | Extension | Notes |
|---|---|---|
| PNG | `.png` | Preferred; supports transparency |
| JPEG | `.jpg`, `.jpeg` | No transparency; not recommended for pieces |
| GIF | `.gif` | Animated GIFs are supported; animation loops during gameplay |
| BMP | `.bmp` | Supported; not recommended (large file size) |

**GIF Animation:** Animated GIFs are handled by `SpriteManager` using a
frame-timer driven by the Game Loop's `delta_time`. Each frame is extracted
at load time and stored as a list of `pygame.Surface` objects. The renderer
advances the frame index each update cycle.

### 5.2 Image Size Requirements

| Requirement | Value |
|---|---|
| Recommended size | 80 × 80 px |
| Minimum size | 16 × 16 px |
| Maximum size | 256 × 256 px |
| Aspect ratio | Square; non-square images are scaled with letterboxing |

Images outside these bounds are accepted but rescaled at load time. A warning
is logged for images exceeding the maximum size.

---

## 6. Mod Loading Lifecycle

```mermaid
sequenceDiagram
    participant App as Application Start
    participant ML as ModLoader
    participant FS as File System
    participant SM as SpriteManager
    participant Cache as ImageCache

    App->>ML: discover_mods(mod_directory)
    ML->>FS: list subdirectories
    FS-->>ML: [dragon_horde/, classic_alt/, ...]
    loop for each mod folder
        ML->>FS: read army.json
        FS-->>ML: raw JSON
        ML->>ML: validate manifest
        alt valid
            ML->>ML: build ArmyMod object
        else invalid
            ML->>ML: log warning; skip mod
        end
    end
    ML-->>App: list[ArmyMod]

    Note over App: Player selects ArmyMod on Army Select Screen

    App->>SM: preload_army(army_mod)
    loop for each rank in army_mod
        SM->>FS: list image files in images/<rank>/
        FS-->>SM: [img1.png, img2.gif, ...]
        SM->>SM: randomly select one image per rank
        SM->>Cache: load and cache Surface(s)
    end
    SM-->>App: ready
```

---

## 7. Data Models

The following models are added to `src/domain/` (see also `data_models.md`
for full domain model context).

### 7.1 `ArmyMod`

```
ArmyMod:
    mod_id: str                          # folder name; unique
    army_name: str                       # from manifest army_name
    author: str | None
    description: str | None
    unit_customisations: dict[Rank, UnitCustomisation]
    mod_directory: Path                  # absolute path to mod folder
```

### 7.2 `UnitCustomisation`

```
UnitCustomisation:
    rank: Rank
    display_name: str                    # custom name; falls back to Classic name
    display_name_plural: str             # plural form
    image_paths: list[Path]              # all valid image files found for this rank
```

### 7.3 `ActiveArmyAssets`

Resolved per game session by `SpriteManager` once an army is selected.

```
ActiveArmyAssets:
    army_mod: ArmyMod
    selected_images: dict[Rank, list[Surface]]   # frames; list length ≥ 1
    current_frame: dict[Rank, int]               # animation frame index
    frame_timers: dict[Rank, float]              # ms since last frame advance
```

---

## 8. Built-In "Classic" Army

The game ships with a built-in army called **"Classic"** that uses the standard
Stratego piece names and the default piece artwork. This army:

- Cannot be deleted or modified.
- Is always listed first in the Army Select dropdown.
- Serves as the fallback when a mod's image files are missing or invalid.

The Classic army is implemented as a hard-coded `ArmyMod` object in
`src/domain/classic_army.py`, not loaded from disk.

---

## 9. Module Responsibilities

| Module | Responsibility |
|---|---|
| `src/infrastructure/mod_loader.py` | Discovers and parses mod folders; returns `list[ArmyMod]` |
| `src/infrastructure/mod_validator.py` | Validates `army.json` against the schema; returns validation errors |
| `src/presentation/sprite_manager.py` | Resolves images for a selected army; handles GIF frame extraction and animation |
| `src/domain/classic_army.py` | Defines the built-in Classic army as a static `ArmyMod` |
| `src/presentation/screens/army_select_screen.py` | Presents loaded armies; shows preview panel |

---

## 10. Security Considerations

| Risk | Mitigation |
|---|---|
| Malicious `army.json` with overly long strings | Field length limits validated at parse time |
| Path traversal via image filenames | `SpriteManager` resolves all paths relative to the mod folder; absolute paths in `army.json` are rejected |
| Malformed/corrupted image files | Wrapped in `try/except`; fallback to Classic image; error logged |
| Executable content disguised as image | Only listed image extensions are loaded; no execution of file contents |

---

## 11. Future Extensions (v2.0)

| Extension | Description |
|---|---|
| **Mod marketplace** | In-game download of community mods (requires network adapter extension) |
| **Board skin mods** | Mods that override board background and lake textures |
| **Sound packs** | Custom combat and movement sound effects per army |
| **Unit ability overrides** | Safely sandboxed scripting to alter piece behaviour (requires security review) |

---

## 12. Related Documents

| Document | Purpose |
|---|---|
| [`architecture_overview.md`](./architecture_overview.md) | Layer boundaries (mods are Infrastructure + Presentation only) |
| [`data_models.md`](./data_models.md) | Full domain model; `ArmyMod` relationship to `GameState` |
| [`screen_flow.md`](./screen_flow.md) | How Army Select Screen integrates with the screen flow |
| [`technology_stack.md`](./technology_stack.md) | pygame-ce and image format support |
| [`adr/ADR-006-custom-army-mod-system.md`](./adr/ADR-006-custom-army-mod-system.md) | Decision record for mod format choice |

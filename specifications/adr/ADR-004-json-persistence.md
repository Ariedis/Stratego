# ADR-004: JSON for Save-Game Persistence

**Status:** Accepted  
**Date:** 2026-02-21  
**Author:** Software Architect (Python Game Specialist)

---

## Context

Save games must be written to and read from disk. We need to select a
serialisation format and strategy.

## Decision

**Use JSON with a versioned schema for save-game files. Python's standard
library `json` module handles serialisation; a custom encoder/decoder handles
domain types (Enums, dataclasses).**

## Rationale

1. **Human-readable:** JSON files can be opened in any text editor for
   debugging. This is invaluable during development and for power users.

2. **No extra dependencies:** `json` is a Python standard library module.
   No additional packages required for the core persistence feature.

3. **Versioned schema:** Including a `"version"` key in the root object
   enables schema migration as the data model evolves. The infrastructure
   layer reads the version and applies the appropriate deserialiser.

4. **Security:** JSON deserialisation with a schema validator is safe. Pickle
   was explicitly rejected because `pickle.load()` can execute arbitrary code
   if the save file is tampered with (a known Python security risk documented
   in the official docs and countless security advisories).

5. **Portability:** JSON files are cross-platform and encoding-agnostic
   (UTF-8). Binary formats would require endianness handling.

## Alternatives Considered

| Format | Outcome |
|---|---|
| `pickle` | **Rejected – security risk.** Deserialising a malicious pickle file executes arbitrary code. Not acceptable for a save format users may share. |
| Protocol Buffers | Schema evolution support is excellent but adds a build step and `protobuf` dependency. Excessive for a local save format. |
| SQLite | Appropriate for complex relational save data (e.g., RPG with inventory). Overkill for a single serialised object. |
| YAML | More expressive than JSON but adds a `PyYAML` dependency and YAML's implicit type coercion is a known source of bugs. |
| MessagePack | Binary, compact, fast. Not human-readable; debugging saved games would be harder. Acceptable for v2.0 if file size becomes a concern. |

## Consequences

- Save files are `~/.stratego/saves/<name>.json`.
- The `json_repository.py` infrastructure module owns all encode/decode logic.
- Domain layer objects have no `json` import; they are plain dataclasses.
- Schema migration: if the data model changes, the version number is bumped
  and a migration function is added to `json_repository.py`.
- **Security note:** The repository must validate JSON against the schema
  before constructing domain objects, to reject malformed or malicious input.

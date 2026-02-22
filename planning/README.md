# Planning

This directory contains all planning artefacts produced by the **Senior
Business Analyst** agent.

## Contents

Planning documents are organised as follows:

```
planning/
├── README.md               ← this file
├── backlog/                ← prioritised backlog and epics
├── user-stories/           ← individual user story files
└── sprints/                ← sprint plans and iteration goals
```

## Conventions

- All documents are Markdown.
- User stories follow the format:
  > **As a** [persona], **I want** [capability], **so that** [benefit].
- Acceptance criteria use Given / When / Then (GWT) where applicable.
- MoSCoW prioritisation is used throughout:
  **Must Have**, **Should Have**, **Could Have**, **Won't Have**.
- Every artefact references the `/specifications` document it derives from.

## Related Documents

| Document | Purpose |
|---|---|
| [`/specifications/architecture_overview.md`](../specifications/architecture_overview.md) | High-level system architecture |
| [`/specifications/game_components.md`](../specifications/game_components.md) | Authoritative game rules |
| [`/specifications/data_models.md`](../specifications/data_models.md) | Domain model definitions |
| [`/specifications/system_design.md`](../specifications/system_design.md) | Module-level design |
| [`/specifications/ai_strategy.md`](../specifications/ai_strategy.md) | AI algorithm design |
| [`/specifications/screen_flow.md`](../specifications/screen_flow.md) | Screen navigation specification |
| [`/specifications/custom_armies.md`](../specifications/custom_armies.md) | Custom army mod system |
| [`/specifications/technology_stack.md`](../specifications/technology_stack.md) | Library and tooling choices |

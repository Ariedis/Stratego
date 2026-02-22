# Planning

This directory contains all planning artefacts produced by the **Senior
Business Analyst** agent.

## Contents

Planning documents are organised as follows:

```
planning/
├── README.md                                     ← this file
├── implementation-plan.md                        ← master phased roadmap
├── epics.md                                      ← full epic catalogue
├── product-backlog.md                            ← prioritised backlog
├── user-stories-epic-1-foundation.md             ← EPIC-1 user stories
├── user-stories-epic-2-domain-layer.md           ← EPIC-2 user stories
├── user-stories-epic-3-application-layer.md      ← EPIC-3 user stories
├── user-stories-epic-4-presentation-layer.md     ← EPIC-4 user stories
├── user-stories-epic-5-ai-layer.md               ← EPIC-5 user stories
├── user-stories-epic-6-infrastructure.md         ← EPIC-6 user stories
├── user-stories-epic-7-custom-armies.md          ← EPIC-7 user stories
├── sprint-phase-1-foundation.md                  ← sprint plan – Phase 1
├── sprint-phase-2-core-game-rules.md             ← sprint plan – Phase 2
├── sprint-phase-3-application-layer.md           ← sprint plan – Phase 3
├── sprint-phase-4-presentation-layer.md          ← sprint plan – Phase 4
├── sprint-phase-5-ai-layer.md                    ← sprint plan – Phase 5
├── sprint-phase-6-infrastructure.md              ← sprint plan – Phase 6
└── sprint-phase-7-custom-armies-and-polish.md    ← sprint plan – Phase 7
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

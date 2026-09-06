# STRUCTURE

**Analysis Date:** 2026-09-06

## Top-Level Layout

```
AgentControlTower/                          # root = fork of entireio/cli
├── agent-control-tower/                    # ★ the hackathon product lives here
│   ├── backend/                            # FastAPI service
│   ├── frontend/                           # React/Vite UI
│   ├── README.md                           # product README, version status
│   ├── .gitignore
│   └── .gitattributes
├── Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip   # planning doc bundle (PRD, build map, etc.)
├── cmd/entire/                             # root CLI entry point (Go)
├── cmd/git-remote-entire/                  # git remote helper (Go)
├── internal/                               # coreapi, entireclient, procsignal, remotehelper, testdirs (Go)
├── redact/                                 # redaction engine (Go)
├── perf/                                   # perf instrumentation (Go)
├── e2e/                                    # E2E test suite for the CLI (Go)
├── docs/                                   # root CLI architecture docs
├── scripts/                                # installer/dev scripts (bash, ps1)
├── mise-tasks/                             # mise task definitions
├── tools/                                  # complexity analysis tool (Go)
├── api/checkpoint/                         # checkpoint API types (Go)
├── go.mod / go.sum                         # root CLI Go module
├── mise.toml                               # toolchain + task config
├── CLAUDE.md                               # root CLI's exhaustive architecture doc (116KB)
├── .entire/                                # Entire's own runtime state for this repo (settings.json, runners/)
└── .planning/                              # ★ GSD planning artifacts (this document lives here)
    └── codebase/                           # this directory
```

**Everything under `agent-control-tower/` is the product under active development for this hackathon.** Everything else at the root (`cmd/`, `internal/`, `redact/`, `e2e/`, etc.) is the vendored/forked `entireio/cli` codebase, present because the hackathon requires dogfooding Entire on its own fork, not because this project modifies it.

## `agent-control-tower/backend/` Layout

```
backend/
├── app/
│   ├── __init__.py          # empty (package marker only)
│   ├── main.py               # FastAPI app + all 3 routes
│   ├── config.py             # Settings singleton (env-driven)
│   └── entire_client.py      # subprocess wrapper around `entire` CLI
├── tests/
│   ├── test_health.py        # tests /health and /version
│   └── test_entire_client.py # tests run_json/list_checkpoints via monkeypatched subprocess
├── pyproject.toml            # package metadata, deps, pytest config
└── .env.example               # documents ACT_REPO_ROOT / ACT_ENTIRE_BIN
```

No `routers/`, `services/`, `models/`, or `schemas/` subpackages yet — everything lives flat in `app/` because there are only 3 endpoints and one integration module. This will likely need restructuring once V1+ adds `checkpoint_ingestor`, `event_normalizer`, `agent_registry`, etc. per the build map's planned module list.

## `agent-control-tower/frontend/` Layout

```
frontend/
├── src/
│   ├── main.tsx              # React root
│   ├── App.tsx               # default Vite/React starter content (not yet product UI)
│   ├── App.css
│   ├── index.css
│   └── assets/                # hero.png, react.svg, etc. (starter assets)
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── index.html
├── package.json
├── package-lock.json
├── vite.config.ts
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── .oxlintrc.json
└── README.md                  # Vite's own generated README (not product-specific)
```

No `components/`, `hooks/`, `api/`, or `pages/` directories yet — this is an unmodified Vite scaffold. Per the build map's planned component list (`ControlTower`, `AgentWorld`, `AgentNode`, `AgentDetailsPanel`, `CommitInspector`, `StatusBadge`, `HandoffPanel`, `CheckpointList`), a `src/components/` directory will likely be the first structural addition in V1.

## Naming Conventions Observed

- **Backend:** snake_case for files and functions (`entire_client.py`, `list_checkpoints`, `run_json`) — standard Python/PEP8 style.
- **Frontend:** PascalCase for component files (`App.tsx`), camelCase for functions/variables — standard React/TS style.
- **Planned module names** (from build map) follow `snake_case_service.py` pattern for backend (`checkpoint_ingestor`, `analysis_service`, `handoff_service`) and `PascalCase` for frontend components — consistent with what's already in place.

## Where to Add New Code

- New backend endpoints → likely warrant splitting `main.py` into `app/routers/` once endpoint count grows past ~5; for now, adding directly to `main.py` matches existing style.
- New backend business logic (normalization, analysis) → new modules in `app/` following the `entire_client.py` pattern (one file per concern, functions not classes).
- New frontend UI → `frontend/src/components/` (does not exist yet — first component added should create it).
- Planning/roadmap docs → `.planning/` (this GSD structure), separate from the hackathon's own doc stack in `Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip` (PRD, build map, task execution plan, etc. — extracted ad hoc to `/tmp/hackdoc` during this analysis, not committed anywhere in-repo as loose files).

---
*Generated by codebase mapping analysis: 2026-09-06*

# ARCHITECTURE

**Analysis Date:** 2026-09-06

## Overview

This repository contains **two architecturally independent systems** sharing one git tree:

1. The **root Go CLI** (`entireio/cli`, "Entire") — a large, mature Cobra-based CLI with a highly structured filesystem-safety and git-plumbing architecture (documented exhaustively in the root `CLAUDE.md`). It is dogfooded to track the hackathon project's own dev sessions but is not itself the hackathon deliverable.
2. **`agent-control-tower/`** — the hackathon product, a client/server web app: FastAPI backend + React/Vite frontend, currently at **V0 (Foundation)** per the versioned build map extracted from `Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip`.

This document focuses on `agent-control-tower/`'s architecture since that is the active development target; the root CLI's architecture is exhaustively documented in the root `CLAUDE.md` (root anchors, checkpoint strategy, git safety rules, etc.) and is treated as a vendored/forked dependency, not something this project modifies as its primary deliverable.

## Target System Design (from hackathon build map, `02_BUILD_MAP.md`)

The intended end-state data flow (most of this is **not yet built** — V0 has only the shells):

```
Entire Checkpoints ──→ Checkpoint Collector ──→ Normalizer ──→ Runtime State
                                                                    │
Entire Graph ───────→ Graph Client ────────────────────────────────┤
                                                                    ↓
                                                              Analysis Engine
                                                        ┌───────────┼───────────┐
                                                        ↓           ↓           ↓
                                                     Intent       Status      Evidence
                                                        │           │
                                                        └──────┬────┘
                                                               ↓
                                                               API
                                                               ↓
                                                         Control Tower
                                                               │
                               ┌────────────────────────────────┼─────────────────────┐
                               ↓                                ↓                     ↓
                         Understanding                     Recovery             Reconstruction
```

Backend modules planned (per build map, "Later modules" not yet present): `checkpoint_ingestor`, `event_normalizer`, `agent_registry`, `analysis_service`, `status_service`, `commit_explainer`, `handoff_service`, `graph_service`, then later `reconstruction_service`, `conflict_service`, `trust_score_service`, `databricks_service`, `fidelity_runner`, `replay_service`.

Frontend components planned (not yet present beyond the Vite starter): `ControlTower`, `AgentWorld`, `AgentNode`, `AgentDetailsPanel`, `CommitInspector`, `StatusBadge`, `HandoffPanel`, `CheckpointList`, then later `ReconstructionPromptPanel`, `ConflictWarningBanner`, `TrustScoreBadge`, `CheckpointTimeline`, `HistoricalMatchPanel`, `AggregateInsightsPanel`.

## Current Architecture (V0 — what actually exists today)

### Backend (`agent-control-tower/backend/app/`)

A minimal 3-file FastAPI app, no layering beyond a single-file router plus one integration module:

- **`main.py`** — single `FastAPI` app instance with 3 routes, all defined inline (no router modules, no dependency injection framework beyond FastAPI's own):
  - `GET /health` → returns `{status, repo_root}` (`app/main.py:9-14`)
  - `GET /version` → returns `{version: "0.1.0"}` (`app/main.py:17-19`)
  - `GET /api/checkpoints` → delegates to `entire_client.list_checkpoints()` (`app/main.py:22-24`)
- **`config.py`** — a module-level `Settings` singleton (`settings = Settings()`), reading `ACT_REPO_ROOT` / `ACT_ENTIRE_BIN` from env at import time. No pydantic `BaseSettings` used despite pydantic being a dependency — this is a plain class.
- **`entire_client.py`** — the sole integration boundary. Every fact the backend derives from Entire flows through `run_json()`, which is a direct, synchronous `subprocess.run(..., timeout=30)` call. Two thin wrappers (`list_checkpoints`, `status`) sit on top. Custom exception `EntireCommandError` carries args/returncode/stderr for callers to handle. Docstring explicitly states the single-chokepoint intent: "there is exactly one place that knows how to invoke the CLI and parse its output."

This is a flat, unlayered architecture appropriate for V0 — there is no service layer, no dependency injection, no async I/O (subprocess call is blocking despite FastAPI being async-capable), and no persistence. This matches the build map's explicit philosophy: "Build vertically... Each version is a complete runnable increment. Do not ask Claude Code to implement the entire roadmap in one pass."

### Frontend (`agent-control-tower/frontend/src/`)

Default Vite + React + TypeScript starter template, **not yet customized** for the product:
- `main.tsx` — React root mount
- `App.tsx` — default Vite/React demo content (hero image, counter button, "Explore Vite"/"Learn more" links) — none of the planned `ControlTower`/`AgentWorld`/etc. components exist yet
- `App.css`, `index.css` — starter styles
- No API client, no fetch/axios calls to the backend, no routing library, no state management library beyond React's built-in `useState`

### Entry Points

- Backend: `uvicorn app.main:app` (from `agent-control-tower/backend/`)
- Frontend: `npm run dev` (Vite dev server) or `npm run build` (production bundle to `dist/`)
- No process manager/orchestration ties the two together yet (no docker-compose, no Procfile in `agent-control-tower/`) — they are run as two independent local processes per the README instructions.

## Data Flow (current, V0)

```
Browser ──(none yet)──> Frontend (Vite/React, static demo)

Client ──HTTP──> FastAPI (main.py)
                    ├─ /health, /version → pure Python, no external calls
                    └─ /api/checkpoints → entire_client.run_json(["checkpoint","list","--json"])
                                             └─ subprocess → `entire` binary (not present in this env)
```

There is currently no live data flow between frontend and backend — that wiring is scoped to V1 per the build map.

## Key Architectural Decisions Evident in Code

1. **Single chokepoint for the CLI boundary** (`entire_client.py`) — mirrors the root CLI's own philosophy of funneling filesystem/git access through single owning packages (see root `CLAUDE.md`, "The Root Anchors" section) even though this is a much smaller, unrelated codebase. Good practice carried over.
2. **Settings via environment, not config files** — `ACT_REPO_ROOT`/`ACT_ENTIRE_BIN`, defaulting to sane values (cwd, `"entire"` on PATH) so the backend can be pointed at any Entire-enabled repo without code changes.
3. **Fork-and-subdirectory placement** — the product intentionally lives inside a fork of `entireio/cli` rather than a standalone repo, per the hackathon's required "Entire mirror/fork workflow" (stated explicitly in `agent-control-tower/README.md`). This means `agent-control-tower/` should be treated as a self-contained subtree; changes to the surrounding root CLI code are out of scope for this project's own build map.

---
*Generated by codebase mapping analysis: 2026-09-06*

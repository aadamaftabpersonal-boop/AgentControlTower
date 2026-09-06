# Agent Control Tower

## What This Is

Agent Control Tower is a live, checkpoint-native developer experience for supervising multiple AI coding agents. It turns evidence captured by Entire (checkpoints and graph) into a visual control room showing what each agent is doing, whether its work matches its original objective, and what to do when it fails or gets stuck. This build targets **V1 — Single Agent Control Tower**: real checkpoint ingestion feeding a live dashboard with one observable agent node. V0 (repo scaffolding, FastAPI backend shell, Vite/React frontend shell, Entire CLI wired in) is already built.

## Core Value

The dashboard must show a real Claude Code session's checkpoint the moment it's created — no invented or synthetic agent state. Entire Checkpoints are the factual source of truth; nothing is fabricated to look impressive in a demo.

## Business Context

- **Customer**: Hackathon judges and the team itself, evaluating a working demo
- **Revenue model**: N/A — hackathon submission, not a monetized product
- **Success metric**: A real Claude Code session creates a checkpoint that appears live in the dashboard (V1's stated "done" condition from the PRD)
- **Strategy notes**: Full product vision and version roadmap (V0–V15+) captured in `Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip` at the repo root — this GSD roadmap scopes only V1; later versions (LLM understanding, Graph intelligence, handoff, reconstruction) are deliberately out of scope for now and should be started as new milestones off that doc stack.

## Requirements

### Validated

- ✓ Repository structure (fork of `entireio/cli` with `agent-control-tower/` subtree) — V0
- ✓ FastAPI backend shell with `/health`, `/version`, `/api/checkpoints` routes — V0
- ✓ React/Vite/TypeScript frontend shell (unstyled starter) — V0
- ✓ Single chokepoint `entire_client.py` wrapping the `entire` CLI via subprocess — V0
- ✓ Entire CLI setup and checkpoint capability enabled on this repo — V0

### Active

- [ ] Real Entire checkpoint ingestion (backend reads actual checkpoint data, not just a passthrough of `entire checkpoint list --json`)
- [ ] Checkpoint parser / normalized data model (Agent, Checkpoint per the technical spec's core data model)
- [ ] Agent registry / live state (in-memory or lightweight local store, no DB yet)
- [ ] Control Tower dashboard (frontend replacing the Vite starter with a real UI)
- [ ] One live Agent Node showing: objective, status placeholder, current activity, latest checkpoint
- [ ] Live update mechanism from backend to frontend (SSE per technical spec, not polling)

### Out of Scope

- LLM-based commit/agent explanation (V3) — deferred; no LLM interpretation layer needed until intent-vs-actual analysis is in scope
- Entire Graph integration (V5) — deferred; not needed for single-agent live dashboard
- Multi-agent / two-agent live world (V8) — deferred; V1 is explicitly single-agent
- Checkpoint reconstruction, handoff generation, collision detection, evidence scoring, timeline, Databricks memory, replay (V6–V14) — deferred; these are later milestones per the existing doc stack roadmap
- WebSockets — SSE is the explicit architecture decision for the live event stream (simpler to debug within hackathon timeframe)
- Persistent database — local/in-memory runtime state is sufficient per the technical spec; V1 does not require durable storage

## Context

- **Repo shape**: This is a fork of `entireio/cli` (a mature Go CLI, documented in the root `CLAUDE.md`). `agent-control-tower/` is a self-contained subtree — the hackathon deliverable. Changes to the root Go CLI are out of scope for this project.
- **Existing docs**: A versioned doc stack (`Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip`) already contains a full PRD, technical spec, UX map, task execution plan, design spec, test plan, demo script, and version roadmap (V0–V15+). This PROJECT.md scopes V1 only; consult the doc stack directly for V2+ detail rather than re-deriving it.
- **Dev workflow constraint**: The hackathon requires developing through Claude Code using the Entire mirror/fork workflow — this is a hard constraint on *how* the code gets written, not a product feature.
- **Timeline**: Tight — hours remain in the hackathon window. Bias toward the smallest coherent V1 slice that satisfies its stated "done" condition over broader but shakier scope.
- **Codebase map available**: `.planning/codebase/` has ARCHITECTURE.md, STACK.md, STRUCTURE.md, CONVENTIONS.md, INTEGRATIONS.md, TESTING.md, CONCERNS.md from an automated scan — read these before planning phase 1.

## Constraints

- **Timeline**: Hackathon deadline, hours remaining — favor coarse phases and minimal process ceremony over thoroughness
- **Tech stack**: React + TypeScript + Vite frontend, Python + FastAPI backend, SSE for live updates — locked by the existing technical spec, not open for reconsideration in this milestone
- **Source of truth**: Every fact shown in the UI must trace back to real `entire` CLI output — no synthetic/invented agent history, per the PRD's "Checkpoint-native" and "Honest uncertainty" principles
- **Scope boundary**: This milestone stops at V1. Do not pull in V2+ capabilities (inspection panels, LLM analysis, Graph) even if they seem easy — they're separate milestones by design

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Scope this milestone to V1 only | Tight hackathon timeline; V0 already done; PRD defines V1's own "done" condition independently of later versions | — Pending |
| Use SSE, not WebSockets, for live updates | Explicit architecture decision in the existing technical spec — simpler to debug under time pressure | — Pending |
| No LLM layer in this milestone | LLM interpretation (V3) requires the evidence pipeline (V1/V2) to exist first; adding it now would violate "deterministic facts before LLM interpretation" | — Pending |
| Claude (Anthropic API) will be the LLM provider when V3 is eventually planned | Consistent with using Claude Code as the dev agent; noted now so a future milestone doesn't need to re-decide | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-06 after initialization*

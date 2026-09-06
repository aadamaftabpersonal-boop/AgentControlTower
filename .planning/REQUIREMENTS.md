# Requirements: Agent Control Tower

**Defined:** 2026-09-06
**Core Value:** The dashboard must show a real Claude Code session's checkpoint the moment it's created — no invented or synthetic agent state.

## v1 Requirements

Requirements for the V1 "Single Agent Control Tower" milestone. Each maps to a roadmap phase.

### Ingestion

- [ ] **INGEST-01**: Backend can invoke `entire checkpoint list --json` (via `entire_client.py`) and parse real checkpoint records without error
- [ ] **INGEST-02**: Each raw checkpoint is normalized into the `Checkpoint` data model (checkpoint_id, agent_id, session_id, timestamp, prompt, transcript, files_touched, tool_calls, commits, metadata) as defined in the technical spec
- [ ] **INGEST-03**: Ingestion handles the "no checkpoints yet" case explicitly (`WAITING FOR AGENT ACTIVITY`), not a crash or empty-object silently rendered as success
- [ ] **INGEST-04**: Ingestion handles a malformed/partial checkpoint record explicitly (`INSUFFICIENT EVIDENCE`), never inventing missing fields

### Registry

- [ ] **REGISTRY-01**: Backend maintains an in-memory Agent registry keyed by `agent_id`/`session_id` (no persistent DB required for V1)
- [ ] **REGISTRY-02**: Each Agent record tracks objective, status placeholder, current_activity, current_files, latest_checkpoint_id, commit_ids, created_at, updated_at per the technical spec's Agent model
- [ ] **REGISTRY-03**: New checkpoints update the corresponding Agent record's `latest_checkpoint_id`, `current_activity`, and `updated_at`

### API

- [ ] **API-01**: `GET /api/checkpoints` returns real normalized checkpoint data (not a raw passthrough) sourced from the Agent registry
- [ ] **API-02**: A new `GET /api/agents` endpoint returns the current Agent registry state
- [ ] **API-03**: A live-update endpoint streams new checkpoint/agent events via Server-Sent Events (SSE), not WebSockets, per the locked architecture decision

### Dashboard

- [ ] **DASH-01**: Frontend replaces the default Vite/React starter content with a real Control Tower layout
- [ ] **DASH-02**: Frontend renders one live Agent Node showing objective, status placeholder, current activity, and latest checkpoint
- [ ] **DASH-03**: Frontend shows an explicit "waiting for agent activity" state when no checkpoints exist yet, matching the backend's failure-philosophy contract

### Live Updates

- [ ] **LIVE-01**: Frontend subscribes to the backend's SSE stream and updates the Agent Node in place when a new checkpoint arrives, without a manual page refresh
- [ ] **LIVE-02**: A dropped/reconnecting SSE connection is surfaced to the user rather than silently freezing the last-seen state with no indication it's stale

## v2 Requirements

Deferred to future milestones. Tracked but not in the current roadmap. Full detail lives in the existing doc stack (`Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip`).

### Inspection (V2)

- **INSPECT-01**: Clickable Agent Node opens a detail panel
- **INSPECT-02**: Detail panel shows original prompt/objective, files touched, tool activity, commits, checkpoint trail

### LLM Understanding (V3)

- **LLM-01**: Commit explanation grounded in real checkpoint evidence
- **LLM-02**: Agent accomplishment summary
- **LLM-03**: Intent-vs-actual analysis with evidence references in every explanation
- **LLM-04**: LLM provider is Claude (Anthropic API), consistent with using Claude Code as the dev agent

### Status Intelligence (V4)

- **STATUS-01**: ON TRACK / STUCK / DONE / DRIFTING status derivation with evidence-backed reasons

### Graph Intelligence (V5)

- **GRAPH-01**: Entire Graph client integration
- **GRAPH-02**: Blast-radius / impact analysis for stuck diagnosis

### Handoff (V6)

- **HANDOFF-01**: Checkpoint-grounded continuation prompt generator

### Reconstruction (V7 — hero feature)

- **RECON-01**: Select-a-checkpoint reconstruction prompt generator with a hard chronological cutoff (no later-checkpoint facts leak in), labeled `UNVERIFIED` until replay fidelity exists

### Multi-Agent (V8–V9)

- **MULTI-01**: Two concurrent live agent sessions with isolated histories
- **COLLISION-01**: Graph-backed detection of agents touching related files/functions

### Trust & Timeline (V10–V11)

- **TRUST-01**: Deterministic evidence score (checkpoint completeness + Graph verification + test pass rate)
- **TIMELINE-01**: Interactive checkpoint timeline tied to inspection and reconstruction

### Historical Memory & Verification (V12–V14)

- **HIST-01**: Databricks-backed historical checkpoint memory and cross-session aggregate insights
- **VERIFY-01**: Fresh-agent replay compared against source checkpoint with fidelity metrics
- **REPLAY-01**: One-click checkpoint replay in a fresh session

## Out of Scope

Explicitly excluded from this V1 milestone. Documented to prevent scope creep during a tight timeline.

| Feature | Reason |
|---------|--------|
| WebSockets for live updates | Technical spec locks SSE as the architecture decision — simpler to debug under time pressure |
| Persistent database (Postgres, SQLite, etc.) | V1's runtime state is in-memory only per the technical spec; durable storage isn't needed until later milestones (if ever) |
| Any LLM interpretation layer | Violates "deterministic facts before LLM interpretation" — the evidence pipeline (this milestone) must exist first |
| Entire Graph integration | Not needed for a single-agent live dashboard; scoped to V5 |
| Multi-agent support | V1 is explicitly single-agent per the PRD's own version definition |
| Authentication / multi-user access control | Not mentioned anywhere in the PRD; single local demo user assumed for the hackathon |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Pending |
| INGEST-02 | Phase 1 | Pending |
| INGEST-03 | Phase 1 | Pending |
| INGEST-04 | Phase 1 | Pending |
| REGISTRY-01 | Phase 2 | Pending |
| REGISTRY-02 | Phase 2 | Pending |
| REGISTRY-03 | Phase 2 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 3 | Pending |
| LIVE-01 | Phase 3 | Pending |
| LIVE-02 | Phase 3 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-06*
*Last updated: 2026-09-06 after initial definition*

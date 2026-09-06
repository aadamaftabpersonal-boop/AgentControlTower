# Roadmap: Agent Control Tower

**Milestone:** V1 — Single Agent Control Tower
**Granularity:** Coarse (tight hackathon timeline)
**Mode:** Vertical MVP slices

## Phase 1: Real Checkpoint Ingestion
**Goal:** Backend reads and normalizes real Entire checkpoint data instead of passing through raw CLI output.
**Mode:** mvp
**Requirements:** INGEST-01, INGEST-02, INGEST-03, INGEST-04
**Success Criteria**:
1. Calling the ingestion path against a repo with real `entire` checkpoints returns normalized `Checkpoint` objects matching the technical spec's field list
2. Calling it against a repo with zero checkpoints returns an explicit `WAITING FOR AGENT ACTIVITY` result, not an exception or empty 200
3. A deliberately malformed/partial checkpoint record is handled as `INSUFFICIENT EVIDENCE`, never silently dropped or filled with invented values
4. Existing `/health`, `/version` routes still work unchanged

## Phase 2: Agent Registry & Read APIs
**Goal:** Backend maintains live Agent state derived from ingested checkpoints and exposes it over HTTP.
**Mode:** mvp
**Requirements:** REGISTRY-01, REGISTRY-02, REGISTRY-03, API-01, API-02
**Success Criteria**:
1. An in-memory Agent registry exists, keyed by agent_id/session_id, holding the fields from the technical spec's Agent model
2. Ingesting a new checkpoint for a known session updates that Agent's `latest_checkpoint_id`, `current_activity`, and `updated_at`
3. `GET /api/agents` returns the current registry contents as JSON
4. `GET /api/checkpoints` returns normalized checkpoint data sourced through the registry/ingestion pipeline built in Phase 1, not a raw CLI passthrough

## Phase 3: Live Updates (SSE)
**Goal:** Frontend receives new checkpoint/agent events in real time without polling or manual refresh.
**Mode:** mvp
**Requirements:** API-03, LIVE-01, LIVE-02
**Success Criteria**:
1. A backend SSE endpoint streams agent/checkpoint update events as they occur
2. A running frontend client updates its local state when an event arrives, with no page reload
3. If the SSE connection drops, the frontend surfaces a visible "disconnected/reconnecting" indicator rather than silently freezing on stale data
4. Manually triggering a new checkpoint (e.g. via a real Claude Code session) is observable end-to-end through the stream within a few seconds

## Phase 4: Control Tower Dashboard
**Goal:** The Vite starter is replaced with a real dashboard showing one live Agent Node, satisfying V1's stated "done" condition.
**Mode:** mvp
**Requirements:** DASH-01, DASH-02, DASH-03
**Success Criteria**:
1. The default Vite/React demo content (hero image, counter button, "Explore Vite" links) is gone
2. The dashboard renders one Agent Node showing objective, status placeholder, current activity, and latest checkpoint, wired to the Phase 2 APIs and Phase 3 live stream
3. With zero checkpoints, the dashboard shows an explicit waiting state instead of a blank or broken screen
4. A real Claude Code session's checkpoint appears in the dashboard without a manual refresh — the milestone's own "done" condition from the PRD

---
*Roadmap created: 2026-09-06*
*4 phases | 15 requirements mapped | 0 unmapped*

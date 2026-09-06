# Phase 1: Real Checkpoint Ingestion - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Backend reads and normalizes real Entire checkpoint data instead of passing through raw CLI output. Covers INGEST-01 through INGEST-04. Does NOT cover the Agent registry, HTTP API surface, SSE, or dashboard — those are Phases 2-4.

</domain>

<decisions>
## Implementation Decisions

### Checkpoint data source
- **D-01:** Ingest the **pending** dataset (`entire checkpoint list --pending --json`), not the committed/condensed dataset (`entire checkpoint list --json` without `--pending`). — **Reversibility:** costly — **rationale:** the whole normalization/registry layer downstream keys off the pending shape (`pendingCheckpointJSON`: id, message, metadata_dir, date, is_task_checkpoint, tool_use_id, is_logs_only, condensation_id, session_id, session_prompt), which differs from the condensed shape (`branchCheckpointJSON`: checkpoint_id, session_id, agent, date, message, is_task_checkpoint, is_logs_only, session_count, session_ids). Switching later means re-deriving the normalizer and registry update logic against a different field set.
  - **Why:** the condensed dataset (plain `checkpoint list --json`) only contains checkpoints already written to `entire/checkpoints/v1` — which happens on `git commit`, per the root CLI's manual-commit strategy. PROJECT.md's core value ("dashboard must show a real Claude Code session's checkpoint the moment it's created") is not satisfiable with the condensed dataset alone: the dashboard would look frozen for the length of an entire agent turn, then jump on commit. `--pending` surfaces live shadow-branch checkpoints (not yet condensed) plus logs-only resume points, matching what "live" actually means here.
  - **Known gap this decision creates:** pending entries for live (uncommitted) checkpoints have an **empty `condensation_id`** (`CheckpointID` is only populated for logs-only points already condensed elsewhere — see `pendingCheckpointJSON.CondensationID` in `cmd/entire/cli/checkpoint_list.go`). This directly conflicts with D-02 below for those entries — flagged there.

### Field depth
- **D-02:** Fetch full per-checkpoint detail via `entire checkpoint explain <id> --json` in addition to the pending list, to populate files_touched, session summaries, etc. — **Reversibility:** reversible — pure additive enrichment on top of the pending list; can be dropped back to list-only fields without touching the registry's identity/keying logic.
  - **Known conflict with D-01:** `explain <id>` requires a resolvable checkpoint ID. Live (uncommitted) pending entries from D-01 have an empty `condensation_id`, so they have **no ID to call `explain` with yet**. Researcher/planner must resolve this — likely: call `explain` only for pending entries that DO carry a non-empty `condensation_id` (logs-only points), and normalize live/uncommitted entries using list-level fields only (message, date, session_prompt, is_task_checkpoint) until they condense. Document this fallback explicitly in the Checkpoint model rather than treating it as an edge case to special-case ad hoc.
  - Real CLI output (`checkpointExportJSON` in `cmd/entire/cli/explain_export.go`) does not literally match the technical spec's idealized Checkpoint fields (`prompt`, `transcript`, `tool_calls`, `commits` as flat fields) — it has `sessions[]` with `summary.intent`/`summary.outcome`, `files_touched`, `token_usage`, but no raw transcript or tool-call list. The normalized Checkpoint model should be built from what the real CLI actually emits, not from the tech spec's field names verbatim — treat the tech spec as directional, not a literal schema to force-fit.

### Malformed/partial checkpoint handling (INGEST-04)
- **D-03:** Treat the CLI's own documented partial signals as the real-world "malformed" case — `checkpointExportJSON.partial: true` plus per-session `error` strings (`checkpointSessionJSON.error`), and any pending entry missing an expected required field (empty `id`/`date`) if ever observed. — **Reversibility:** reversible.
  - No synthetic bad-JSON fixture is needed for the live demo path itself. Use a hand-crafted malformed fixture only in automated unit tests for the normalizer, to exercise INSUFFICIENT EVIDENCE deterministically without depending on the CLI ever actually emitting a partial result live.

### Binary/subprocess failure handling
- **D-04:** Fixing the existing bare-500 behavior when the `entire` binary is missing or fails (CONCERNS.md #1) is explicitly **out of scope for Phase 1**. — **Reversibility:** reversible.
  - Ingestion code should still not crash uncaught on `EntireCommandError`/`FileNotFoundError`/`subprocess.TimeoutExpired` — it's fine (and expected) for these to propagate as errors for now, distinct from the `WAITING FOR AGENT ACTIVITY` (zero checkpoints) and `INSUFFICIENT EVIDENCE` (malformed record) cases defined in INGEST-03/04. Structured error responses for binary failures are deferred to a later phase.

### Claude's Discretion
- Exact normalized `Checkpoint` Python model/dataclass shape (field names, types) beyond what D-01/D-02 constrain.
- Whether normalization lives in a new module (e.g. `normalizer.py`) vs. inline in `entire_client.py` — planner's call based on the single-chokepoint pattern already established.
- Test fixture format/location for the malformed-checkpoint unit test from D-03.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product/requirements
- `.planning/PROJECT.md` — core value, V1 scope, constraints
- `.planning/REQUIREMENTS.md` — INGEST-01..04 full text
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria

### Existing doc stack (hackathon PRD/tech spec, extracted from repo-root zip)
- `Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip` → `04_TECHNICAL_SPEC.md` — Core Data Model (§4, Checkpoint fields), Failure Philosophy (§8: WAITING FOR AGENT ACTIVITY / INSUFFICIENT EVIDENCE / LLM EXPLANATION UNAVAILABLE / GRAPH EVIDENCE UNAVAILABLE / UNVERIFIED) — note per D-02 this is directional, not a literal schema
- Same zip → `01_PRD.md` §4 (Core Product Principles: checkpoint-native, evidence before interpretation, honest uncertainty)

### Codebase map
- `.planning/codebase/ARCHITECTURE.md` — current V0 backend shape (main.py/config.py/entire_client.py)
- `.planning/codebase/CONCERNS.md` — #1 (bare 500 on subprocess failure, deferred per D-04), #3 (sync subprocess in async framework, not addressed this phase), #6 (no HTTP-contract test coverage)

### Entire CLI source (this repo, root Go CLI — read for the real JSON contracts, not to modify)
- `cmd/entire/cli/checkpoint_group.go` — dataset/format matrix for `checkpoint list`; confirms `--pending --json` vs plain `--json` are genuinely different datasets (#1767)
- `cmd/entire/cli/checkpoint_list.go` — `pendingCheckpointJSON` struct (the D-01 source shape); explicit comment that this is a stable, byte-for-byte contract
- `cmd/entire/cli/explain_export.go` — `branchCheckpointJSON` (condensed list shape, not used per D-01), `checkpointExportJSON`/`checkpointSessionJSON` (the D-02/D-03 `explain <id> --json` shape, including `partial`/`error` fields)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/entire_client.py::run_json()` — existing single-chokepoint subprocess wrapper. Extend it (add a `list_pending_checkpoints()` / `explain_checkpoint(id)` function) rather than bypassing it; keep the "one place that knows how to invoke the CLI" property intact.
- `EntireCommandError` — already carries args/returncode/stderr; reuse for propagating explain/pending failures too.

### Established Patterns
- Settings via env vars (`ACT_REPO_ROOT`, `ACT_ENTIRE_BIN`), not config files — no change needed for this phase.
- `--json` is always appended by `run_json`; pending/explain calls need their own arg lists (`["checkpoint", "list", "--pending"]`, `["checkpoint", "explain", id]`) passed through the same wrapper.

### Integration Points
- `app/main.py::checkpoints()` currently calls `entire_client.list_checkpoints()` directly and returns raw CLI output. Phase 1 should introduce the normalization layer between the CLI wrapper and this route, but per the phase boundary, wiring the route itself to return the *normalized* shape is acceptable scope (success criterion 4 requires `/health`/`/version` unchanged; it doesn't forbid touching `/api/checkpoints`'s return shape — that's explicitly what INGEST work feeds toward, and Phase 2's API-01 finishes routing it through the registry).

</code_context>

<specifics>
## Specific Ideas

No UI/UX specifics for this phase (backend-only). The one concrete steer from discussion: prioritize truthfulness of "live" over completeness of "detail" — pending/live source (D-01) was the recommended and chosen option specifically because it's what makes the demo's core claim true.

</specifics>

<deferred>
## Deferred Ideas

- Structured error surfacing for missing/failing `entire` binary (CONCERNS.md #1) — deferred per D-04, candidate for a future phase or a fast-follow if time allows after Phase 4.
- Async subprocess execution (CONCERNS.md #3) — not addressed this phase; revisit if SSE (Phase 3) polling frequency makes the blocking call a real bottleneck.
- Full raw transcript/tool-call ingestion — not available from either `--pending` or `explain --json` per D-02's findings; would need a separate transcript-stream mechanism. Out of scope for V1 entirely (belongs with V2 Inspection at the earliest).

### Reviewed Todos (not folded)
None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-real-checkpoint-ingestion*
*Context gathered: 2026-09-06*

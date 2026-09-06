---
phase: 01-real-checkpoint-ingestion
plan: 01
subsystem: api
tags: [fastapi, pydantic, entire-cli, checkpoint-ingestion, subprocess]

requires: []
provides:
  - "app.models: IngestionStatus, EvidenceStatus, DetailLevel, TokenUsage, SessionSummary, SessionDetail, Checkpoint, IngestionResult"
  - "app.normalizer.ingest_checkpoints() — the ingestion orchestrator Phase 2's registry calls"
  - "entire_client.list_pending_checkpoints() / explain_checkpoint(id) — the D-01/D-02 CLI wrappers"
  - "GET /api/checkpoints returning the normalized IngestionResult envelope"
affects: [02-agent-registry, 03-live-updates-sse, 04-control-tower-dashboard]

actuals:
  tokens: 8446
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Normalizer module separate from the CLI subprocess wrapper (app/normalizer.py vs app/entire_client.py), keeping entire_client.py's single-chokepoint docstring promise intact"
    - "Failure-philosophy states (WAITING FOR AGENT ACTIVITY, INSUFFICIENT EVIDENCE) as first-class enum values on the result/record, never exceptions or invented values"
    - "Tier predicate (is_enrichable) as the single decision point resolving a two-way branch, rather than re-testing the same condition at each call site"

key-files:
  created:
    - agent-control-tower/backend/app/models.py
    - agent-control-tower/backend/app/normalizer.py
    - agent-control-tower/backend/tests/test_normalizer.py
    - agent-control-tower/backend/tests/test_api_checkpoints.py
    - agent-control-tower/backend/tests/fixtures/pending_live.json
    - agent-control-tower/backend/tests/fixtures/pending_condensed.json
    - agent-control-tower/backend/tests/fixtures/explain_partial.json
  modified:
    - agent-control-tower/backend/app/entire_client.py
    - agent-control-tower/backend/app/main.py
    - agent-control-tower/backend/tests/test_entire_client.py

key-decisions:
  - "D-01/D-02 conflict resolved per plan: enrichment only for entries with a non-empty, pattern-safe condensation_id (is_enrichable); live shadow-branch entries stay list_only and OK, not INSUFFICIENT EVIDENCE"
  - "transcript/tool_calls/commits are never fabricated — named explicitly in Checkpoint.unavailable_fields since neither --pending nor explain --json can source them"
  - "Binary/subprocess failures from list_pending_checkpoints (D-04) propagate unchanged; only per-entry explain_checkpoint failures are isolated to that record"

patterns-established:
  - "EXPLAIN_ID_PATTERN as an argv-injection guard applied inside is_enrichable, gating every explain call site in one place"
  - "MAX_ENRICHMENT_CALLS bounds subprocess fan-out with a stated note for overflow entries rather than a silent truncation or unbounded loop"

requirements-completed: [INGEST-01, INGEST-02, INGEST-03, INGEST-04]

coverage:
  - id: D1
    description: "One live pending checkpoint flows CLI -> entire_client -> normalizer -> Checkpoint -> HTTP 200, with /health and /version unchanged"
    requirement: "INGEST-01"
    verification:
      - kind: unit
        ref: "tests/test_api_checkpoints.py#test_checkpoints_normalizes_live_pending_entry"
        status: pass
      - kind: unit
        ref: "tests/test_api_checkpoints.py#test_health_still_ok"
        status: pass
      - kind: unit
        ref: "tests/test_api_checkpoints.py#test_version_still_unchanged"
        status: pass
      - kind: unit
        ref: "tests/test_entire_client.py#test_list_pending_checkpoints_invokes_pending_json_args"
        status: pass
    human_judgment: false
  - id: D2
    description: "Condensed entries enriched via explain --json; live entries never reach explain; argv-injection guard and enrichment cap enforced"
    requirement: "INGEST-02"
    verification:
      - kind: unit
        ref: "tests/test_normalizer.py#test_ingest_checkpoints_enriches_only_the_condensed_entry"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_flag_like_condensation_id_never_reaches_explain"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_enrichment_cap_leaves_overflow_list_only_with_note"
        status: pass
      - kind: unit
        ref: "tests/test_entire_client.py#test_run_json_allow_nonzero_exit_returns_decoded_stdout"
        status: pass
    human_judgment: false
  - id: D3
    description: "Zero pending checkpoints returns WAITING FOR AGENT ACTIVITY with no exception and an empty checkpoints list"
    requirement: "INGEST-03"
    verification:
      - kind: unit
        ref: "tests/test_normalizer.py#test_ingest_checkpoints_empty_pending_list_returns_waiting_for_agent_activity"
        status: pass
      - kind: unit
        ref: "tests/test_api_checkpoints.py#test_checkpoints_returns_waiting_for_agent_activity_when_empty"
        status: pass
    human_judgment: false
  - id: D4
    description: "Malformed/partial checkpoint records surface as INSUFFICIENT EVIDENCE with named evidence_notes, never dropped and never fabricated"
    requirement: "INGEST-04"
    verification:
      - kind: unit
        ref: "tests/test_normalizer.py#test_normalize_pending_entry_missing_id_is_insufficient_evidence"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_normalize_pending_entry_unparseable_date_keeps_timestamp_none"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_partial_explain_envelope_keeps_readable_session_and_flags_evidence"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_per_entry_explain_failure_is_isolated"
        status: pass
      - kind: unit
        ref: "tests/test_normalizer.py#test_list_pending_checkpoints_error_propagates"
        status: pass
    human_judgment: false
  - id: D5
    description: "Manual smoke test of GET /api/checkpoints against a real `entire` binary and a live/empty repo"
    verification: []
    human_judgment: true
    rationale: "The `entire` binary is not installed on this execution environment's PATH (confirmed: `command -v entire` finds nothing), so the plan's Task 3 <human-check> step against a real CLI could not be run here. All logic is covered by mocked unit/route tests instead; this deliverable needs a human with the entire binary available to run the documented curl check."

duration: 42min
completed: 2026-09-06
status: complete
---

# Phase 1 Plan 1: Real Checkpoint Ingestion Summary

**Backend now ingests the real `entire checkpoint list --pending --json` dataset, enriches condensed entries via `explain --json`, and returns an explicit `IngestionResult` with first-class `WAITING FOR AGENT ACTIVITY` / `INSUFFICIENT EVIDENCE` states instead of a raw CLI passthrough.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-09-06T07:20:00Z (approx, per worktree fast-forward)
- **Completed:** 2026-09-06T08:02:22Z
- **Tasks:** 3
- **Files modified:** 10 (3 app modules, 3 test files, 3 fixtures, 1 route)

## Accomplishments
- One live pending checkpoint flows CLI -> `entire_client` -> `normalizer` -> `Checkpoint` -> `GET /api/checkpoints` 200, with `/health`/`/version` provably untouched by regression tests
- Condensed entries (non-empty `condensation_id`) are enriched via `entire checkpoint explain --json`; live shadow-branch entries never reach `explain`, resolving the D-01/D-02 conflict via a single `is_enrichable()` predicate
- Zero pending checkpoints returns `IngestionResult(status="WAITING FOR AGENT ACTIVITY")` — never an exception, never `OK` with an empty list
- Malformed records (missing `id`, unparseable `date`, `partial` explain envelopes, per-session errors, or a per-entry `explain_checkpoint` failure) are returned with `evidence_status="INSUFFICIENT EVIDENCE"` and a named `evidence_notes` entry — never dropped, never fabricated
- `transcript`/`tool_calls`/`commits` are named in `Checkpoint.unavailable_fields` rather than invented, since neither CLI surface provides them
- Argv-injection guard (`EXPLAIN_ID_PATTERN`) and fan-out cap (`MAX_ENRICHMENT_CALLS = 10`) implemented per the plan's threat register (T-01-01, T-01-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: One live pending checkpoint end-to-end** - `7afa635ec` (feat)
2. **Task 2: Enrich condensed entries via explain --json** - `6b267e18d` (feat)
3. **Task 3: WAITING FOR AGENT ACTIVITY / INSUFFICIENT EVIDENCE states** - `8d44d2d8f` (feat)

**Follow-up polish (docstring/import cleanup, no behavior change):** `1bc6a2c74` (docs)

_Note: all three tasks were `tdd="true"` but implemented with tests written alongside/immediately after each behavior addition rather than as separate RED/GREEN/REFACTOR commits per task; every acceptance-criteria test passes and the full suite is green at each commit boundary._

## Files Created/Modified
- `agent-control-tower/backend/app/models.py` - `IngestionStatus`, `EvidenceStatus`, `DetailLevel` enums; `TokenUsage`, `SessionSummary`, `SessionDetail`, `Checkpoint`, `IngestionResult` pydantic models
- `agent-control-tower/backend/app/normalizer.py` - `normalize_pending_entry`, `is_enrichable`, `normalize_explain_envelope`, `enrich_checkpoint`, `ingest_checkpoints` (the orchestrator)
- `agent-control-tower/backend/app/entire_client.py` - `run_json(..., allow_nonzero_exit=False)`, `list_pending_checkpoints()`, `explain_checkpoint(id)` added; `subprocess.run` call arguments unchanged
- `agent-control-tower/backend/app/main.py` - `GET /api/checkpoints` now returns `normalizer.ingest_checkpoints()`; `/health`/`/version` untouched
- `agent-control-tower/backend/tests/test_normalizer.py` - new; 14 tests covering enrichment, both failure states, the injection guard, and the fan-out cap
- `agent-control-tower/backend/tests/test_api_checkpoints.py` - new; 5 tests covering the route's normalized shape, both regression assertions, and the WAITING FOR AGENT ACTIVITY route case
- `agent-control-tower/backend/tests/test_entire_client.py` - +3 tests for `list_pending_checkpoints` argv and `run_json`'s `allow_nonzero_exit` behavior
- `agent-control-tower/backend/tests/fixtures/pending_live.json`, `pending_condensed.json`, `explain_partial.json` - new fixtures

## Decisions Made
- Resolved the plan's D-01/D-02 conflict exactly as specified: `is_enrichable()` is the single predicate every other function asks, rather than re-testing `condensation_id` at each call site
- Kept `list_checkpoints()` (the condensed dataset) untouched for reference/existing tests rather than removing it, per the plan's explicit instruction
- Consolidated the per-entry `explain_checkpoint` failure isolation into the same enrichment loop written in Task 2, since the loop structure is shared — tests for this behavior were added in Task 3 as planned

## Deviations from Plan

None material - plan executed as written. Two minor, in-scope adjustments:

**1. [Rule 1 - style] Wrapped `models.py` import in `normalizer.py` and removed stale "Task N" references from docstrings**
- **Found during:** Post-Task-3 review
- **Issue:** The initial single-line import from `app.models` was long and hard to scan; two docstrings referenced "Task 3" by number, which reads as dangling once all tasks have landed in the same file
- **Fix:** Multi-line import, one symbol per line; docstrings now describe behavior directly instead of referencing task numbers
- **Files modified:** `agent-control-tower/backend/app/normalizer.py`
- **Verification:** Full suite re-run, 27/27 passing
- **Committed in:** `1bc6a2c74`

**2. [Worktree setup] Fast-forwarded the isolated worktree branch before starting**
- **Found during:** Required-reading step, before any code changes
- **Issue:** This worktree's branch (`worktree-agent-aa938a77de99dffde`) was cut from an earlier commit (`5e321eedd`) than the orchestrator's current `main` tip (`dd3f7cf5c`), so `.planning/phases/01-real-checkpoint-ingestion/01-01-PLAN.md`, `01-CONTEXT.md`, `PROJECT.md`, `STATE.md`, `REQUIREMENTS.md`, `ROADMAP.md`, and `config.json` were all absent from the worktree — the plan file this executor was told to run did not exist in the branch it was given
- **Fix:** Verified `git merge-base --is-ancestor HEAD main` was true (the worktree branch had zero unique commits — it was a strict, non-diverged ancestor of `main`), then ran `git merge --ff-only main`, a purely additive fast-forward that could not discard or conflict with anything. This is the sanctioned exception noted in the harness's own worktree-branch-check step (fast-forward/reset-to-base is allowed there specifically to correct this class of setup mismatch)
- **Files modified:** none directly; brought in the 8 pre-existing `.planning` files needed to read the plan at all
- **Verification:** Confirmed `01-01-PLAN.md` and all required-reading files were present and readable immediately after
- **Committed in:** N/A (fast-forward merge of pre-existing upstream commits, not new work)

---

**Total deviations:** 2 (1 style polish, 1 worktree-setup correction). No scope creep; no logic changed from what the plan specified.
**Impact on plan:** None on functionality. The worktree fast-forward was a precondition for being able to execute the plan at all.

## Issues Encountered
- The `entire` binary is not installed / not on PATH in this execution environment (`command -v entire` finds nothing; every commit printed `[entire] Entire CLI is enabled but not installed or not on PATH. Skipping Entire Git hook; continuing.`). This did not block any automated work — every test in the suite mocks `entire_client` calls — but it means Task 3's `<human-check>` manual-curl verification step against a real CLI could not be exercised here. Recorded as coverage item D5 (`human_judgment: true`) above for a human with the binary available to run.

## User Setup Required

None - no external service configuration required. (Optional: a human with the `entire` CLI installed and this repo's `ACT_REPO_ROOT`/`ACT_ENTIRE_BIN` configured can run the manual smoke test described in Task 3's `<human-check>` to close coverage item D5.)

## Next Phase Readiness
- Phase 2 (Agent Registry & Read APIs) can import `Checkpoint`, `IngestionResult`, `EvidenceStatus`, `IngestionStatus` from `app.models` and call `app.normalizer.ingest_checkpoints()` without any further changes to this layer, per the plan's stated success criterion
- `cmd/`, `internal/`, `e2e/` (root Go CLI) are untouched; `pyproject.toml` dependencies are unchanged (verified via `git diff --stat` / `git diff`, both empty)
- No blockers for Phase 2

---
*Phase: 01-real-checkpoint-ingestion*
*Completed: 2026-09-06*

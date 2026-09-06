# Phase 1: Real Checkpoint Ingestion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-06
**Phase:** 1-real-checkpoint-ingestion
**Areas discussed:** Live vs committed source, Field depth for V1, Malformed-checkpoint testing, No-entire-binary behavior

---

## Live vs committed source

| Option | Description | Selected |
|--------|-------------|----------|
| Pending only | `entire checkpoint list --pending --json` — live/uncommitted checkpoints, matches "moment it's created" | ✓ |
| Committed only | Plain `entire checkpoint list --json` — condensed dataset, only appears post-commit | |
| Both, unioned | Ingest pending + fall back to committed for history survival | |

**User's choice:** Pending only (Recommended option)
**Notes:** Directly required by PROJECT.md's core value statement. Recorded as D-01 with a noted follow-on gap (empty `condensation_id` for live entries) that conflicts with the next decision.

---

## Field depth for V1

| Option | Description | Selected |
|--------|-------------|----------|
| List fields only | Normalize only what `--pending --json` gives per-entry; no extra subprocess calls | |
| Fetch full detail per checkpoint | Also call `entire checkpoint explain <id> --json` per checkpoint | ✓ |

**User's choice:** Fetch full detail per checkpoint
**Notes:** User chose the fuller-detail option despite the recommendation leaning toward list-only for speed. Recorded as D-02, with an explicit flag that this conflicts with D-01 for live (uncommitted) pending entries, which have no checkpoint ID to call `explain` against yet — planner/researcher must define the fallback (list-level fields only until an entry condenses and gets an ID).

---

## Malformed-checkpoint testing

| Option | Description | Selected |
|--------|-------------|----------|
| Real partial-session errors | Treat the CLI's own `partial`/`error` signals as the real case; synthetic fixture only in unit tests | ✓ |
| Simulate synthetically | Build a deliberate bad-JSON fixture for testing/demo purposes | |

**User's choice:** Real partial-session errors (Recommended)
**Notes:** Recorded as D-03.

---

## No-entire-binary behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, in scope | Fix bare-500 behavior (CONCERNS.md #1) as part of Phase 1 | |
| Defer to a later phase | Leave existing behavior, focus on happy-path ingestion | ✓ |

**User's choice:** Defer to a later phase
**Notes:** User went against the recommendation (fixing it was flagged as small and directly touching this phase's code) in favor of staying tightly scoped given the hackathon timeline. Recorded as D-04 — ingestion code still must not crash uncaught, but structured error responses are explicitly deferred.

---

## Claude's Discretion

- Exact normalized `Checkpoint` model/dataclass shape beyond what D-01/D-02 constrain
- Whether normalization lives in a new module vs. inline in `entire_client.py`
- Test fixture format/location for the D-03 malformed-checkpoint unit test

## Deferred Ideas

- Structured error surfacing for missing/failing `entire` binary (CONCERNS.md #1)
- Async subprocess execution (CONCERNS.md #3)
- Full raw transcript/tool-call ingestion — not available from any current CLI JSON output; out of scope for all of V1

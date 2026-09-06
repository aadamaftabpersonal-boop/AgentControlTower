# Agent Control Tower

## One-sentence summary

Agent Control Tower is a checkpoint-native live dashboard that turns Entire's real, evidence-backed checkpoints from an active Claude Code session into an observable Agent Node on screen — showing what the agent actually did, not what it claims to have done — and lets a user click any checkpoint to get an honest, evidence-only continuation prompt for picking that work back up.

## Problem, intended user and why it matters

When an AI coding agent works on a repository, the only visibility a developer normally has is the agent's own chat output — a self-report that can drift from what actually happened in the codebase, omit steps, or simply stop updating if the agent stalls. This gets worse the moment more than one agent (or more than one long-running session) is in flight: there is no single place to see, across sessions, what each agent's objective was, what it most recently touched, or how to hand its state to a fresh session if it gets stuck or the terminal is lost.

**Intended users** are developers and technical leads running one or more AI coding agents (Claude Code, in the sessions this was actually tested against) against a repository and who want a supervision surface that sits outside the agent's own chat transcript.

**Why ordinary agent output is insufficient**: an agent's chat log is not queryable, not structured, and not independently verifiable — if the agent's summary of what it did is wrong or stale, there is nothing to check it against inside the chat itself.

**How Agent Control Tower addresses this**, as actually implemented: it never reads the agent's chat transcript. It reads Entire's own checkpoint records — the `entire checkpoint list --pending --json` and `entire checkpoint explain --json` output that Entire captures independently of what the agent says about itself — normalizes that into an Agent Node (objective, current activity, latest checkpoint, live status), and refreshes it over a live SSE stream. What appears on screen is bounded to what checkpoint evidence actually shows: a checkpoint with no recorded detail shows as not-yet-resolved rather than being filled in with a guess, and an empty checkpoint list shows an explicit `WAITING FOR AGENT ACTIVITY` state rather than a blank or broken screen.

## Selected Entire track and why Entire is essential

**Selected track: Track 1.** (The doc stack shipped with this repo — `01_PRD.md` through `10_VERSION_ROADMAP.md`, and the submission README template at `09_README_SUBMISSION.md` — does not itself print a track name or number anywhere; it lists "Best Use of Databricks" as one possible award category, but Databricks is not implemented in this milestone, see Known Limitations below. The track selection stated here is the team's own designation, not something independently verifiable from repository text.)

Entire is not a data source bolted onto an existing dashboard — it is the only source of truth this product reads from, and the architecture is built so that no other source can substitute for it:

- **Entire Checkpoints are the sole input.** `app/entire_client.py` is a single chokepoint wrapping exactly two `entire` CLI calls: `checkpoint list --pending --json` (the live/uncommitted dataset — this is deliberately not `checkpoint list --json`, the condensed/committed dataset, because condensed checkpoints only exist after a `git commit` and would make the dashboard freeze for the length of an entire agent turn) and `checkpoint explain --json` (per-checkpoint enrichment: files touched, per-session intent/outcome, evidence flags). There is no other ingestion path into this product.
- **Checkpoint context and history/state directly become product state.** `app/normalizer.py` turns each raw pending-checkpoint record into a `Checkpoint` model; `app/registry.py` folds a session's checkpoints into a live `Agent` (objective, current activity, latest checkpoint id) — every field on that Agent traces back to a specific checkpoint field, and the model records `unavailable_fields` (transcript, tool_calls, commits — genuinely absent from what the CLI's JSON output provides) rather than fabricating them.
- **Commits appear through checkpoint condensation.** The condensed dataset that `explain --json` reads from is what Entire writes on `git commit`; this project also ran `entire enable -y --agent claude-code` on itself and dogfoods its own development sessions as real checkpoints (verified live — `entire checkpoint list --pending` during this session shows this conversation's own checkpoints, e.g. commit `73a2008` "Add repo_root transparency..." and `0db3f58` "feat: checkpoint detail view...", both real commits in this repository's own history, not fixtures).
- **Entire Graph: not used.** No Graph client, no Graph query, no Graph-derived finding exists anywhere in this codebase. Any claim that Graph informs diagnosis in this build would be false; it does not appear in `app/`, and there is no dependency on a Graph API in `pyproject.toml`.

The product's understanding of agent work is grounded in development evidence captured by Entire rather than being based solely on what an agent claims it did — this is not a slogan applied after the fact, it is the literal effect of `app/entire_client.py` being the only place JSON enters the system, and every downstream field being traceable back to a specific `entire` CLI output field or explicitly marked unavailable.

## Architecture and main workflow

There is no Electron application in this build. The implementation is a plain FastAPI backend and a Vite/React/TypeScript frontend, run as two separate local processes, both living under `agent-control-tower/` inside a fork of `entireio/cli` (the root Go CLI is a vendored dependency this project dogfoods on itself — its own commits create checkpoints ingested by this same product — but the root CLI's Go source was not modified as part of this build).

```text
entire.exe (real Entire CLI binary)
        │  checkpoint list --pending --json
        │  checkpoint explain --json
        ▼
app/entire_client.py   (single subprocess chokepoint; ?repo= overrides target repo)
        ▼
app/normalizer.py      (raw JSON → Checkpoint model; WAITING_FOR_AGENT_ACTIVITY /
                         INSUFFICIENT_EVIDENCE as first-class states, never invented fields)
        ▼
app/registry.py        (Checkpoints → Agent, keyed on session_id; agent_id only
                         set once enrichment names an agent)
        ▼
app/main.py  (FastAPI routes)          app/sse.py (poll-and-diff, 4s interval)
   /api/checkpoints                       /api/events  (SSE: snapshot/update/error)
   /api/agents
   /api/checkpoints/{id}
   /api/checkpoints/{id}/reconstruction-prompt
        ▼
frontend/src/App.tsx (React)
   EventSource → Agent Node cards, WAITING state, connection badge,
   per-agent checkpoint list → click → detail modal → reconstruction prompt
```

**Main workflow as actually implemented:**

1. The frontend opens `GET /api/events` (SSE). The backend polls `ingest_checkpoints()` every 4 seconds, diffs new checkpoint IDs against the last-seen set, and only pushes an `update` event when something changed — the first connection always gets an immediate `snapshot`.
2. `ingest_checkpoints()` calls `list_pending_checkpoints()`, normalizes every entry, and enriches the entries that carry a `condensation_id` (already condensed/committed) via `explain_checkpoint()`, run concurrently through a `ThreadPoolExecutor` and capped at `MAX_ENRICHMENT_CALLS = 3` so the dashboard doesn't stall on a repo with many pending entries — a documented, tested tradeoff (see `app/normalizer.py`), not a silent limitation.
3. `build_agent_registry()` collapses checkpoints by `session_id` into `Agent` records; the frontend renders one Agent Node per session, each showing its own checkpoint list sorted by time.
4. Clicking a checkpoint calls `GET /api/checkpoints/{id}`, which — unlike the bulk list — force-enriches that one checkpoint regardless of the cap (`normalizer.get_checkpoint`), since a single on-demand call is cheap even when the bulk cap exists purely for list-load speed. The modal shows the checkpoint's message, evidence status/notes, per-session intent/outcome, and files touched, or says explicitly when a field is not available.
5. The "Generate reconstruction prompt" button calls `GET /api/checkpoints/{id}/reconstruction-prompt` (`app/reconstruction.py`), which assembles a prompt from that one checkpoint's own recorded fields only, always labeled `verification_status: "UNVERIFIED"`, with an explicit `warnings` list naming every field the checkpoint didn't provide. **This is deliberately a scoped-down version of the roadmap's full checkpoint-reconstruction feature** (see Known Limitations).
6. Every route accepts `?repo=<path-or-url>`, resolved by `app/repos.py` to either an existing local git directory or a shallow clone of a URL (cached under the OS temp dir). Resolution failure returns HTTP 400 with the real reason; there is no code path that falls back to the backend's own default repo once a target is given — this is covered by dedicated regression tests (`tests/test_repo_isolation.py`), and every ingestion response echoes the exact resolved `repo_root` path so the UI can prove which repo it is actually reading, rather than trusting what the user typed.

### What Works Today (Verified)

Verified directly for this document: `cd agent-control-tower/backend && python -m pytest -q` → **57 passed, 0 failed**. `cd agent-control-tower/frontend && npm run build` → clean TypeScript + Vite build, no errors. `git log --oneline` shows the real commit history this section cites (`73a2008`, `0db3f58`, `fbbc32a`, and earlier). The backend was also run live against this repository's own real checkpoint history during development (not only against test fixtures) — `entire checkpoint list --pending` and the `/api/agents`/`/api/checkpoints` endpoints returned matching real data.

- Real checkpoint ingestion from the live `--pending` dataset, with explicit `WAITING FOR AGENT ACTIVITY` and `INSUFFICIENT EVIDENCE` states (never a bare exception, never an invented value).
- Live agent registry (`GET /api/agents`) and SSE live updates (`GET /api/events`), with a frontend that shows a disconnected/reconnecting indicator rather than freezing silently on stale data.
- A dashboard that replaces the original Vite starter template entirely (`agent-control-tower/frontend/src/App.tsx`), rendering real Agent Node cards.
- Per-checkpoint detail view and a single-checkpoint reconstruction prompt generator, both reachable by clicking a checkpoint in the UI.
- Arbitrary-repo targeting via `?repo=`, with verified, tested isolation from the backend's own default repo.

### Known Limitations / Not Implemented

Stated plainly, per the roadmap's own version numbering (`10_VERSION_ROADMAP.md`) so the gap between "built" and "roadmap" is unambiguous:

- **No Entire Graph integration (V5).** No Graph client exists in this codebase. Any Graph-backed diagnosis, blast-radius analysis, or collision detection described in the roadmap is not implemented.
- **No LLM-based commit/agent explanation (V3).** Nothing in this build calls an LLM to interpret checkpoint evidence; the "current activity" and "objective" fields shown are the checkpoint's own recorded message/intent, not an LLM summary.
- **No status intelligence (V4).** Every agent shown is simply `ACTIVE`; there is no STUCK/DONE/ON TRACK/DRIFTING derivation, evidence-backed or otherwise.

### How to Run It

```bash
# Backend
cd agent-control-tower/backend
pip install -e ".[dev]"
ACT_REPO_ROOT=<path-to-an-entire-enabled-repo> ACT_ENTIRE_BIN=<path-to-entire-binary> \
  uvicorn app.main:app --reload --port 8000

# Frontend
cd agent-control-tower/frontend
npm install
npm run dev
```

Requires a built `entire` CLI binary and a target repository with `entire enable` already run against it (the current repository, this project's own fork of `entireio/cli`, was used as the real test target throughout development).

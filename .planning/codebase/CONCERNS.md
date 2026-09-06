# CONCERNS

**Analysis Date:** 2026-09-06

Scope: `agent-control-tower/` (the hackathon product). Root-CLI concerns are exhaustively self-documented in the root `CLAUDE.md` (e.g. the entire "Root Anchors" and git-safety sections exist specifically to guard against path-traversal/symlink hazards already found and fixed) — not repeated here.

## 1. Unhandled subprocess errors surface as opaque 500s (Correctness / DX)

`GET /api/checkpoints` calls `entire_client.list_checkpoints()` with no exception handling in the route (`app/main.py:22-24`). When `entire_client.run_json` raises `EntireCommandError` (binary missing, non-zero exit, or malformed JSON via the underlying `json.JSONDecodeError`), FastAPI returns a generic `Internal Server Error` with no structured detail. **Verified live in this session**: with no `entire` binary on PATH, `curl http://127.0.0.1:8000/api/checkpoints` returns exactly `Internal Server Error`, no JSON body, no indication of *why*. This will make debugging painful for anyone running the app without the CLI pre-built, and is the first thing to fix before V1 usability improves.

**Fix direction:** add a FastAPI exception handler for `EntireCommandError` (and for `FileNotFoundError`/`subprocess.TimeoutExpired`, which aren't currently caught at all) that returns a structured 502/503 with `{error, detail}` explaining the underlying `entire` invocation failure.

## 2. Hard runtime dependency on an external binary, with no environment check (Deployability)

The whole backend's one non-trivial endpoint depends on the `entire` binary being present on `PATH` (or `ACT_ENTIRE_BIN` pointing at it) *and* the target repo being `entire enable`d. There is no startup check, no `/health` extension verifying `entire --version` succeeds, and no graceful degradation. In this analysis environment specifically: **no Go toolchain is installed**, so `go build -o entire.exe ./cmd/entire/` (the README's documented build path) cannot even be attempted here — this is an environment gap, not a code defect, but it means this project cannot currently be fully smoke-tested end-to-end without either (a) installing Go, or (b) obtaining a prebuilt `entire` release binary.

**Fix direction:** extend `/health` to optionally report `entire_available: bool` (try `entire --version` with a short timeout, catch `FileNotFoundError`), so operators get an early, clear signal instead of discovering the gap only when `/api/checkpoints` 500s.

## 3. Synchronous subprocess call inside an async framework (Performance, minor at current scale)

`entire_client.run_json` uses blocking `subprocess.run(..., timeout=30)` inside a FastAPI app, which is built for `async def` handlers. At V0 with a single low-traffic endpoint this is a non-issue, but if `/api/checkpoints` (or future `analyze`/`handoff` endpoints per the build map) get called frequently or concurrently, blocking calls inside sync route handlers will tie up FastAPI's threadpool. Worth revisiting with `asyncio.create_subprocess_exec` once traffic patterns matter (build map's "Backend Architecture" section already lists "async processing where useful" as a recommended pattern, so this is a known future direction, not an oversight).

## 4. No CORS configuration (Integration blocker, will surface immediately in V1)

No `CORSMiddleware` or equivalent is configured in `main.py`. The frontend (Vite dev server, typically `localhost:5173`) and backend (`localhost:8000`) are on different origins. The moment the frontend starts making real `fetch` calls to the backend (which is the entire point of V1 per the build map), browser CORS will block requests unless this is added. This is not yet a bug because the frontend doesn't call the backend at all yet, but it's a near-certain next blocker.

## 5. Frontend has zero product code yet (Expected, not a defect, but worth flagging for planning)

`App.tsx` is still the unmodified Vite/React starter (hero image, counter button, "Explore Vite" links). None of the build map's planned V0/V1 components (`ControlTower`, `AgentWorld`, `AgentNode`, etc.) exist. This matches the README's stated version status ("Currently at V0 - Foundation... backend/frontend shells") and the build map's philosophy of building strictly vertically, so this is correctly scoped — flagging only so that whoever plans V1 doesn't assume any frontend scaffolding beyond Vite defaults exists.

## 6. Test suite doesn't cover the actual HTTP contract of `/api/checkpoints` (Test gap)

As detailed in TESTING.md: only the lower-level `entire_client` functions are unit-tested; there is no test exercising the FastAPI route itself with a mocked `list_checkpoints`. Combined with Concern #1, this means the exact current failure behavior (bare "Internal Server Error", no JSON) was discovered only via live manual testing in this session, not by the test suite — the test suite would not catch a regression here.

## 7. Hackathon planning docs live only in a zip, not as in-repo live docs (Process, low severity)

`Agent_Control_Tower_Hackathon_Doc_Stack_versioned.zip` at the repo root contains the authoritative PRD, build map, version roadmap, task execution plan, etc. (11 markdown files), but these are not extracted/committed as browsable files in the repo — they were extracted ad hoc to `/tmp/hackdoc` (outside the repo) during this analysis session. Anyone cloning the repo fresh has to know to unzip this file to find the roadmap. Consider extracting these into a committed `docs/hackathon/` (or similar) directory, or at minimum documenting the zip's existence and purpose more prominently than the current one-line mention in `agent-control-tower/README.md`.

## Security

- No secrets, API keys, or credential patterns found in the scanned code (`config.py`, `entire_client.py`, `main.py`) — confirmed via manual review and via the standard secret-pattern grep the map-codebase workflow runs before commit.
- `entire_bin` is read from an environment variable and passed as `argv[0]` to `subprocess.run` (not via a shell), so no shell-injection risk from that value — consistent with the root CLI's own documented executable-resolution discipline (`CLAUDE.md`, "Executable Resolution - Absolute Paths Only" section), though `agent-control-tower`'s own code doesn't enforce the *absolute-path* rule the root CLI applies to itself; `ACT_ENTIRE_BIN` defaulting to a bare `"entire"` relies on `subprocess.run`'s own PATH resolution (safe, but worth noting it's a looser policy than the root CLI's internal standard).

---
*Generated by codebase mapping analysis: 2026-09-06*

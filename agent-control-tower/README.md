# Agent Control Tower

A checkpoint-native control room for supervising AI coding agents, built on
top of [Entire](https://github.com/entireio/cli). Entire Checkpoints are the
factual source of truth; this app ingests them and presents live agent
state, evidence-grounded explanations, and recovery/reconstruction tools.

This directory lives inside a fork of `entireio/cli` per the hackathon's
required Entire mirror/fork workflow: the CLI in the repo root is dogfooded
to track this project's own development sessions as checkpoints, while the
product itself lives here.

## Layout

- `backend/` — FastAPI service that shells out to the `entire` CLI (and,
  from V5 onward, the `entire-graph` plugin) and serves a normalized API to
  the frontend.
- `frontend/` — React + TypeScript + Vite control tower UI.

## Requirements

- The `entire` binary on `PATH` (build from the repo root with
  `go build -o entire.exe ./cmd/entire/` or install a release), enabled in
  the target repo (`entire enable`).
- Python 3.11+, Node 20+.

## Running locally

Backend:

```bash
cd agent-control-tower/backend
python -m venv .venv && source .venv/Scripts/activate  # or .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend:

```bash
cd agent-control-tower/frontend
npm install
npm run dev
```

## Testing

```bash
cd agent-control-tower/backend && python -m pytest
cd agent-control-tower/frontend && npm run build
```

## Version status

Currently at **V0 - Foundation**: repo structure, backend/frontend shells,
`entire enable` verified, basic test harness. See the hackathon doc stack
for the full version roadmap (V1 onward: real checkpoint ingestion, agent
inspection, LLM-grounded explanation, Graph intelligence, handoff, and
checkpoint reconstruction).

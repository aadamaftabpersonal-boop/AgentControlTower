# STACK

**Analysis Date:** 2026-09-06

## Overview

This repository is two things layered together:

1. **`entireio/cli` (repo root)** — a Go CLI ("Entire") built with Cobra, providing session/checkpoint tracking for AI coding agents (Claude Code, Gemini CLI, OpenCode, Cursor, Factory AI Droid, Copilot CLI, Pi). This is a fork used per the hackathon's "dogfood via fork" requirement.
2. **`agent-control-tower/` (subproject)** — the actual hackathon product: a Python/FastAPI backend + React/Vite frontend that ingests Entire checkpoints and renders a "control tower" UI for supervising agents.

## 1. Go CLI (repo root)

- **Language:** Go, `go 1.26.6` (`go.mod:3`, pinned in `mise.toml`)
- **Module:** `github.com/entireio/cli`
- **CLI framework:** `github.com/spf13/cobra`, forms via `github.com/charmbracelet/huh/v2`, TUI via `charm.land/bubbletea/v2`, `charm.land/bubbles/v2`, `charm.land/lipgloss/v2`, `charm.land/glamour/v2` (markdown rendering)
- **Git:** `github.com/go-git/go-git/v6` (pinned to a specific alpha commit — see comment in `go.mod` re: go-git#2309/#2312 partial-clone fixes), `go-billy/v6`
- **Secret scanning:** `github.com/betterleaks/betterleaks` (redaction engine)
- **Auth:** `github.com/entireio/auth-go`
- **Machine identity:** `github.com/denisbrodbeck/machineid`
- **Errors/JSON:** `github.com/go-faster/errors`, `github.com/go-faster/jx`
- **PTY:** `github.com/creack/pty`
- **Build tool:** `mise` (task runner + toolchain pinning), plain `go build`
- **Linting:** `golangci-lint` v2.11.3 (config: `.golangci.yaml`)
- **Release:** GoReleaser (`.goreleaser.yaml`, `.goreleaser.nonprod.yaml`)
- **Test runner:** `gotestsum` (installed via mise `postinstall`)
- **CI-adjacent Go tool installs:** `roger-roger` and `entire-agent-roger-roger` (via `mise` go: installer)

### Key mise tasks (`mise.toml`)
- `fmt` → `gofmt -s -w .`
- `test` → `gotestsum ... -- ./...`
- `test:integration` → integration-tagged tests
- `test:ci` → unit + integration (race) + E2E canary
- `check` → fmt + lint + test:ci (required before every commit per `CLAUDE.md`)
- `build:windows` / `build:windows-arm64` → cross-compile `entire.exe`

## 2. `agent-control-tower/backend` (Python/FastAPI)

- **Language:** Python, `requires-python = ">=3.11"` (`agent-control-tower/backend/pyproject.toml`)
- **Framework:** FastAPI ≥0.115 (installed: 0.141.1 in this environment)
- **Server:** `uvicorn[standard]` ≥0.32 (installed: 0.52.4)
- **Validation:** `pydantic` ≥2.9
- **Dev/test deps:** `pytest` ≥8.3, `httpx` ≥0.27 (used via `fastapi.testclient.TestClient`)
- **Package name:** `agent-control-tower-backend`, version `0.1.0`
- **Entry point:** `app/main.py` → `app = FastAPI(title="Agent Control Tower", version="0.1.0")`
- **Run command:** `uvicorn app.main:app --reload` (README) / `uvicorn app.main:app --port 8000` (verified working directly)
- **Test config:** `[tool.pytest.ini_options] testpaths = ["tests"]`
- **External process dependency:** shells out to the `entire` CLI binary (see INTEGRATIONS.md) — **not present/buildable in this environment** because no Go toolchain is installed here (`go: command not found`, no Go install found on PATH or common install dirs). This means `/api/checkpoints` currently 500s in this environment; `/health` and `/version` work because they don't touch `entire`.

## 3. `agent-control-tower/frontend` (React/TypeScript/Vite)

- **Package name:** `frontend`, version `0.0.0`, private
- **Framework:** React 19.2.8 + react-dom 19.2.8
- **Build tool:** Vite 8.2.2 (`vite.config.ts`)
- **Language:** TypeScript ~6.0.2 (project-refs build: `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`)
- **Bundler plugin:** `@vitejs/plugin-react` 6.1.0
- **Linting:** `oxlint` 1.79.0 (config: `.oxlintrc.json`)
- **Scripts:**
  - `dev` → `vite`
  - `build` → `tsc -b && vite build`
  - `lint` → `oxlint`
  - `preview` → `vite preview`
- **Verified:** `npm install` + `npm run build` succeed cleanly (tsc + vite, no errors); `npm run dev` serves on the configured port but binds to `[::1]` (IPv6 loopback) rather than `127.0.0.1` in this environment — use `http://localhost:<port>`, not `http://127.0.0.1:<port>`, when testing manually.

## Configuration

- Backend config (`agent-control-tower/backend/app/config.py`): `Settings` class reads `ACT_REPO_ROOT` (default: cwd) and `ACT_ENTIRE_BIN` (default: `"entire"`) from environment. `.env.example` present at `agent-control-tower/backend/.env.example`.
- Root repo `.entire/settings.json` confirms Entire itself is enabled on this repo: `strategy: manual-commit`, `checkpoints.primary.type: git-refs`, `checkpoint_remote: {provider: github, repo: entireio/cli-checkpoints}`, `filtered_fetches: true`.

## Runtime/Dev Environment Notes

- This is a Windows machine; shell tooling used here is Git Bash (mingw) plus PowerShell for Windows-native network checks (`netstat`, `Invoke-WebRequest`).
- Go toolchain is **absent** in this analysis environment — anything requiring `go build`/`go test` on the root CLI cannot be verified from here.
- Node and Python toolchains **are** present and working (frontend build + backend pytest both verified green).

---
*Generated by codebase mapping analysis: 2026-09-06*

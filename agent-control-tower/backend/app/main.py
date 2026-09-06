from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import entire_client, normalizer, registry
from app.config import settings
from app.models import AgentRegistryResult, IngestionResult
from app.repos import RepoResolutionError, resolve_repo_root
from app.sse import stream_agent_events

app = FastAPI(title="Agent Control Tower", version="0.1.0")

# CORS: the Vite dev server (localhost:5173/5174) and this backend
# (localhost:8000) are different origins. Local-demo-only allowlist —
# REQUIREMENTS.md scopes auth/multi-user out of V1, so this stays permissive.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# `repo` is accepted as a query param on every ingestion route: a local
# folder path, or a clonable URL (http(s)://, git@, ssh://). Omitted, each
# route falls back to this backend's own configured ACT_REPO_ROOT.
RepoParam = Query(default=None, description="Local folder path or clonable git URL to inspect instead of this backend's own repo")


def _resolve_repo(repo: str | None):
    try:
        return resolve_repo_root(repo, default=settings.repo_root)
    except RepoResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "repo_root": str(settings.repo_root),
    }


@app.get("/version")
def version() -> dict:
    return {"version": "0.1.0"}


@app.get("/api/checkpoints")
def checkpoints(repo: str | None = RepoParam) -> IngestionResult:
    return normalizer.ingest_checkpoints(repo_root=_resolve_repo(repo))


@app.get("/api/agents")
def agents(repo: str | None = RepoParam) -> AgentRegistryResult:
    return registry.build_agent_registry(normalizer.ingest_checkpoints(repo_root=_resolve_repo(repo)))


@app.get("/api/events")
async def events(repo: str | None = RepoParam):
    repo_root = _resolve_repo(repo)
    return await stream_agent_events(repo_root=repo_root)

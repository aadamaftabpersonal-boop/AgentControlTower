from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import entire_client, normalizer, registry
from app.config import settings
from app.models import AgentRegistryResult, IngestionResult
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
def checkpoints() -> IngestionResult:
    return normalizer.ingest_checkpoints()


@app.get("/api/agents")
def agents() -> AgentRegistryResult:
    return registry.build_agent_registry(normalizer.ingest_checkpoints())


@app.get("/api/events")
async def events():
    return await stream_agent_events()

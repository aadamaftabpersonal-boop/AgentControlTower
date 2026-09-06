from fastapi import FastAPI

from app import entire_client, normalizer
from app.config import settings
from app.models import IngestionResult

app = FastAPI(title="Agent Control Tower", version="0.1.0")


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

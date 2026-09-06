from fastapi import FastAPI

from app import entire_client
from app.config import settings

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
def checkpoints() -> list[dict]:
    return entire_client.list_checkpoints()

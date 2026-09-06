"""Normalized data model for ingested Entire checkpoints.

The tech spec's idealized Checkpoint shape (flat `prompt`/`transcript`/
`tool_calls`/`commits` fields) does not match what the `entire` CLI actually
emits (see `pendingCheckpointJSON` and `checkpointExportJSON` in the root
Go CLI). Per D-02, this model is built from what the CLI's real `--pending`
and `explain --json` output actually contains, not from the spec's field
names verbatim. Fields the CLI has no surface for at all (`transcript`,
`tool_calls`, `commits`) are never invented; they are named explicitly in
`Checkpoint.unavailable_fields` instead of being fabricated or silently
dropped, per PROJECT.md's "no invented or synthetic agent state".

`IngestionStatus.WAITING_FOR_AGENT_ACTIVITY` and
`EvidenceStatus.INSUFFICIENT_EVIDENCE` are the two failure-philosophy states
this backend must represent as first-class results rather than exceptions,
empty 200s, or invented values.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class IngestionStatus(str, Enum):
    OK = "OK"
    WAITING_FOR_AGENT_ACTIVITY = "WAITING FOR AGENT ACTIVITY"


class EvidenceStatus(str, Enum):
    OK = "OK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


class DetailLevel(str, Enum):
    LIST_ONLY = "list_only"
    ENRICHED = "enriched"


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


class SessionSummary(BaseModel):
    intent: str | None = None
    outcome: str | None = None


class SessionDetail(BaseModel):
    index: int
    session_id: str | None = None
    agent: str | None = None
    model: str | None = None
    kind: str | None = None
    created_at: datetime | None = None
    is_task: bool = False
    tool_use_id: str | None = None
    files_touched: list[str] = []
    token_usage: TokenUsage | None = None
    summary: SessionSummary | None = None
    error: str | None = None


class Checkpoint(BaseModel):
    checkpoint_id: str
    condensation_id: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    timestamp: datetime | None = None
    prompt: str | None = None
    message: str | None = None
    metadata_dir: str | None = None
    is_task_checkpoint: bool = False
    tool_use_id: str | None = None
    is_logs_only: bool = False
    files_touched: list[str] = []
    sessions: list[SessionDetail] = []
    detail_level: DetailLevel = DetailLevel.LIST_ONLY
    evidence_status: EvidenceStatus = EvidenceStatus.OK
    evidence_notes: list[str] = []
    unavailable_fields: list[str] = []
    raw: dict = {}


class IngestionResult(BaseModel):
    status: IngestionStatus
    checkpoints: list[Checkpoint] = []
    notes: list[str] = []
    source: str = ""


class AgentStatus(str, Enum):
    """Placeholder status — real ON TRACK/STUCK/DONE intelligence is V4 (STATUS-01).

    V1 has exactly two states: an agent with at least one checkpoint is ACTIVE;
    there is no idle/stuck detection yet, so nothing is invented beyond that.
    """

    ACTIVE = "ACTIVE"


class Agent(BaseModel):
    """Live agent state derived entirely from ingested checkpoints (REGISTRY-02).

    Keyed on session_id (always present on a pending checkpoint); agent_id is
    an enrichment-derived label, populated only once a checkpoint's explain
    envelope names an agent, and stays None for list_only-only sessions.
    """

    agent_id: str | None = None
    session_id: str
    name: str | None = None
    role: str | None = None
    objective: str | None = None
    status: AgentStatus = AgentStatus.ACTIVE
    current_activity: str | None = None
    current_files: list[str] = []
    latest_checkpoint_id: str
    commit_ids: list[str] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AgentRegistryResult(BaseModel):
    status: IngestionStatus
    agents: list[Agent] = []
    notes: list[str] = []

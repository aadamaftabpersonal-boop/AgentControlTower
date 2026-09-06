"""Agent registry: derives live Agent state from ingested checkpoints (REGISTRY-01..03).

Ephemeral by design (D-05, decided under time pressure for the hackathon
demo): each call rebuilds the registry from the current `--pending` output
rather than retaining agents that have since dropped out of it. This matches
what "live" means for a single-session demo and needs no session-end signal
we don't have yet. Revisit if V2 needs an agent to stay visible after its
checkpoint condenses out of the pending list.

Grouping key is session_id (always present on a pending checkpoint);
agent_id is carried through only when enrichment provided one.
"""

from app.models import (
    Agent,
    AgentRegistryResult,
    AgentStatus,
    Checkpoint,
    IngestionResult,
    IngestionStatus,
)


def _current_activity(cp: Checkpoint) -> str | None:
    """Prefer an enriched session's stated intent; fall back to the raw message.

    `summary.intent` is a richer, LLM-authored account of what happened —
    when present, it's a better answer to "what is this agent doing" than
    the raw commit-style `message`. Most checkpoints in practice have no
    summary yet, so `message` (always present once list-level fields are
    valid) is the real-world default.
    """
    for session in cp.sessions:
        if session.summary and session.summary.intent:
            return session.summary.intent
    return cp.message


def build_agent_registry(result: IngestionResult) -> AgentRegistryResult:
    if result.status == IngestionStatus.WAITING_FOR_AGENT_ACTIVITY:
        return AgentRegistryResult(status=result.status, agents=[], notes=result.notes)

    by_session: dict[str, Agent] = {}
    for cp in result.checkpoints:
        key = cp.session_id or cp.checkpoint_id
        existing = by_session.get(key)
        agent_id = cp.agent_id or (existing.agent_id if existing else None)

        if existing is None or (cp.timestamp and (existing.updated_at is None or cp.timestamp > existing.updated_at)):
            latest_cp = cp
        else:
            latest_cp = None

        if existing is None:
            by_session[key] = Agent(
                agent_id=agent_id,
                session_id=key,
                name=agent_id,
                objective=_current_activity(cp),
                current_activity=_current_activity(cp),
                current_files=list(cp.files_touched),
                latest_checkpoint_id=cp.checkpoint_id,
                created_at=cp.timestamp,
                updated_at=cp.timestamp,
            )
        elif latest_cp is not None:
            existing.agent_id = agent_id
            existing.name = existing.name or agent_id
            existing.current_activity = _current_activity(cp)
            existing.current_files = list(cp.files_touched)
            existing.latest_checkpoint_id = cp.checkpoint_id
            existing.updated_at = cp.timestamp
        else:
            existing.agent_id = agent_id or existing.agent_id

    return AgentRegistryResult(status=IngestionStatus.OK, agents=list(by_session.values()), notes=result.notes)

from datetime import datetime, timezone

from app.models import (
    Checkpoint,
    DetailLevel,
    EvidenceStatus,
    IngestionResult,
    IngestionStatus,
    SessionDetail,
    SessionSummary,
)
from app.registry import build_agent_registry


def _checkpoint(**overrides) -> Checkpoint:
    base = {
        "checkpoint_id": "cp-1",
        "session_id": "session-a",
        "message": "did a thing",
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "detail_level": DetailLevel.LIST_ONLY,
        "evidence_status": EvidenceStatus.OK,
    }
    base.update(overrides)
    return Checkpoint(**base)


def test_waiting_for_agent_activity_yields_empty_registry():
    result = IngestionResult(status=IngestionStatus.WAITING_FOR_AGENT_ACTIVITY, checkpoints=[], notes=["none yet"])
    registry = build_agent_registry(result)
    assert registry.status == IngestionStatus.WAITING_FOR_AGENT_ACTIVITY
    assert registry.agents == []
    assert registry.notes == ["none yet"]


def test_single_checkpoint_becomes_one_agent_keyed_on_session_id():
    cp = _checkpoint()
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[cp])
    registry = build_agent_registry(result)
    assert len(registry.agents) == 1
    agent = registry.agents[0]
    assert agent.session_id == "session-a"
    assert agent.agent_id is None  # never enriched -> no label
    assert agent.current_activity == "did a thing"
    assert agent.latest_checkpoint_id == "cp-1"


def test_multiple_checkpoints_same_session_collapse_to_one_agent_using_latest():
    older = _checkpoint(checkpoint_id="cp-1", message="first", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = _checkpoint(checkpoint_id="cp-2", message="second", timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc))
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[older, newer])
    registry = build_agent_registry(result)
    assert len(registry.agents) == 1
    agent = registry.agents[0]
    assert agent.latest_checkpoint_id == "cp-2"
    assert agent.current_activity == "second"
    assert agent.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert agent.updated_at == datetime(2026, 1, 2, tzinfo=timezone.utc)


def test_different_sessions_produce_separate_agents():
    cp_a = _checkpoint(checkpoint_id="cp-1", session_id="session-a")
    cp_b = _checkpoint(checkpoint_id="cp-2", session_id="session-b")
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[cp_a, cp_b])
    registry = build_agent_registry(result)
    assert {a.session_id for a in registry.agents} == {"session-a", "session-b"}


def test_enriched_checkpoint_sets_agent_id_label():
    # agent_id is populated by normalizer.enrich_checkpoint, not re-derived here —
    # the registry only reads what the Checkpoint already carries.
    cp = _checkpoint(
        detail_level=DetailLevel.ENRICHED,
        agent_id="Claude Code",
        sessions=[SessionDetail(index=0, agent="Claude Code")],
    )
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[cp])
    registry = build_agent_registry(result)
    assert registry.agents[0].agent_id == "Claude Code"
    assert registry.agents[0].name == "Claude Code"


def test_current_activity_prefers_summary_intent_over_message():
    cp = _checkpoint(
        message="raw commit message",
        sessions=[SessionDetail(index=0, summary=SessionSummary(intent="explained intent"))],
    )
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[cp])
    registry = build_agent_registry(result)
    assert registry.agents[0].current_activity == "explained intent"


def test_ok_status_with_zero_checkpoints_yields_empty_agent_list():
    result = IngestionResult(status=IngestionStatus.OK, checkpoints=[])
    registry = build_agent_registry(result)
    assert registry.status == IngestionStatus.OK
    assert registry.agents == []

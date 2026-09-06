import json
from pathlib import Path

import pytest

from app import normalizer
from app.entire_client import EntireCommandError
from app.models import DetailLevel, EvidenceStatus, IngestionStatus
from app.normalizer import (
    enrich_checkpoint,
    ingest_checkpoints,
    is_enrichable,
    normalize_pending_entry,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


FULL_ENVELOPE = {
    "checkpoint_id": "d4e2b8f6c3a1",
    "checkpoints_count": 1,
    "files_touched": ["app/normalizer.py", "app/models.py"],
    "session_count": 1,
    "sessions": [
        {
            "index": 0,
            "session_id": "session-def456",
            "agent": "claude-code",
            "model": "claude-sonnet-5",
            "kind": "code",
            "created_at": "2026-09-06T13:09:00Z",
            "is_task": False,
            "files_touched": ["app/normalizer.py"],
            "token_usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_tokens": 0,
                "cache_creation_tokens": 0,
            },
            "summary": {"intent": "Fix the tier predicate", "outcome": "Fixed"},
        }
    ],
    "partial": False,
}


def test_is_enrichable_true_for_nonempty_condensation_id():
    cp = normalize_pending_entry(_load_fixture("pending_condensed.json")[1])
    assert is_enrichable(cp) is True


def test_is_enrichable_false_for_live_entry():
    cp = normalize_pending_entry(_load_fixture("pending_condensed.json")[0])
    assert is_enrichable(cp) is False


def test_is_enrichable_false_for_flag_like_id():
    cp = normalize_pending_entry(_load_fixture("pending_condensed.json")[1])
    cp = cp.model_copy(update={"condensation_id": "--force"})
    assert is_enrichable(cp) is False


def test_enrich_checkpoint_folds_envelope_fields():
    cp = normalize_pending_entry(_load_fixture("pending_condensed.json")[1])
    enriched = enrich_checkpoint(cp, FULL_ENVELOPE)

    assert enriched.detail_level == DetailLevel.ENRICHED
    assert enriched.files_touched == ["app/normalizer.py", "app/models.py"]
    assert len(enriched.sessions) == 1
    assert enriched.agent_id == "claude-code"


def test_ingest_checkpoints_enriches_only_the_condensed_entry(monkeypatch):
    fixture = _load_fixture("pending_condensed.json")
    calls = []

    def fake_explain(checkpoint_id):
        calls.append(checkpoint_id)
        return FULL_ENVELOPE

    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda: fixture)
    monkeypatch.setattr(normalizer.entire_client, "explain_checkpoint", fake_explain)

    result = ingest_checkpoints()

    assert len(calls) == 1
    assert calls[0] == fixture[1]["condensation_id"]

    live_cp = next(c for c in result.checkpoints if c.checkpoint_id == fixture[0]["id"])
    condensed_cp = next(c for c in result.checkpoints if c.checkpoint_id == fixture[1]["id"])
    assert live_cp.detail_level == DetailLevel.LIST_ONLY
    assert condensed_cp.detail_level == DetailLevel.ENRICHED


def test_flag_like_condensation_id_never_reaches_explain(monkeypatch):
    fixture = _load_fixture("pending_condensed.json")
    fixture = [dict(fixture[0]), dict(fixture[1])]
    fixture[1]["condensation_id"] = "--force"

    def fake_explain(checkpoint_id):
        raise AssertionError("explain_checkpoint must not be called for an unsafe ID")

    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda: fixture)
    monkeypatch.setattr(normalizer.entire_client, "explain_checkpoint", fake_explain)

    result = ingest_checkpoints()
    assert result.status == IngestionStatus.OK


def test_enrichment_cap_leaves_overflow_list_only_with_note(monkeypatch):
    entries = []
    for i in range(normalizer.MAX_ENRICHMENT_CALLS + 2):
        entries.append(
            {
                "id": f"cp-{i}",
                "message": "m",
                "metadata_dir": "",
                "date": "2026-09-06T00:00:00Z",
                "is_task_checkpoint": False,
                "tool_use_id": "",
                "is_logs_only": True,
                "condensation_id": f"cond-{i}",
                "session_id": f"session-{i}",
                "session_prompt": "p",
            }
        )

    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda: entries)
    monkeypatch.setattr(normalizer.entire_client, "explain_checkpoint", lambda cid: FULL_ENVELOPE)

    result = ingest_checkpoints()

    enriched_count = sum(1 for c in result.checkpoints if c.detail_level == DetailLevel.ENRICHED)
    list_only_count = sum(1 for c in result.checkpoints if c.detail_level == DetailLevel.LIST_ONLY)
    assert enriched_count == normalizer.MAX_ENRICHMENT_CALLS
    assert list_only_count == 2
    assert len(result.notes) >= 1
    assert "MAX_ENRICHMENT_CALLS" in result.notes[0]

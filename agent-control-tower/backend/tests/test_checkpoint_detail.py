import json
from pathlib import Path

from app import normalizer
from app.models import DetailLevel, EvidenceStatus
from app.normalizer import get_checkpoint

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


FULL_ENVELOPE = {
    "checkpoint_id": "d4e2b8f6c3a1",
    "files_touched": ["app/normalizer.py"],
    "sessions": [
        {
            "index": 0,
            "agent": "claude-code",
            "summary": {"intent": "Fix the tier predicate", "outcome": "Fixed"},
        }
    ],
    "partial": False,
}


def test_get_checkpoint_returns_none_when_not_in_pending_list(monkeypatch):
    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda **_: [])
    assert get_checkpoint("does-not-exist") is None


def test_get_checkpoint_returns_list_only_entry_unenriched(monkeypatch):
    fixture = _load_fixture("pending_condensed.json")
    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda **_: fixture)

    cp = get_checkpoint(fixture[0]["id"])

    assert cp is not None
    assert cp.detail_level == DetailLevel.LIST_ONLY


def test_get_checkpoint_force_enriches_beyond_bulk_cap(monkeypatch):
    fixture = _load_fixture("pending_condensed.json")
    calls = []

    def fake_explain(checkpoint_id, **_):
        calls.append(checkpoint_id)
        return FULL_ENVELOPE

    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda **_: fixture)
    monkeypatch.setattr(normalizer.entire_client, "explain_checkpoint", fake_explain)
    monkeypatch.setattr(normalizer, "MAX_ENRICHMENT_CALLS", 0)  # bulk cap would skip everything

    cp = get_checkpoint(fixture[1]["id"])

    assert len(calls) == 1
    assert cp is not None
    assert cp.detail_level == DetailLevel.ENRICHED
    assert cp.agent_id == "claude-code"


def test_get_checkpoint_isolates_explain_failure(monkeypatch):
    from app.entire_client import EntireCommandError

    fixture = _load_fixture("pending_condensed.json")

    def raise_error(checkpoint_id, **_):
        raise EntireCommandError(["checkpoint", "explain", checkpoint_id], 1, "boom")

    monkeypatch.setattr(normalizer.entire_client, "list_pending_checkpoints", lambda **_: fixture)
    monkeypatch.setattr(normalizer.entire_client, "explain_checkpoint", raise_error)

    cp = get_checkpoint(fixture[1]["id"])

    assert cp is not None
    assert cp.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE

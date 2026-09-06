from datetime import datetime, timezone

from app.models import Checkpoint, DetailLevel, EvidenceStatus, SessionDetail, SessionSummary
from app.reconstruction import build_reconstruction_prompt


def test_prompt_is_always_unverified():
    cp = Checkpoint(checkpoint_id="cp-1", message="did a thing")
    result = build_reconstruction_prompt(cp)
    assert result.verification_status == "UNVERIFIED"
    assert result.checkpoint_id == "cp-1"


def test_prompt_includes_recorded_fields_and_warns_about_gaps():
    cp = Checkpoint(
        checkpoint_id="cp-1",
        message="raw message",
        detail_level=DetailLevel.LIST_ONLY,
        unavailable_fields=["transcript", "tool_calls", "commits"],
    )
    result = build_reconstruction_prompt(cp)

    assert "raw message" in result.prompt
    assert "transcript" in result.prompt
    assert "files_touched unavailable" in result.warnings


def test_prompt_prefers_summary_intent_over_raw_message():
    cp = Checkpoint(
        checkpoint_id="cp-1",
        message="raw message",
        detail_level=DetailLevel.ENRICHED,
        files_touched=["a.py"],
        sessions=[SessionDetail(index=0, summary=SessionSummary(intent="the real intent", outcome="done"))],
    )
    result = build_reconstruction_prompt(cp)

    assert "the real intent" in result.prompt
    assert "done" in result.prompt
    assert "a.py" in result.prompt
    assert "files_touched unavailable" not in result.warnings


def test_prompt_surfaces_insufficient_evidence_notes():
    cp = Checkpoint(
        checkpoint_id="cp-1",
        message="m",
        evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
        evidence_notes=["missing or empty required field: id"],
    )
    result = build_reconstruction_prompt(cp)

    assert "missing or empty required field: id" in result.prompt
    assert any("INSUFFICIENT_EVIDENCE" in w for w in result.warnings)


def test_prompt_notes_missing_timestamp():
    cp = Checkpoint(checkpoint_id="cp-1", message="m", timestamp=None)
    result = build_reconstruction_prompt(cp)
    assert "timestamp unavailable" in result.warnings

    cp2 = Checkpoint(checkpoint_id="cp-2", message="m", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    result2 = build_reconstruction_prompt(cp2)
    assert "timestamp unavailable" not in result2.warnings
    assert "2026-01-01" in result2.prompt

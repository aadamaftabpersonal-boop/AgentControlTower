"""Normalization layer between `entire_client`'s raw dicts and `Checkpoint`.

`entire_client.py`'s own docstring defers reshaping to "the normalizer's
job" — this module is that normalizer. It interprets and reshapes what
`entire_client` decodes from CLI stdout; it never invokes a subprocess or
touches the filesystem itself, except through `entire_client` inside
`ingest_checkpoints()`, which is the only function here that does.

The D-01/D-02 tier split (which pending entries can be enriched via
`explain --json`, and which cannot yet because they have no condensed ID)
is resolved entirely by `is_enrichable()`. Every other function asks that
predicate rather than re-testing `condensation_id` itself.
"""

import re
from datetime import datetime

from app import entire_client
from app.entire_client import EntireCommandError
from app.models import Checkpoint, EvidenceStatus, DetailLevel, IngestionResult, IngestionStatus, SessionDetail, SessionSummary, TokenUsage

UNAVAILABLE_FIELDS = ("transcript", "tool_calls", "commits")

# Bounds the explain-enrichment fan-out. `run_json` uses a 30s timeout and
# the CLI caps the pending list at 20 entries (`pendingCheckpointsLimit`), so
# an unbounded enrichment loop is a 600s worst-case hang on a route a live
# dashboard polls (threat T-01-03).
MAX_ENRICHMENT_CALLS = 10

# A checkpoint ID read from CLI stdout becomes argv of another CLI
# invocation. An ID beginning with `-` would be parsed by Cobra as a flag,
# not a positional argument (threat T-01-01). The leading-alphanumeric
# anchor is the load-bearing part.
EXPLAIN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_pending_entry(entry: dict) -> Checkpoint:
    """Map one raw pending-checkpoint dict onto a `Checkpoint`.

    Pure: no subprocess, no filesystem access. Does not raise on a missing
    optional field, and does not raise on a missing `id`/`date` either --
    the evidence-status bookkeeping for those belongs to Task 3's
    INSUFFICIENT EVIDENCE handling.
    """
    checkpoint_id = entry.get("id") or ""
    timestamp = _parse_timestamp(entry.get("date"))

    return Checkpoint(
        checkpoint_id=checkpoint_id,
        condensation_id=entry.get("condensation_id") or None,
        session_id=entry.get("session_id") or None,
        timestamp=timestamp,
        prompt=entry.get("session_prompt") or None,
        message=entry.get("message") or None,
        metadata_dir=entry.get("metadata_dir") or None,
        is_task_checkpoint=bool(entry.get("is_task_checkpoint", False)),
        tool_use_id=entry.get("tool_use_id") or None,
        is_logs_only=bool(entry.get("is_logs_only", False)),
        unavailable_fields=list(UNAVAILABLE_FIELDS),
        raw=entry,
    )


def is_enrichable(cp: Checkpoint) -> bool:
    """True when `cp.condensation_id` is a non-empty, safe-to-pass ID.

    This single predicate is the whole D-01/D-02 resolution: a live
    shadow-branch entry has no condensation_id yet and stays list_only; a
    logs-only/condensed entry has one and can be enriched via
    `explain --json`.
    """
    return bool(cp.condensation_id) and bool(EXPLAIN_ID_PATTERN.match(cp.condensation_id))


def normalize_explain_envelope(
    envelope: dict,
) -> tuple[list[str], list[SessionDetail], list[str]]:
    """Map an explain envelope onto `(files_touched, sessions, evidence_notes)`.

    Pure. `evidence_notes` here is the collected per-session `error` strings;
    Task 3 wires the `partial` flag and this list into `evidence_status`.
    """
    files_touched = list(envelope.get("files_touched") or [])
    evidence_notes: list[str] = []
    sessions: list[SessionDetail] = []

    for raw_session in envelope.get("sessions") or []:
        token_usage_raw = raw_session.get("token_usage")
        token_usage = TokenUsage(**token_usage_raw) if token_usage_raw else None

        summary_raw = raw_session.get("summary")
        summary = (
            SessionSummary(intent=summary_raw.get("intent"), outcome=summary_raw.get("outcome"))
            if summary_raw
            else None
        )

        created_at = _parse_timestamp(raw_session.get("created_at"))
        error = raw_session.get("error") or None

        sessions.append(
            SessionDetail(
                index=raw_session.get("index", 0),
                session_id=raw_session.get("session_id") or None,
                agent=raw_session.get("agent") or None,
                model=raw_session.get("model") or None,
                kind=raw_session.get("kind") or None,
                created_at=created_at,
                is_task=bool(raw_session.get("is_task", False)),
                tool_use_id=raw_session.get("tool_use_id") or None,
                files_touched=list(raw_session.get("files_touched") or []),
                token_usage=token_usage,
                summary=summary,
                error=error,
            )
        )
        if error:
            evidence_notes.append(f"session {raw_session.get('index', 0)}: {error}")

    return files_touched, sessions, evidence_notes


def enrich_checkpoint(cp: Checkpoint, envelope: dict) -> Checkpoint:
    """Fold an explain envelope onto a copy of `cp`.

    Pure. `unavailable_fields` is unchanged -- enrichment does not make
    transcripts or tool calls available.
    """
    files_touched, sessions, session_errors = normalize_explain_envelope(envelope)

    agent_id = next((s.agent for s in sessions if s.agent), None)

    evidence_status = cp.evidence_status
    evidence_notes = list(cp.evidence_notes)
    if envelope.get("partial") or session_errors:
        evidence_status = EvidenceStatus.INSUFFICIENT_EVIDENCE
        if envelope.get("partial"):
            evidence_notes.append("explain envelope reported partial: true")
        evidence_notes.extend(session_errors)

    return cp.model_copy(
        update={
            "files_touched": files_touched,
            "sessions": sessions,
            "detail_level": DetailLevel.ENRICHED,
            "agent_id": agent_id,
            "evidence_status": evidence_status,
            "evidence_notes": evidence_notes,
        }
    )


def ingest_checkpoints() -> IngestionResult:
    """Read the pending checkpoint dataset and normalize it into a result.

    Per D-04, `EntireCommandError`, `FileNotFoundError`, and
    `subprocess.TimeoutExpired` raised by `list_pending_checkpoints` are
    deliberately not caught here -- letting them propagate is the deferred
    behaviour, distinct from the two evidence states this function returns
    explicitly. A per-entry `explain_checkpoint` failure is isolated instead
    (Task 3) and does not abort the whole ingestion.
    """
    entries = entire_client.list_pending_checkpoints()

    checkpoints = [normalize_pending_entry(entry) for entry in entries]

    notes: list[str] = []
    enrichment_calls = 0
    overflow_count = 0
    result_checkpoints: list[Checkpoint] = []

    for cp in checkpoints:
        if not is_enrichable(cp):
            result_checkpoints.append(cp)
            continue

        if enrichment_calls >= MAX_ENRICHMENT_CALLS:
            overflow_count += 1
            result_checkpoints.append(cp)
            continue

        enrichment_calls += 1
        try:
            envelope = entire_client.explain_checkpoint(cp.condensation_id)
            result_checkpoints.append(enrich_checkpoint(cp, envelope))
        except EntireCommandError as exc:
            result_checkpoints.append(
                cp.model_copy(
                    update={
                        "evidence_status": EvidenceStatus.INSUFFICIENT_EVIDENCE,
                        "evidence_notes": [*cp.evidence_notes, str(exc)],
                    }
                )
            )

    if overflow_count:
        notes.append(
            f"MAX_ENRICHMENT_CALLS ({MAX_ENRICHMENT_CALLS}) reached; "
            f"{overflow_count} enrichable checkpoint(s) left list_only"
        )

    return IngestionResult(
        status=IngestionStatus.OK,
        checkpoints=result_checkpoints,
        notes=notes,
        source="entire checkpoint list --pending --json",
    )

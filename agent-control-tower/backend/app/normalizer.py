"""Normalization layer between `entire_client`'s raw dicts and `Checkpoint`.

`entire_client.py`'s own docstring defers reshaping to "the normalizer's
job" — this module is that normalizer. It interprets and reshapes what
`entire_client` decodes from CLI stdout; it never invokes a subprocess or
touches the filesystem itself, except through `entire_client` inside
`ingest_checkpoints()`, which is the only function here that does.
"""

from datetime import datetime

from app import entire_client
from app.models import Checkpoint, IngestionResult, IngestionStatus

UNAVAILABLE_FIELDS = ("transcript", "tool_calls", "commits")


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


def ingest_checkpoints() -> IngestionResult:
    """Read the pending checkpoint dataset and normalize it into a result.

    Per D-04, `EntireCommandError`, `FileNotFoundError`, and
    `subprocess.TimeoutExpired` are deliberately not caught here -- letting
    them propagate is the deferred behaviour, distinct from the two evidence
    states this function returns explicitly.
    """
    entries = entire_client.list_pending_checkpoints()

    checkpoints = [normalize_pending_entry(entry) for entry in entries]

    return IngestionResult(
        status=IngestionStatus.OK,
        checkpoints=checkpoints,
        notes=[],
        source="entire checkpoint list --pending --json",
    )

"""Generate a self-contained continuation prompt from one checkpoint.

Scoped-down version of the PRD's V7 hero feature (full historical-cutoff
reconstruction across a session's entire checkpoint history, filtering out
any fact first introduced after the selected point). That needs a real
per-session timeline this V1 ingestion layer doesn't build yet -- ingestion
here reads the *current* pending snapshot, not a session's full history.

What this module does instead: assemble a prompt entirely from one
checkpoint's own fields. Because the prompt draws from exactly one
checkpoint, there is no later-checkpoint fact it could leak -- the
single-checkpoint scope is what keeps the "no future information" invariant
trivially true rather than requiring a cutoff filter. Every fact the
checkpoint doesn't carry (transcript, tool calls, commits, and anything
enrichment didn't provide) is named as unknown, never invented, per
PROJECT.md's core value. `verification_status` is always UNVERIFIED --
replay-fidelity verification (V13) doesn't exist at any scope yet.
"""

from app.models import Checkpoint, EvidenceStatus, ReconstructionPrompt


def build_reconstruction_prompt(cp: Checkpoint) -> ReconstructionPrompt:
    warnings: list[str] = []

    lines = [
        "You are continuing work on a codebase from a specific Entire checkpoint.",
        "This prompt was generated from exactly one checkpoint's recorded evidence.",
        "It is UNVERIFIED: no replay/fidelity check has confirmed it reproduces the",
        "original state, and any fact not listed below was NOT available -- do not",
        "assume or invent it.",
        "",
        f"## Checkpoint {cp.checkpoint_id}",
    ]

    if cp.timestamp:
        lines.append(f"- Recorded at: {cp.timestamp.isoformat()}")
    else:
        lines.append("- Recorded at: unknown (checkpoint had no parseable timestamp)")
        warnings.append("timestamp unavailable")

    if cp.session_id:
        lines.append(f"- Session: {cp.session_id}")

    objective = None
    for session in cp.sessions:
        if session.summary and session.summary.intent:
            objective = session.summary.intent
            break
    objective = objective or cp.prompt or cp.message

    if objective:
        lines.append(f"- Stated objective / intent: {objective}")
    else:
        lines.append("- Stated objective / intent: unknown -- no prompt, message, or summary was recorded")
        warnings.append("no objective/intent recorded")

    outcome = next((s.summary.outcome for s in cp.sessions if s.summary and s.summary.outcome), None)
    if outcome:
        lines.append(f"- Recorded outcome: {outcome}")

    if cp.files_touched:
        lines.append("")
        lines.append("## Files touched as of this checkpoint")
        lines.extend(f"- {f}" for f in cp.files_touched)
    else:
        lines.append("")
        lines.append("## Files touched")
        lines.append(
            "Unknown -- this checkpoint's file list was not available "
            f"(detail_level={cp.detail_level.value})."
        )
        warnings.append("files_touched unavailable")

    if cp.unavailable_fields:
        lines.append("")
        lines.append("## Explicitly unavailable (do not invent these)")
        lines.extend(f"- {field}" for field in cp.unavailable_fields)

    if cp.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
        lines.append("")
        lines.append("## Evidence gaps in this checkpoint")
        lines.extend(f"- {note}" for note in cp.evidence_notes)
        warnings.append("checkpoint evidence_status is INSUFFICIENT_EVIDENCE")

    lines.append("")
    lines.append("## Task")
    lines.append(
        "Starting from the current state of this repository, pick up the objective "
        "above. Do not assume any work exists beyond what's listed here as evidence."
    )

    return ReconstructionPrompt(
        checkpoint_id=cp.checkpoint_id,
        prompt="\n".join(lines),
        verification_status="UNVERIFIED",
        warnings=warnings,
    )

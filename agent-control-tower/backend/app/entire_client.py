"""Thin subprocess wrapper around the `entire` CLI.

Every Entire-derived fact in this backend flows through here so there is
exactly one place that knows how to invoke the CLI and parse its output.
Callers get back plain dicts/lists decoded from `--json` output; nothing
here interprets or reshapes the data, that's the normalizer's job.
"""

import json
import subprocess

from app.config import settings


class EntireCommandError(RuntimeError):
    def __init__(self, args: list[str], returncode: int, stderr: str) -> None:
        super().__init__(f"entire {' '.join(args)} failed ({returncode}): {stderr.strip()}")
        self.args_ = args
        self.returncode = returncode
        self.stderr = stderr


def run_json(args: list[str], allow_nonzero_exit: bool = False) -> dict | list:
    """Run `entire <args...> --json` in the configured repo and decode stdout.

    `entire checkpoint explain --json` deliberately exits non-zero when its
    envelope is `partial`, after already writing the full valid envelope to
    stdout -- the CLI's own doc comment says the exit code exists so
    "automation doesn't mistake incomplete data for a clean export". Passing
    `allow_nonzero_exit=True` reads that envelope instead of discarding it;
    it still raises `EntireCommandError` if stdout is empty or undecodable.
    """
    result = subprocess.run(
        [settings.entire_bin, *args, "--json"],
        cwd=settings.repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        if not allow_nonzero_exit:
            raise EntireCommandError(args, result.returncode, result.stderr)
        if not result.stdout:
            raise EntireCommandError(args, result.returncode, result.stderr)
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise EntireCommandError(args, result.returncode, result.stderr) from exc
    return json.loads(result.stdout)


def list_checkpoints() -> list[dict]:
    data = run_json(["checkpoint", "list"])
    if isinstance(data, dict):
        return data.get("checkpoints", [])
    return data


def list_pending_checkpoints() -> list[dict]:
    """Return the pending (live + logs-only) checkpoint dataset.

    This is the D-01 dataset: `entire checkpoint list --pending --json`.
    It differs from `list_checkpoints()`'s condensed dataset in that it
    surfaces shadow-branch checkpoints that have not yet been committed,
    which is what makes "live" ingestion possible.
    """
    data = run_json(["checkpoint", "list", "--pending"])
    if isinstance(data, dict):
        return data.get("checkpoints", [])
    if isinstance(data, list):
        return data
    return []


def explain_checkpoint(checkpoint_id: str) -> dict:
    """Fetch the per-checkpoint detail envelope for an already-condensed ID.

    Uses `allow_nonzero_exit=True` since a `partial` envelope is still valid
    JSON worth reading (see `run_json`'s docstring).
    """
    data = run_json(["checkpoint", "explain", checkpoint_id], allow_nonzero_exit=True)
    return data if isinstance(data, dict) else {}


def status() -> dict:
    data = run_json(["status"])
    return data if isinstance(data, dict) else {}

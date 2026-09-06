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


def run_json(args: list[str]) -> dict | list:
    """Run `entire <args...> --json` in the configured repo and decode stdout."""
    result = subprocess.run(
        [settings.entire_bin, *args, "--json"],
        cwd=settings.repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise EntireCommandError(args, result.returncode, result.stderr)
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


def status() -> dict:
    data = run_json(["status"])
    return data if isinstance(data, dict) else {}

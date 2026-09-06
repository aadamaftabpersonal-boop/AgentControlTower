"""Resolve a user-supplied repo target (local folder or clonable URL) to a
filesystem path the rest of the backend can point `entire` at.

This is what makes the dashboard show a repo other than the one the backend
was started against: every ingestion call takes an optional `repo` string
from the request, and this module turns it into a real, existing directory
for `entire_client.run_json`'s `repo_root` override.

Cloned repos are cached under the OS temp dir, keyed by a hash of the URL,
and reused across requests rather than re-cloned every poll -- a shallow
clone is still a real network+git cost, and the SSE stream polls every few
seconds. This does not `entire enable` the clone: a repo that already used
Entire during its own development (the common, interesting case for a demo
-- e.g. entireio/cli's own history) has real checkpoint refs the moment
it's cloned; a repo that never used Entire legitimately has none, and
`ingest_checkpoints` already reports that as WAITING FOR AGENT ACTIVITY
either way; inventing a `.entire` setup as a strike-through side effect of
"look at this repo" would be a surprise, not a feature.
"""

import hashlib
import subprocess
import tempfile
from pathlib import Path

CACHE_ROOT = Path(tempfile.gettempdir()) / "act-repo-cache"
CLONE_TIMEOUT_SECONDS = 60


class RepoResolutionError(RuntimeError):
    """A repo target could not be resolved to a usable local directory."""


def _is_clonable_url(target: str) -> bool:
    return target.startswith(("http://", "https://", "git@", "ssh://"))


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _clone_or_reuse(url: str) -> Path:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    dest = CACHE_ROOT / _cache_key(url)

    if (dest / ".git").is_dir():
        return dest

    if dest.exists():
        raise RepoResolutionError(f"cache path exists but is not a git repo: {dest}")

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RepoResolutionError(f"cloning {url} timed out after {CLONE_TIMEOUT_SECONDS}s") from exc

    if result.returncode != 0:
        raise RepoResolutionError(f"git clone of {url} failed: {result.stderr.strip()}")

    return dest


def resolve_repo_root(target: str | None, default: Path) -> Path:
    """Resolve `target` to an existing directory, or fall back to `default`.

    `target` is treated as a clonable URL if it looks like one (http(s)://,
    git@, ssh://), otherwise as a local filesystem path. An empty/None
    target returns `default` unchanged -- the backend's own configured repo.
    """
    if not target or not target.strip():
        return default

    target = target.strip()

    if _is_clonable_url(target):
        return _clone_or_reuse(target)

    path = Path(target).expanduser().resolve()
    if not path.is_dir():
        raise RepoResolutionError(f"not a directory: {path}")
    if not (path / ".git").exists():
        raise RepoResolutionError(f"not a git repository (no .git found): {path}")
    return path

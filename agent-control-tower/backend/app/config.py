import os
from pathlib import Path


class Settings:
    """Runtime configuration for the Agent Control Tower backend.

    repo_root points at the git worktree whose Entire checkpoints/sessions
    this backend ingests. It defaults to the current working directory so
    the server can be launched from the target repo, but can be overridden
    for local development against a different checkout.
    """

    def __init__(self) -> None:
        self.repo_root: Path = Path(os.environ.get("ACT_REPO_ROOT", os.getcwd())).resolve()
        self.entire_bin: str = os.environ.get("ACT_ENTIRE_BIN", "entire")


settings = Settings()

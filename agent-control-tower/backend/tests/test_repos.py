from pathlib import Path

import pytest

from app.repos import RepoResolutionError, resolve_repo_root


def test_empty_target_returns_default(tmp_path):
    assert resolve_repo_root(None, default=tmp_path) == tmp_path
    assert resolve_repo_root("   ", default=tmp_path) == tmp_path


def test_local_path_target_must_exist_and_be_a_git_repo(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(RepoResolutionError):
        resolve_repo_root(str(missing), default=tmp_path)

    not_git = tmp_path / "plain-dir"
    not_git.mkdir()
    with pytest.raises(RepoResolutionError):
        resolve_repo_root(str(not_git), default=tmp_path)

    real_repo = tmp_path / "real-repo"
    (real_repo / ".git").mkdir(parents=True)
    assert resolve_repo_root(str(real_repo), default=tmp_path) == real_repo.resolve()


def test_url_target_is_detected_by_scheme(tmp_path, monkeypatch):
    called = {}

    def fake_clone(url: str) -> Path:
        called["url"] = url
        return tmp_path / "cloned"

    import app.repos as repos_module

    monkeypatch.setattr(repos_module, "_clone_or_reuse", fake_clone)

    result = resolve_repo_root("https://github.com/example/repo.git", default=tmp_path)
    assert called["url"] == "https://github.com/example/repo.git"
    assert result == tmp_path / "cloned"

import json
import subprocess

import pytest

from app import entire_client


def test_run_json_decodes_stdout(monkeypatch):
    def fake_run(args, cwd, capture_output, text, timeout):
        assert args[0] == entire_client.settings.entire_bin
        assert args[-1] == "--json"
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"ok": True}), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert entire_client.run_json(["status"]) == {"ok": True}


def test_run_json_raises_on_nonzero_exit(monkeypatch):
    def fake_run(args, cwd, capture_output, text, timeout):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(entire_client.EntireCommandError):
        entire_client.run_json(["status"])


def test_list_checkpoints_unwraps_dict_shape(monkeypatch):
    monkeypatch.setattr(entire_client, "run_json", lambda args: {"checkpoints": [{"id": "1"}]})
    assert entire_client.list_checkpoints() == [{"id": "1"}]


def test_list_checkpoints_passes_through_list_shape(monkeypatch):
    monkeypatch.setattr(entire_client, "run_json", lambda args: [{"id": "1"}])
    assert entire_client.list_checkpoints() == [{"id": "1"}]


def test_list_pending_checkpoints_invokes_pending_json_args(monkeypatch):
    captured = {}

    def fake_run(args, cwd, capture_output, text, timeout):
        captured["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps([]), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    entire_client.list_pending_checkpoints()
    assert captured["args"][-4:] == ["checkpoint", "list", "--pending", "--json"]
    assert captured["args"][0] == entire_client.settings.entire_bin


def test_run_json_allow_nonzero_exit_returns_decoded_stdout(monkeypatch):
    def fake_run(args, cwd, capture_output, text, timeout):
        return subprocess.CompletedProcess(args, 1, stdout=json.dumps({"partial": True}), stderr="incomplete")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert entire_client.run_json(["checkpoint", "explain", "abc"], allow_nonzero_exit=True) == {
        "partial": True
    }


def test_run_json_allow_nonzero_exit_raises_on_empty_stdout(monkeypatch):
    def fake_run(args, cwd, capture_output, text, timeout):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(entire_client.EntireCommandError):
        entire_client.run_json(["checkpoint", "explain", "abc"], allow_nonzero_exit=True)

"""Tests unitarios para el actualizador automático de job0t."""

from pathlib import Path
import httpx
from job0t.updater import (
    check_uncommitted_changes,
    get_app_root,
    get_current_git_branch,
    get_local_commit_sha,
    get_remote_commit_info,
)


def test_get_app_root():
    root = get_app_root()
    assert root.exists()
    assert (root / "pyproject.toml").exists()


def test_get_current_git_branch():
    root = get_app_root()
    branch = get_current_git_branch(root)
    assert branch is not None
    assert branch in ("main", "master", "develop")


def test_get_local_commit_sha():
    root = get_app_root()
    sha = get_local_commit_sha(root)
    assert sha is not None
    assert len(sha) == 40


def test_get_remote_commit_info_success(monkeypatch):
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200

            def json(self):
                return {
                    "sha": "1234567890abcdef1234567890abcdef12345678",
                    "commit": {"message": "feat: release new version\n\nExtra details"},
                }

        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)
    sha, msg, err = get_remote_commit_info("main")
    assert sha == "1234567890abcdef1234567890abcdef12345678"
    assert msg == "feat: release new version"
    assert err is None


def test_get_remote_commit_info_rate_limit(monkeypatch):
    def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 403

        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)
    sha, msg, err = get_remote_commit_info("main")
    assert sha is None
    assert "Límite de peticiones" in err


def test_get_remote_commit_info_network_error(monkeypatch):
    def mock_get(*args, **kwargs):
        raise httpx.RequestError("Connection timeout")

    monkeypatch.setattr(httpx, "get", mock_get)
    sha, msg, err = get_remote_commit_info("main")
    assert sha is None
    assert "No se pudo conectar" in err

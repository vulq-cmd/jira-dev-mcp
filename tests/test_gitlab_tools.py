"""Tests for GitLab read-only tools: project encoding, trims, diff cap,
graceful degrade, not-configured path. All HTTP mocked with respx.
"""
import os

import httpx
import respx

import gitlab_client
from gitlab_client import encode_project
from tools import gitlab_tools

API = "https://gitlab.example.com/api/v4"
SECRET = os.environ["GITLAB_TOKEN"]


def test_encode_project_numeric_and_path():
    assert encode_project(123) == "123"
    assert encode_project("123") == "123"
    assert encode_project("group/sub/repo") == "group%2Fsub%2Frepo"


def test_search_mrs_trims_and_flags_heuristic():
    payload = [
        {
            "iid": 7,
            "title": "PROJ-123 add regions",
            "state": "merged",
            "source_branch": "feature/PROJ-123",
            "target_branch": "main",
            "author": {"name": "Dev"},
            "web_url": "https://gitlab.example.com/x/-/merge_requests/7",
        }
    ]
    with respx.mock(base_url=API) as mock:
        mock.get("/merge_requests").mock(return_value=httpx.Response(200, json=payload))
        out = gitlab_tools.gitlab_search_mrs("PROJ-123")
    assert out["count"] == 1
    assert out["merge_requests"][0]["iid"] == 7
    assert "candidates" in out["note"]


def test_commit_diff_truncates_and_caps_files():
    diffs = [
        {"old_path": f"f{i}.js", "new_path": f"f{i}.js", "diff": "x" * 2000}
        for i in range(20)
    ]
    with respx.mock(base_url=API) as mock:
        mock.get("/projects/9/repository/commits/abc/diff").mock(
            return_value=httpx.Response(200, json=diffs)
        )
        out = gitlab_tools.gitlab_get_commit_diff("9", "abc")
    assert out["files_changed"] == 20
    assert out["files_shown"] == gitlab_tools.MAX_DIFF_FILES
    assert out["omitted"] == 20 - gitlab_tools.MAX_DIFF_FILES
    assert out["files"][0]["diff"].endswith("chars]")  # truncated


def test_pipeline_status_for_ref():
    with respx.mock(base_url=API) as mock:
        mock.get("/projects/9/pipelines/latest").mock(
            return_value=httpx.Response(200, json={"id": 1, "status": "success", "ref": "main",
                                                   "sha": "deadbeefcafe"})
        )
        out = gitlab_tools.gitlab_get_pipeline_status("9", ref="main")
    assert out["status"] == "success"
    assert out["sha"] == "deadbeef"  # shortened


def test_code_search_degrades_gracefully():
    with respx.mock(base_url=API) as mock:
        mock.get("/search").mock(return_value=httpx.Response(403, text="forbidden"))
        out = gitlab_tools.gitlab_search_code("foo")
    assert "unavailable" in out["error"]
    assert "hint" in out


def test_get_file_decodes_base64():
    import base64

    raw = "console.log('hi')\n"
    payload = {
        "file_path": "src/a.js",
        "size": len(raw),
        "encoding": "base64",
        "content": base64.b64encode(raw.encode()).decode(),
    }
    with respx.mock(base_url=API) as mock:
        mock.get("/projects/9/repository/files/src%2Fa.js").mock(
            return_value=httpx.Response(200, json=payload)
        )
        out = gitlab_tools.gitlab_get_file("9", "src/a.js", ref="main")
    assert "console.log" in out["content"]


def test_not_configured_returns_friendly_message(monkeypatch):
    monkeypatch.setattr(gitlab_client, "gitlab_client", None)
    out = gitlab_tools.gitlab_get_mr("9", 1)
    assert out == gitlab_client.NOT_CONFIGURED
    assert SECRET not in str(out)

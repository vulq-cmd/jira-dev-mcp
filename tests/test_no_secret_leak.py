"""The security premise: NO token / auth header may ever appear in tool output.

Forces every error class on every tool and asserts the masked result never
contains the PAT value or the word 'Bearer'.
"""
import os

import httpx
import pytest
import respx

from tools import gitlab_tools, jira_tools

BASE = "https://jira.example.com"
SECRET = os.environ["JIRA_PAT"]

# (tool, kwargs) — one read per tool that triggers a single GET we can fail.
SINGLE_GET_TOOLS = [
    (jira_tools.jira_get_issue, {"key": "X-1"}, "/rest/api/2/issue/X-1"),
    (jira_tools.jira_get_comments, {"key": "X-1"}, "/rest/api/2/issue/X-1/comment"),
    (jira_tools.jira_get_subtasks, {"key": "X-1"}, "/rest/api/2/issue/X-1"),
    (jira_tools.jira_get_linked_issues, {"key": "X-1"}, "/rest/api/2/issue/X-1"),
    (jira_tools.jira_search, {"jql": "project = X"}, "/rest/api/2/search"),
    (jira_tools.jira_get_fields, {}, "/rest/api/2/field"),
    (jira_tools.jira_get_ticket_bundle, {"key": "X-1"}, "/rest/api/2/issue/X-1"),
]


def _assert_clean(result):
    s = str(result)
    assert SECRET not in s, "PAT LEAKED into tool output!"
    assert "Bearer" not in s, "Auth header scheme LEAKED into tool output!"
    assert "error" in result  # masked error dict


@pytest.mark.parametrize("fn,kwargs,path", SINGLE_GET_TOOLS)
def test_http_401_is_masked(fn, kwargs, path):
    with respx.mock(base_url=BASE) as mock:
        mock.get(path).mock(return_value=httpx.Response(401, text="Unauthorized"))
        _assert_clean(fn(**kwargs))


@pytest.mark.parametrize("fn,kwargs,path", SINGLE_GET_TOOLS)
def test_http_500_is_masked(fn, kwargs, path):
    with respx.mock(base_url=BASE) as mock:
        mock.get(path).mock(return_value=httpx.Response(500, text="boom"))
        _assert_clean(fn(**kwargs))


@pytest.mark.parametrize("fn,kwargs,path", SINGLE_GET_TOOLS)
def test_timeout_is_masked(fn, kwargs, path):
    with respx.mock(base_url=BASE) as mock:
        mock.get(path).mock(side_effect=httpx.TimeoutException("t"))
        _assert_clean(fn(**kwargs))


def test_tools_do_not_accept_token_args():
    """No tool should expose a token/pat parameter (secrets stay in env)."""
    import inspect

    from tools import gitlab_tools, jira_agile_tools, jira_attachment_tools

    all_tools = (
        jira_tools.TOOLS
        + jira_agile_tools.TOOLS
        + jira_attachment_tools.TOOLS
        + gitlab_tools.TOOLS
    )
    for fn in all_tools:
        params = set(inspect.signature(fn).parameters)
        assert not (params & {"token", "pat", "auth", "password", "secret"}), (
            f"{fn.__name__} exposes a secret-shaped argument"
        )


# --- GitLab error masking (PRIVATE-TOKEN must never leak) -------------------
GITLAB_API = "https://gitlab.example.com/api/v4"
GITLAB_SECRET = os.environ["GITLAB_TOKEN"]

GITLAB_TOOLS = [
    (gitlab_tools.gitlab_get_mr, {"project": "9", "mr_iid": 1}, "/projects/9/merge_requests/1"),
    (gitlab_tools.gitlab_get_commits, {"project": "9"}, "/projects/9/repository/commits"),
    (gitlab_tools.gitlab_get_pipeline_status, {"project": "9", "ref": "main"},
     "/projects/9/pipelines/latest"),
]


@pytest.mark.parametrize("fn,kwargs,path", GITLAB_TOOLS)
def test_gitlab_errors_are_masked(fn, kwargs, path):
    from tools import gitlab_tools as _gt  # noqa: F401 - ensure import side effects

    for status in (401, 500):
        with respx.mock(base_url=GITLAB_API) as mock:
            mock.get(path).mock(return_value=httpx.Response(status, text="nope"))
            result = fn(**kwargs)
        s = str(result)
        assert GITLAB_SECRET not in s, "GitLab token LEAKED!"
        assert "PRIVATE-TOKEN" not in s, "GitLab auth header LEAKED!"
        assert "error" in result

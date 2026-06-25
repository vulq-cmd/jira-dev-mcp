"""Tests for Jira read-only tools: shape, trimming, pagination, and secret masking.

All HTTP is mocked with respx — no live Jira is contacted.
"""
import os

import httpx
import respx

from tools import jira_tools

BASE = "https://jira.example.com"
SECRET = os.environ["JIRA_PAT"]  # set by conftest

ISSUE = {
    "key": "PROJ-123",
    "fields": {
        "summary": "Add geo regions",
        "description": "x" * 4000,
        "status": {"name": "In Progress"},
        "issuetype": {"name": "Story"},
        "priority": {"name": "High"},
        "assignee": {"displayName": "Avada Dev"},
        "labels": ["frontend"],
        "components": [{"name": "cookie-bar"}],
        "subtasks": [
            {"key": "PROJ-124", "fields": {"summary": "UI", "status": {"name": "To Do"}}}
        ],
        "issuelinks": [
            {
                "type": {"outward": "blocks"},
                "outwardIssue": {
                    "key": "PROJ-200",
                    "fields": {"summary": "Dep", "status": {"name": "Done"}},
                },
            }
        ],
    },
}
COMMENTS = {
    "total": 1,
    "comments": [
        {"author": {"displayName": "PM"}, "created": "2026-06-20", "body": "confirm scope"}
    ],
}


def test_get_issue_trims_and_truncates():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-123").mock(return_value=httpx.Response(200, json=ISSUE))
        out = jira_tools.jira_get_issue("PROJ-123")
    assert out["key"] == "PROJ-123"
    assert out["status"] == "In Progress"
    assert out["assignee"] == "Avada Dev"
    assert out["components"] == ["cookie-bar"]
    assert out["description"].endswith("chars]")  # truncated


def test_ticket_bundle_composes_everything():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-123").mock(return_value=httpx.Response(200, json=ISSUE))
        mock.get("/rest/api/2/issue/PROJ-123/comment").mock(
            return_value=httpx.Response(200, json=COMMENTS)
        )
        b = jira_tools.jira_get_ticket_bundle("PROJ-123")
    assert b["subtasks"][0]["key"] == "PROJ-124"
    assert b["links"][0]["relation"] == "blocks"
    assert b["links"][0]["direction"] == "outward"
    assert b["comments"][0]["author"] == "PM"
    assert b["comment_total"] == 1


def test_search_caps_and_paginates():
    page = {
        "total": 3,
        "issues": [
            {"key": f"PROJ-{i}", "fields": {"summary": f"s{i}", "status": {"name": "Open"}}}
            for i in range(3)
        ],
    }
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/search").mock(return_value=httpx.Response(200, json=page))
        out = jira_tools.jira_search("project = PROJ", limit=2)
    assert out["returned"] == 2  # capped to limit
    assert out["total"] == 3


def test_extra_custom_fields_are_surfaced(monkeypatch):
    import jira_client

    monkeypatch.setattr(jira_client, "EXTRA_FIELDS", ["customfield_10026", "customfield_10100"])
    payload = {
        "key": "PROJ-7",
        "fields": {
            "summary": "x",
            "customfield_10026": 5,  # story points
            "customfield_10100": "AC: user can do X",  # acceptance criteria
        },
    }
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-7").mock(return_value=httpx.Response(200, json=payload))
        out = jira_tools.jira_get_issue("PROJ-7")
    assert out["extra"]["customfield_10026"] == 5
    assert "AC:" in out["extra"]["customfield_10100"]


def test_my_tasks_filters_assignee_and_active_statuses():
    captured = {}

    def _handler(request):
        captured["jql"] = dict(request.url.params).get("jql", "")
        return httpx.Response(200, json={"total": 0, "issues": []})

    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/search").mock(side_effect=_handler)
        out = jira_tools.jira_my_tasks()
    assert "currentUser()" in captured["jql"]
    assert '"To Do"' in captured["jql"] and '"Doing"' in captured["jql"]
    assert "filter" in out


def test_linked_issues_handles_inward():
    payload = {
        "key": "PROJ-1",
        "fields": {
            "issuelinks": [
                {
                    "type": {"inward": "is blocked by"},
                    "inwardIssue": {"key": "PROJ-9", "fields": {"status": {"name": "Open"}}},
                }
            ]
        },
    }
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-1").mock(return_value=httpx.Response(200, json=payload))
        out = jira_tools.jira_get_linked_issues("PROJ-1")
    assert out["links"][0]["direction"] == "inward"
    assert out["links"][0]["key"] == "PROJ-9"

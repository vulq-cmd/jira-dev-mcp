"""Jira Agile read-only MCP tools (Server/DC, REST /rest/agile/1.0/).

Epics & sprints live under a different base path than core issues. Reuses the
authenticated Jira client + trim helpers from jira_client.
"""
from jira_client import get_json, tool_safe, trim_issue

# Token-efficient field set for issues listed under an epic/sprint.
_LIST_FIELDS = "summary,status,assignee,priority,issuetype,updated"


def _trim_issue_list(data: dict, limit: int) -> dict:
    issues = (data.get("issues") or [])[:limit]
    return {
        "total": data.get("total", len(issues)),
        "returned": len(issues),
        "issues": [trim_issue(i) for i in issues],
    }


@tool_safe
def jira_get_epic(epic_key: str) -> dict:
    """Get a Jira epic by key/id (read-only)."""
    e = get_json(f"/rest/agile/1.0/epic/{epic_key}")
    return {
        "key": e.get("key"),
        "id": e.get("id"),
        "name": e.get("name"),
        "summary": e.get("summary"),
        "done": e.get("done"),
    }


@tool_safe
def jira_get_epic_issues(epic_key: str, limit: int = 50) -> dict:
    """List issues belonging to an epic (read-only)."""
    limit = max(1, min(limit, 100))
    data = get_json(
        f"/rest/agile/1.0/epic/{epic_key}/issue",
        params={"fields": _LIST_FIELDS, "startAt": 0, "maxResults": limit},
    )
    return {"epic": epic_key, **_trim_issue_list(data, limit)}


@tool_safe
def jira_get_sprint(sprint_id: int) -> dict:
    """Get a sprint by id (read-only)."""
    s = get_json(f"/rest/agile/1.0/sprint/{sprint_id}")
    return {
        "id": s.get("id"),
        "name": s.get("name"),
        "state": s.get("state"),
        "startDate": s.get("startDate"),
        "endDate": s.get("endDate"),
        "goal": s.get("goal"),
    }


@tool_safe
def jira_get_sprint_issues(sprint_id: int, limit: int = 50) -> dict:
    """List issues in a sprint (read-only)."""
    limit = max(1, min(limit, 100))
    data = get_json(
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        params={"fields": _LIST_FIELDS, "startAt": 0, "maxResults": limit},
    )
    return {"sprint": sprint_id, **_trim_issue_list(data, limit)}


TOOLS = [
    jira_get_epic,
    jira_get_epic_issues,
    jira_get_sprint,
    jira_get_sprint_issues,
]


def register(mcp) -> None:
    """Register all Jira agile tools on the given FastMCP instance."""
    for fn in TOOLS:
        mcp.tool()(fn)

"""Jira read-only MCP tools (Server/DC, REST v2).

Each tool is wrapped with @tool_safe so any failure returns a masked error dict
(no token leakage). Payloads are trimmed for token efficiency.
"""
import os

from jira_client import (
    DEFAULT_ISSUE_FIELDS,
    attachments_from_fields,
    get_json,
    links_from_fields,
    subtasks_from_fields,
    tool_safe,
    trim_issue,
    truncate,
)

# The default local-dev working set: my tasks in these statuses.
# Override via env JIRA_ACTIVE_STATUSES (comma-separated).
ACTIVE_STATUSES = [
    s.strip() for s in os.getenv("JIRA_ACTIVE_STATUSES", "To Do,Doing").split(",") if s.strip()
]

# Custom multi-user field "Assignees" (≠ standard single "assignee"). Tasks where
# I'm in this field should also count as mine. Set "" to disable. Accepts a field
# NAME (quoted in JQL) or a cf[id]/customfield_xxx reference (used as-is).
ASSIGNEES_FIELD = os.getenv("JIRA_ASSIGNEES_FIELD", "Assignees").strip()


def _assignees_jql_clause() -> str:
    """Extra JQL OR-clause matching the multi-user Assignees field, or '' if disabled."""
    if not ASSIGNEES_FIELD:
        return ""
    ref = (
        ASSIGNEES_FIELD
        if ASSIGNEES_FIELD.startswith(("cf[", "customfield_"))
        else f'"{ASSIGNEES_FIELD}"'
    )
    return f" OR {ref} = currentUser()"


@tool_safe
def jira_get_issue(key: str, fields: str | None = None) -> dict:
    """Fetch a single Jira issue (read-only).

    Args:
        key: Issue key, e.g. 'PROJ-123'.
        fields: Optional comma-separated Jira field list. Defaults to a
            token-efficient set (summary, status, assignee, description, ...).

    Returns:
        Trimmed issue dict. Never includes auth/token data.
    """
    data = get_json(
        f"/rest/api/2/issue/{key}",
        params={"fields": fields or DEFAULT_ISSUE_FIELDS},
    )
    return trim_issue(data)


@tool_safe
def jira_get_comments(key: str, limit: int = 20) -> dict:
    """Fetch comments on a Jira issue (read-only). Returns the most recent `limit`.

    Args:
        key: Issue key, e.g. 'PROJ-123'.
        limit: Max comments to return (newest kept). Default 20.
    """
    data = get_json(f"/rest/api/2/issue/{key}/comment")
    comments = data.get("comments", []) or []
    trimmed = comments[-limit:] if limit and len(comments) > limit else comments
    return {
        "key": key,
        "total": data.get("total", len(comments)),
        "returned": len(trimmed),
        "comments": [
            {
                "author": (c.get("author") or {}).get("displayName"),
                "created": c.get("created"),
                "body": truncate(c.get("body")),
            }
            for c in trimmed
        ],
    }


@tool_safe
def jira_get_subtasks(key: str) -> dict:
    """List subtasks of a Jira issue (read-only)."""
    data = get_json(f"/rest/api/2/issue/{key}", params={"fields": "subtasks"})
    subs = subtasks_from_fields(data.get("fields", {}) or {})
    return {"key": key, "count": len(subs), "subtasks": subs}


@tool_safe
def jira_get_linked_issues(key: str) -> dict:
    """List issues linked to a Jira issue (read-only), with relation + direction."""
    data = get_json(f"/rest/api/2/issue/{key}", params={"fields": "issuelinks"})
    links = links_from_fields(data.get("fields", {}) or {})
    return {"key": key, "count": len(links), "links": links}


@tool_safe
def jira_search(jql: str, fields: str | None = None, limit: int = 25) -> dict:
    """Search Jira issues by JQL (read-only), with offset pagination.

    Args:
        jql: JQL query, e.g. 'project = PROJ AND status = "In Progress"'.
        fields: Optional comma-separated field list.
        limit: Max issues to return (capped at 50).
    """
    limit = max(1, min(limit, 50))
    field_list = fields or "summary,status,assignee,priority,issuetype,parent,updated"
    collected: list = []
    start = 0
    total = 0
    while len(collected) < limit:
        data = get_json(
            "/rest/api/2/search",
            params={
                "jql": jql,
                "fields": field_list,
                "startAt": start,
                "maxResults": min(50, limit - len(collected)),
            },
        )
        total = data.get("total", 0)
        issues = data.get("issues", []) or []
        if not issues:
            break
        collected.extend(issues)
        start += len(issues)
        if start >= total:
            break
    collected = collected[:limit]  # defensive: enforce cap even if server over-returns
    return {
        "jql": jql,
        "total": total,
        "returned": len(collected),
        "issues": [trim_issue(i) for i in collected],
    }


@tool_safe
def jira_my_tasks(extra_jql: str | None = None, limit: int = 25) -> dict:
    """List MY tasks: assigned to me, in active statuses (default: To Do, Doing).

    This is the default local-dev working set — call with no key to see what to
    work on. Override statuses via env JIRA_ACTIVE_STATUSES.

    Args:
        extra_jql: Optional extra JQL ANDed in, e.g. 'project = PROJ'.
        limit: Max tasks to return.
    """
    statuses = ", ".join(f'"{s}"' for s in ACTIVE_STATUSES)
    # Match standard assignee OR the multi-user "Assignees" field (tôi nằm trong đó).
    jql = f"(assignee = currentUser(){_assignees_jql_clause()}) AND status in ({statuses})"
    if extra_jql:
        jql += f" AND ({extra_jql})"
    jql += " ORDER BY updated DESC"
    result = jira_search(jql, limit=limit)
    if isinstance(result, dict) and "issues" in result:
        scope = "assignee=me" + (f" hoặc {ASSIGNEES_FIELD} có me" if ASSIGNEES_FIELD else "")
        result["filter"] = f"{scope}, status in {ACTIVE_STATUSES}"
    return result


@tool_safe
def jira_get_fields() -> dict:
    """List Jira field metadata to resolve custom field IDs (read-only).

    Run once per instance during setup to discover IDs for Sprint, Epic Link,
    Story Points, etc. (these differ per Jira instance).
    """
    data = get_json("/rest/api/2/field")
    return {
        "count": len(data),
        "fields": [
            {"id": fld.get("id"), "name": fld.get("name"), "custom": fld.get("custom", False)}
            for fld in data
        ],
    }


@tool_safe
def jira_get_ticket_bundle(key: str) -> dict:
    """One-call ticket context for analysis (read-only): the PRIMARY tool for /jira-dev.

    Returns the issue + subtasks + linked issues + recent comments in a single
    token-efficient payload, avoiding multiple round-trips.

    Args:
        key: Issue key, e.g. 'PROJ-123'.
    """
    issue = get_json(
        f"/rest/api/2/issue/{key}",
        params={"fields": DEFAULT_ISSUE_FIELDS},
    )
    f = issue.get("fields", {}) or {}
    bundle = trim_issue(issue)
    bundle["subtasks"] = subtasks_from_fields(f)
    bundle["links"] = links_from_fields(f)
    bundle["attachments"] = attachments_from_fields(f)

    # Comments require a separate endpoint; failure here shouldn't sink the bundle.
    try:
        cdata = get_json(f"/rest/api/2/issue/{key}/comment")
        comments = cdata.get("comments", []) or []
        bundle["comment_total"] = cdata.get("total", len(comments))
        bundle["comments"] = [
            {
                "author": (c.get("author") or {}).get("displayName"),
                "created": c.get("created"),
                "body": truncate(c.get("body")),
            }
            for c in comments[-10:]
        ]
    except Exception:  # noqa: BLE001 - comments are best-effort
        bundle["comment_total"] = 0
        bundle["comments"] = []

    return bundle


# Tools registered on the FastMCP instance by server.py.
TOOLS = [
    jira_my_tasks,
    jira_get_issue,
    jira_get_comments,
    jira_get_subtasks,
    jira_get_linked_issues,
    jira_search,
    jira_get_fields,
    jira_get_ticket_bundle,
]


def register(mcp) -> None:
    """Register all Jira tools on the given FastMCP instance."""
    for fn in TOOLS:
        mcp.tool()(fn)

"""Jira Server/DC REST v2 read-only transport helpers.

All helpers here are READ-ONLY (HTTP GET). Errors are masked (via http_common)
so no auth header or token value can leak into tool output — the whole security
premise of this server. See config.jira_client for the authenticated client.
"""
import os

from config import jira_client
from http_common import build_tool_safe, get_with_retry, truncate  # re-exported for tools

# Decorator that masks any Jira tool failure into a safe error dict.
tool_safe = build_tool_safe("Jira")

# Token-efficient default field set for issue reads (avoid Jira's `*all`).
_BASE_ISSUE_FIELDS = (
    "summary,description,status,assignee,reporter,priority,labels,"
    "components,fixVersions,issuetype,parent,issuelinks,subtasks,attachment,created,updated"
)

# Extra custom fields to ALSO fetch + surface — e.g. Story Points, Sprint,
# Acceptance Criteria. Set ids via env JIRA_EXTRA_FIELDS="customfield_10001,customfield_10026"
# (discover ids with jira_get_fields). Surfaced under issue["extra"].
EXTRA_FIELDS = [f.strip() for f in os.getenv("JIRA_EXTRA_FIELDS", "").split(",") if f.strip()]
DEFAULT_ISSUE_FIELDS = _BASE_ISSUE_FIELDS + ("," + ",".join(EXTRA_FIELDS) if EXTRA_FIELDS else "")

# Description = the actual REQUIREMENT (often long tables of links/ACs) — don't lose it.
# Default rộng rãi (20k). Set JIRA_DESC_MAX=0 để KHÔNG giới hạn (full description).
DESC_MAX = int(os.getenv("JIRA_DESC_MAX", "20000"))


def attachments_from_fields(f: dict) -> list:
    """Extract attachment METADATA (no content) from an issue's `fields`.

    Lets the dev/skill see at a glance whether a task has images/mockups to
    analyze — download is a separate explicit tool.
    """
    out = []
    for a in f.get("attachment", []) or []:
        out.append({
            "id": a.get("id"),
            "filename": a.get("filename"),
            "mimeType": a.get("mimeType"),
            "size": a.get("size"),
            "is_image": str(a.get("mimeType") or "").startswith("image/"),
        })
    return out


def get_json(path: str, params: dict | None = None):
    """GET a Jira REST path and return parsed JSON. Raises on HTTP/transport error.

    Retries transient failures (timeout/429/5xx) — GET is idempotent so safe.
    """
    resp = get_with_retry(jira_client, path, params=params)
    resp.raise_for_status()
    return resp.json()


def get_response(url: str, follow_redirects: bool = False):
    """GET a (possibly absolute) URL and return the raw httpx Response.

    Used for binary downloads (attachments). Attachment content URLs may 302,
    so callers pass follow_redirects=True. Auth header is applied by the client.
    """
    resp = get_with_retry(jira_client, url, follow_redirects=follow_redirects)
    resp.raise_for_status()
    return resp


# --- shared shape helpers (DRY across tools) -------------------------------

def _name(obj):
    return obj.get("name") if isinstance(obj, dict) else obj


def _user(obj):
    if not isinstance(obj, dict):
        return None
    return obj.get("displayName") or obj.get("name")


def _simplify_value(v):
    """Flatten a custom-field value to something readable + token-efficient."""
    if isinstance(v, str):
        return truncate(v, 600)
    if isinstance(v, dict):
        return v.get("value") or v.get("name") or v
    if isinstance(v, list):
        return [_simplify_value(x) for x in v]
    return v


def trim_issue(issue: dict) -> dict:
    """Reduce a raw Jira issue to an essential, token-efficient shape."""
    f = issue.get("fields", {}) or {}
    out = {
        "key": issue.get("key"),
        "summary": f.get("summary"),
        "type": _name(f.get("issuetype")),
        "status": _name(f.get("status")),
        "priority": _name(f.get("priority")),
        "assignee": _user(f.get("assignee")),
        "reporter": _user(f.get("reporter")),
        "labels": f.get("labels") or [],
        "components": [_name(c) for c in (f.get("components") or [])],
        "fixVersions": [_name(v) for v in (f.get("fixVersions") or [])],
        "parent": (f.get("parent") or {}).get("key"),
        "description": (truncate(f.get("description"), DESC_MAX) if DESC_MAX > 0 else f.get("description")),
        "created": f.get("created"),
        "updated": f.get("updated"),
    }
    # Surface any configured custom fields (Story Points, Sprint, Acceptance Criteria).
    if EXTRA_FIELDS:
        out["extra"] = {fld: _simplify_value(f.get(fld)) for fld in EXTRA_FIELDS}
    return out


def subtasks_from_fields(f: dict) -> list:
    """Extract a trimmed subtask list from an issue's `fields`."""
    out = []
    for s in f.get("subtasks", []) or []:
        sf = s.get("fields", {}) or {}
        out.append({
            "key": s.get("key"),
            "summary": sf.get("summary"),
            "status": _name(sf.get("status")),
        })
    return out


def links_from_fields(f: dict) -> list:
    """Extract a trimmed linked-issue list from an issue's `fields`."""
    out = []
    for link in f.get("issuelinks", []) or []:
        lt = link.get("type") or {}
        if link.get("outwardIssue"):
            other, rel, direction = link["outwardIssue"], lt.get("outward"), "outward"
        elif link.get("inwardIssue"):
            other, rel, direction = link["inwardIssue"], lt.get("inward"), "inward"
        else:
            continue
        of = other.get("fields", {}) or {}
        out.append({
            "relation": rel,
            "direction": direction,
            "key": other.get("key"),
            "summary": of.get("summary"),
            "status": _name(of.get("status")),
        })
    return out

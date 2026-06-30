"""GitLab (self-hosted) REST v4 read-only transport helpers.

READ-ONLY (HTTP GET) over the authenticated client in config.gitlab_client.
Errors are masked via http_common so the PAT never leaks into tool output.
GitLab config is optional: if absent, tools return a "not configured" message.
"""
import functools
import inspect
import urllib.parse

from config import gitlab_client
from http_common import build_tool_safe, get_with_retry, truncate  # re-exported for tools

_tool_safe = build_tool_safe("GitLab")

NOT_CONFIGURED = {
    "error": "GitLab not configured. Set GITLAB_URL and GITLAB_TOKEN env vars "
    "(PAT scopes: read_api, read_repository)."
}


def gitlab_tool(fn):
    """Decorator: short-circuit with NOT_CONFIGURED if GitLab is unset, else mask errors."""
    safe = _tool_safe(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if gitlab_client is None:
            return NOT_CONFIGURED
        return safe(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(fn)
    return wrapper


def encode_project(project) -> str:
    """Accept a numeric project ID or a 'group/sub/repo' path; URL-encode the path."""
    s = str(project).strip()
    if s.isdigit():
        return s
    return urllib.parse.quote(s, safe="")


def encode_path(file_path: str) -> str:
    """URL-encode a repo file path (slashes included) for the files API."""
    return urllib.parse.quote(str(file_path), safe="")


def get_json(path: str, params: dict | None = None):
    """GET a GitLab REST path and return parsed JSON. Raises on HTTP/transport error.

    Retries transient failures (timeout/429/5xx) — GET is idempotent so safe.
    """
    resp = get_with_retry(gitlab_client, path, params=params)
    resp.raise_for_status()
    return resp.json()


def get_paginated(path: str, params: dict | None = None, limit: int = 20) -> list:
    """GET a list endpoint, following pages until `limit` items or no more data."""
    params = dict(params or {})
    per_page = min(limit, 100)
    collected: list = []
    page = 1
    while len(collected) < limit:
        params.update({"per_page": min(per_page, limit - len(collected)), "page": page})
        batch = get_json(path, params=params)
        if not isinstance(batch, list) or not batch:
            break
        collected.extend(batch)
        if len(batch) < params["per_page"]:
            break
        page += 1
    return collected[:limit]


# --- shape helpers (token-efficient trims) ---------------------------------

def trim_mr(mr: dict) -> dict:
    return {
        "iid": mr.get("iid"),
        "title": mr.get("title"),
        "state": mr.get("state"),
        "source_branch": mr.get("source_branch"),
        "target_branch": mr.get("target_branch"),
        "author": (mr.get("author") or {}).get("name"),
        "web_url": mr.get("web_url"),
        "merged_at": mr.get("merged_at"),
        "updated_at": mr.get("updated_at"),
    }


def trim_commit(c: dict) -> dict:
    return {
        "id": c.get("short_id") or (c.get("id") or "")[:8],
        "title": c.get("title"),
        "author": c.get("author_name"),
        "created_at": c.get("created_at"),
        "web_url": c.get("web_url"),
    }


def trim_pipeline(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "status": p.get("status"),
        "ref": p.get("ref"),
        "sha": (p.get("sha") or "")[:8],
        "web_url": p.get("web_url"),
        "created_at": p.get("created_at"),
        "updated_at": p.get("updated_at"),
    }

"""GitLab read-only MCP tools (self-hosted, REST v4).

Each tool uses @gitlab_tool, which returns a friendly message if GitLab is not
configured and masks any error otherwise (no token leakage). Payloads trimmed.
"""
from gitlab_client import (
    encode_path,
    encode_project,
    get_json,
    get_paginated,
    gitlab_tool,
    trim_commit,
    trim_mr,
    trim_pipeline,
    truncate,
)

# Caps for diff output (token efficiency).
MAX_DIFF_FILES = 15
MAX_DIFF_CHARS = 800


@gitlab_tool
def gitlab_search_mrs(ticket_key: str, project: str | None = None, limit: int = 20) -> dict:
    """Find merge requests referencing a ticket key (read-only, heuristic).

    Searches MR title + description for the key. Linkage is a HEURISTIC — results
    are candidates, not guaranteed matches.

    Args:
        ticket_key: e.g. 'PROJ-123'.
        project: Optional numeric ID or 'group/repo' path to scope the search.
        limit: Max MRs to return.
    """
    if project:
        path = f"/projects/{encode_project(project)}/merge_requests"
        params = {"search": ticket_key, "state": "all", "order_by": "updated_at"}
    else:
        path = "/merge_requests"
        params = {"search": ticket_key, "scope": "all", "state": "all"}
    mrs = get_paginated(path, params=params, limit=limit)
    return {
        "ticket": ticket_key,
        "count": len(mrs),
        "note": "candidates by title/description match — verify before relying",
        "merge_requests": [trim_mr(m) for m in mrs],
    }


@gitlab_tool
def gitlab_get_mr(project: str, mr_iid: int) -> dict:
    """Get a single merge request (read-only)."""
    mr = get_json(f"/projects/{encode_project(project)}/merge_requests/{mr_iid}")
    out = trim_mr(mr)
    out["description"] = truncate(mr.get("description"))
    return out


@gitlab_tool
def gitlab_get_mr_commits(project: str, mr_iid: int, limit: int = 50) -> dict:
    """List commits in a merge request (read-only)."""
    commits = get_paginated(
        f"/projects/{encode_project(project)}/merge_requests/{mr_iid}/commits",
        limit=limit,
    )
    return {"mr_iid": mr_iid, "count": len(commits), "commits": [trim_commit(c) for c in commits]}


@gitlab_tool
def gitlab_get_commits(project: str, ref: str | None = None, limit: int = 20) -> dict:
    """List recent commits for a project branch/ref (read-only)."""
    params = {"ref_name": ref} if ref else {}
    commits = get_paginated(
        f"/projects/{encode_project(project)}/repository/commits", params=params, limit=limit
    )
    return {"ref": ref, "count": len(commits), "commits": [trim_commit(c) for c in commits]}


@gitlab_tool
def gitlab_get_commit_diff(project: str, sha: str) -> dict:
    """Get a commit's diff (read-only). Truncated for token efficiency.

    Args:
        project: numeric ID or 'group/repo' path.
        sha: commit SHA.
    """
    diffs = get_json(f"/projects/{encode_project(project)}/repository/commits/{sha}/diff")
    diffs = diffs if isinstance(diffs, list) else []
    shown = diffs[:MAX_DIFF_FILES]
    files = [
        {
            "old_path": d.get("old_path"),
            "new_path": d.get("new_path"),
            "new_file": d.get("new_file", False),
            "deleted_file": d.get("deleted_file", False),
            "renamed_file": d.get("renamed_file", False),
            "diff": truncate(d.get("diff"), MAX_DIFF_CHARS),
        }
        for d in shown
    ]
    return {
        "sha": sha,
        "files_changed": len(diffs),
        "files_shown": len(files),
        "omitted": max(0, len(diffs) - len(files)),
        "files": files,
    }


@gitlab_tool
def gitlab_get_pipeline_status(
    project: str, ref: str | None = None, mr_iid: int | None = None
) -> dict:
    """Get latest pipeline status for a branch/ref or a merge request (read-only).

    Provide either `ref` (branch) or `mr_iid`.
    """
    enc = encode_project(project)
    if mr_iid is not None:
        pipelines = get_paginated(
            f"/projects/{enc}/merge_requests/{mr_iid}/pipelines", limit=1
        )
        if not pipelines:
            return {"mr_iid": mr_iid, "status": None, "note": "no pipelines found"}
        return {"mr_iid": mr_iid, **trim_pipeline(pipelines[0])}
    # branch/ref path
    params = {"ref": ref} if ref else None
    pipeline = get_json(f"/projects/{enc}/pipelines/latest", params=params)
    return {"ref": ref, **trim_pipeline(pipeline)}


@gitlab_tool
def gitlab_search_code(query: str, project: str | None = None, limit: int = 20) -> dict:
    """Search code (blobs) across GitLab (read-only). Degrades gracefully.

    Use this only for repos NOT checked out locally; for local repos prefer
    Claude's native Grep/Glob. Requires Advanced Search on the instance.
    """
    if project:
        path = f"/projects/{encode_project(project)}/search"
    else:
        path = "/search"
    try:
        results = get_paginated(path, params={"scope": "blobs", "search": query}, limit=limit)
    except Exception:  # noqa: BLE001 - feature may be disabled (403/404)
        return {
            "query": query,
            "error": "code (blobs) search unavailable on this instance",
            "hint": "use local Grep/Glob, or enable Advanced Search in GitLab",
        }
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "path": r.get("path"),
                "project_id": r.get("project_id"),
                "ref": r.get("ref"),
                "startline": r.get("startline"),
                "snippet": truncate(r.get("data"), 400),
            }
            for r in results
        ],
    }


@gitlab_tool
def gitlab_get_file(project: str, file_path: str, ref: str = "main") -> dict:
    """Read a repo file's content (read-only). Truncated for token efficiency.

    Args:
        project: numeric ID or 'group/repo' path.
        file_path: path within the repo, e.g. 'src/utils/auth.js'.
        ref: branch/tag/SHA (default 'main').
    """
    import base64

    enc = encode_project(project)
    enc_file = encode_path(file_path)
    meta = get_json(f"/projects/{enc}/repository/files/{enc_file}", params={"ref": ref})
    content = meta.get("content")
    decoded = None
    if content and meta.get("encoding") == "base64":
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - binary/undecodable file
            decoded = None
    return {
        "path": meta.get("file_path", file_path),
        "ref": ref,
        "size": meta.get("size"),
        "content": truncate(decoded, 4000) if decoded is not None else "[binary or undecodable]",
    }


TOOLS = [
    gitlab_search_mrs,
    gitlab_get_mr,
    gitlab_get_mr_commits,
    gitlab_get_commits,
    gitlab_get_commit_diff,
    gitlab_get_pipeline_status,
    gitlab_search_code,
    gitlab_get_file,
]


def register(mcp) -> None:
    """Register all GitLab tools on the given FastMCP instance."""
    for fn in TOOLS:
        mcp.tool()(fn)

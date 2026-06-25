"""Jira attachment tools (read-only): list metadata + securely download files.

Why: tasks often carry the real spec in IMAGES (mockups/screenshots). The dev
needs those analyzed without leaking the token. These tools download via the
authenticated client server-side, then return a LOCAL FILE PATH that Claude can
read with vision (or hand to the ai-multimodal skill). The PAT is never exposed.
"""
import os
import tempfile

from jira_client import attachments_from_fields, get_json, get_response, tool_safe

# Where downloaded attachments land (local, per-issue). Override with env if needed.
_DOWNLOAD_ROOT = os.getenv(
    "JIRA_ATTACHMENT_DIR", os.path.join(tempfile.gettempdir(), "devflow-mcp-attachments")
)


def _find_attachment(key: str, attachment_id: str) -> dict | None:
    data = get_json(f"/rest/api/2/issue/{key}", params={"fields": "attachment"})
    for a in (data.get("fields", {}) or {}).get("attachment", []) or []:
        if str(a.get("id")) == str(attachment_id):
            return a
    return None


@tool_safe
def jira_get_attachments(key: str) -> dict:
    """List attachment metadata on a Jira issue (read-only, no download).

    Use this to see whether a task has images/mockups worth analyzing. Download
    a specific one with jira_download_attachment.
    """
    data = get_json(f"/rest/api/2/issue/{key}", params={"fields": "attachment"})
    items = attachments_from_fields(data.get("fields", {}) or {})
    return {
        "key": key,
        "count": len(items),
        "has_images": any(i["is_image"] for i in items),
        "attachments": items,
    }


@tool_safe
def jira_download_attachment(key: str, attachment_id: str) -> dict:
    """Download one Jira attachment to a LOCAL file and return its path (read-only).

    The download uses the server's authenticated client (token stays hidden).
    Claude can then read the returned `path` with vision, or pass it to the
    ai-multimodal skill, to analyze an image/mockup attached to the task.

    Args:
        key: Issue key, e.g. 'PROJ-123'.
        attachment_id: The attachment id (from jira_get_attachments).

    Returns:
        {path, filename, mimeType, size} — `path` is an absolute local file path.
    """
    att = _find_attachment(key, attachment_id)
    if not att:
        return {"error": f"Attachment {attachment_id} not found on {key}"}

    content_url = att.get("content")
    if not content_url:
        return {"error": "Attachment has no content URL"}

    resp = get_response(content_url, follow_redirects=True)

    safe_name = os.path.basename(att.get("filename") or f"attachment-{attachment_id}")
    dest_dir = os.path.join(_DOWNLOAD_ROOT, str(key))
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, safe_name)
    with open(path, "wb") as fh:
        fh.write(resp.content)

    return {
        "path": path,
        "filename": safe_name,
        "mimeType": att.get("mimeType"),
        "size": att.get("size"),
        "is_image": str(att.get("mimeType") or "").startswith("image/"),
        "hint": "read this path with vision, or use the ai-multimodal skill, to analyze it",
    }


TOOLS = [jira_get_attachments, jira_download_attachment]


def register(mcp) -> None:
    """Register Jira attachment tools on the given FastMCP instance."""
    for fn in TOOLS:
        mcp.tool()(fn)

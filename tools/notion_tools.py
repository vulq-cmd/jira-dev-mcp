"""Notion read-only tool — đọc content 1 page (spec/docs đính trong ticket).

OPTIONAL: self-disable nếu NOTION_TOKEN chưa set. Page phải được share cho
internal integration. Token giấu trong client (không lộ ra output).
"""
import functools
import inspect
import re

from config import notion_client
from http_common import build_tool_safe, truncate

_safe = build_tool_safe("Notion")
NOT_CONFIGURED = {
    "error": "Notion chưa cấu hình. Set NOTION_TOKEN (internal integration + share page cho nó)."
}


def notion_tool(fn):
    """Self-disable nếu Notion chưa config, else mask lỗi."""
    safe = _safe(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if notion_client is None:
            return NOT_CONFIGURED
        return safe(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(fn)
    return wrapper


def _page_id(s: str) -> str:
    """Lấy 32 hex cuối từ URL/id → format 8-4-4-4-12 (Notion chấp nhận)."""
    hexs = re.sub(r"[^0-9a-fA-F]", "", s or "")
    if len(hexs) < 32:
        return (s or "").strip()
    h = hexs[-32:]
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _rich(arr) -> str:
    return "".join(t.get("plain_text", "") for t in (arr or []))


def _block_text(b: dict, depth: int) -> str:
    t = b.get("type")
    data = b.get(t, {}) if t else {}
    pad = "  " * depth
    txt = _rich(data.get("rich_text"))
    if t in ("heading_1", "heading_2", "heading_3"):
        return f"\n{'#' * int(t[-1])} {txt}"
    if t == "bulleted_list_item":
        return f"{pad}- {txt}"
    if t == "numbered_list_item":
        return f"{pad}1. {txt}"
    if t == "to_do":
        return f"{pad}- [{'x' if data.get('checked') else ' '}] {txt}"
    if t == "code":
        return f"```\n{txt}\n```"
    if t == "child_page":
        return f"{pad}[page] {data.get('title', '')}"
    if t == "image":
        return f"{pad}[image]"
    return f"{pad}{txt}" if txt else ""


def _walk(block_id: str, depth: int, out: list, budget: list) -> None:
    if depth > 2 or budget[0] <= 0:
        return
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = notion_client.get(f"/blocks/{block_id}/children", params=params)
        resp.raise_for_status()
        data = resp.json()
        for b in data.get("results", []) or []:
            line = _block_text(b, depth)
            if line:
                out.append(line)
                budget[0] -= len(line)
            if b.get("has_children") and budget[0] > 0:
                _walk(b["id"], depth + 1, out, budget)
            if budget[0] <= 0:
                return
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")


@notion_tool
def notion_get_page(page: str) -> dict:
    """Đọc nội dung 1 Notion page (text, read-only). Nhận URL hoặc page id.

    Args:
        page: URL Notion (vd https://notion.so/Title-<id>) hoặc page id.

    Returns:
        {page_id, title, content} — content đã flatten + truncate.
    """
    pid = _page_id(page)
    title = None
    try:
        meta = notion_client.get(f"/pages/{pid}")
        meta.raise_for_status()
        for prop in (meta.json().get("properties", {}) or {}).values():
            if prop.get("type") == "title":
                title = _rich(prop.get("title"))
                break
    except Exception:  # noqa: BLE001 - title is best-effort
        pass
    out: list = []
    _walk(pid, 0, out, [12000])
    content = "\n".join(x for x in out if x)
    return {"page_id": pid, "title": title, "content": truncate(content, 8000)}


TOOLS = [notion_get_page]


def register(mcp) -> None:
    for fn in TOOLS:
        mcp.tool()(fn)

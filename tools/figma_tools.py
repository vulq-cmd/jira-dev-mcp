"""Figma read-only tool — render frame design ra PNG (local path) để xem bằng vision.

OPTIONAL: self-disable nếu FIGMA_TOKEN chưa set. Design là visual → render ảnh +
vision chuẩn hơn đọc JSON tree. Token giấu trong client.
"""
import functools
import inspect
import os
import re
import tempfile

import httpx

from config import figma_client
from http_common import build_tool_safe

_safe = build_tool_safe("Figma")
NOT_CONFIGURED = {"error": "Figma chưa cấu hình. Set FIGMA_TOKEN (personal access token)."}
_DL_ROOT = os.path.join(tempfile.gettempdir(), "devflow-mcp-figma")


def figma_tool(fn):
    safe = _safe(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if figma_client is None:
            return NOT_CONFIGURED
        return safe(*args, **kwargs)

    wrapper.__signature__ = inspect.signature(fn)
    return wrapper


def _parse(url_or_key: str):
    """Tách file_key + node ids từ URL figma.com/(file|design)/<key>/...?node-id=1-23."""
    key = url_or_key.strip()
    m = re.search(r"figma\.com/(?:file|design|board)/([A-Za-z0-9]+)", url_or_key)
    if m:
        key = m.group(1)
    nodes = [n.replace("-", ":") for n in re.findall(r"node-id=([0-9]+[-:][0-9]+)", url_or_key)]
    return key, nodes


@figma_tool
def figma_get_frames(url_or_file_key: str, node_ids: str | None = None, scale: float = 1) -> dict:
    """Render frame Figma ra PNG (local path) để xem design bằng vision (read-only).

    Args:
        url_or_file_key: URL Figma (kèm ?node-id=) hoặc file key.
        node_ids: id node phẩy-phân-cách (vd '1:23,4:5'). Bỏ trống → lấy từ URL,
            không có nữa → trả danh sách frame cấp 1 để chọn.
        scale: tỉ lệ render (1-4).

    Returns:
        {file_key, frames:[{node, path}]} — đọc `path` bằng vision để xem design.
    """
    key, url_nodes = _parse(url_or_file_key)
    ids = [n.strip().replace("-", ":") for n in (node_ids or "").split(",") if n.strip()] or url_nodes

    if not ids:
        # Chưa biết frame nào → liệt kê frame cấp 1 để skill/dev chọn.
        f = figma_client.get(f"/files/{key}", params={"depth": 1})
        f.raise_for_status()
        frames = []
        for canvas in (f.json().get("document", {}) or {}).get("children", []) or []:
            for ch in canvas.get("children", []) or []:
                frames.append({"id": ch.get("id"), "name": ch.get("name")})
        return {"file_key": key, "need_node_id": True, "frames": frames[:50]}

    r = figma_client.get(
        f"/images/{key}", params={"ids": ",".join(ids), "format": "png", "scale": scale}
    )
    r.raise_for_status()
    images = r.json().get("images", {}) or {}
    os.makedirs(os.path.join(_DL_ROOT, key), exist_ok=True)
    out = []
    for node, img_url in images.items():
        if not img_url:
            out.append({"node": node, "error": "render failed"})
            continue
        dl = httpx.get(img_url, timeout=60, follow_redirects=True)  # S3 url, no auth
        dl.raise_for_status()
        path = os.path.join(_DL_ROOT, key, f"{node.replace(':', '-')}.png")
        with open(path, "wb") as fh:
            fh.write(dl.content)
        out.append({"node": node, "path": path})
    return {
        "file_key": key,
        "frames": out,
        "hint": "đọc `path` bằng vision (hoặc ai-multimodal skill) để xem design",
    }


TOOLS = [figma_get_frames]


def register(mcp) -> None:
    for fn in TOOLS:
        mcp.tool()(fn)

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
from http_common import build_tool_safe, get_with_retry
from tools.figma_specs import walk_specs

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
def figma_get_frames(
    url_or_file_key: str, node_ids: str | None = None, scale: float = 2, refresh: bool = False
) -> dict:
    """Render frame Figma ra PNG (local path) để xem design bằng vision (read-only).

    Gọi /files + /images qua retry (tự thử lại khi Figma 429/timeout) và CACHE PNG
    theo (node, scale) trên đĩa → lần sau không render lại, đỡ rate-limit.

    Args:
        url_or_file_key: URL Figma (kèm ?node-id=) hoặc file key.
        node_ids: id node phẩy-phân-cách (vd '1:23,4:5'). Bỏ trống → lấy từ URL,
            không có nữa → trả danh sách frame cấp 1 để chọn.
        scale: tỉ lệ render 1-4 (mặc định 2 cho rõ chữ/spec; tăng để xem chi tiết hơn).
        refresh: True = bỏ qua cache, render lại (dùng khi design Figma đã đổi).

    Returns:
        {file_key, scale, frames:[{node, path, cached?}]} — đọc `path` bằng vision.
    """
    key, url_nodes = _parse(url_or_file_key)
    ids = [n.strip().replace("-", ":") for n in (node_ids or "").split(",") if n.strip()] or url_nodes
    scale = max(1.0, min(float(scale), 4.0))

    if not ids:
        # Chưa biết frame nào → liệt kê frame cấp 1 để skill/dev chọn.
        f = get_with_retry(figma_client, f"/files/{key}", params={"depth": 1})
        f.raise_for_status()
        frames = []
        for canvas in (f.json().get("document", {}) or {}).get("children", []) or []:
            for ch in canvas.get("children", []) or []:
                frames.append({"id": ch.get("id"), "name": ch.get("name")})
        return {"file_key": key, "need_node_id": True, "frames": frames[:50]}

    out_dir = os.path.join(_DL_ROOT, key)
    os.makedirs(out_dir, exist_ok=True)

    def _cache_path(node: str) -> str:
        return os.path.join(out_dir, f"{node.replace(':', '-')}-s{scale:g}.png")

    # Q3 cache: bỏ qua node đã render ở scale này (trừ khi refresh) → ít gọi Figma hơn.
    results: dict = {}
    todo: list = []
    for node in ids:
        p = _cache_path(node)
        if not refresh and os.path.exists(p) and os.path.getsize(p) > 0:
            results[node] = {"node": node, "path": p, "cached": True}
        else:
            todo.append(node)

    if todo:
        r = get_with_retry(
            figma_client,
            f"/images/{key}",
            params={"ids": ",".join(todo), "format": "png", "scale": scale},
        )
        r.raise_for_status()
        body = r.json()
        images = body.get("images", {}) or {}
        api_err = body.get("err")  # Figma trả lý do thật khi render fail → surface, đừng nuốt
        with httpx.Client(timeout=60, follow_redirects=True) as dlc:
            for node in todo:
                img_url = images.get(node)
                if not img_url:
                    results[node] = {
                        "node": node,
                        "error": api_err or "Figma không render được node này (sai node-id?)",
                    }
                    continue
                dl = get_with_retry(dlc, img_url)  # S3 url, no auth
                dl.raise_for_status()
                p = _cache_path(node)
                with open(p, "wb") as fh:
                    fh.write(dl.content)
                results[node] = {"node": node, "path": p}

    return {
        "file_key": key,
        "scale": scale,
        "frames": [results[n] for n in ids if n in results],
        "hint": "đọc `path` bằng vision để xem design; cache theo (node,scale) — refresh=True nếu Figma đã đổi",
    }


@figma_tool
def figma_get_specs(url_or_file_key: str, node_ids: str | None = None, depth: int = 3) -> dict:
    """Trích SPEC CHÍNH XÁC từ Figma node tree: size px, màu hex, text, font (read-only).

    Bổ trợ cho figma_get_frames (ảnh để NHÌN) — tool này cho GIÁ TRỊ ĐÚNG để code
    pixel-perfect (màu/kích thước/chữ chính xác, không phải đoán qua ảnh). Cần node-id.

    Args:
        url_or_file_key: URL Figma (kèm ?node-id=) hoặc file key.
        node_ids: id node phẩy-phân-cách (vd '1:23,4:5'). Bỏ trống → lấy từ URL.
        depth: độ sâu cây con để trích (0-6, mặc định 3).

    Returns:
        {file_key, nodes:{<id>:{name, type, specs:[...]}}} — px/hex/text là giá trị thật.
    """
    key, url_nodes = _parse(url_or_file_key)
    ids = [n.strip().replace("-", ":") for n in (node_ids or "").split(",") if n.strip()] or url_nodes
    if not ids:
        return {
            "file_key": key,
            "need_node_id": True,
            "hint": "truyền node_ids hoặc URL có ?node-id= (figma_get_frames không id sẽ list frame)",
        }
    r = get_with_retry(figma_client, f"/files/{key}/nodes", params={"ids": ",".join(ids)})
    r.raise_for_status()
    nodes = r.json().get("nodes", {}) or {}
    max_depth = max(0, min(int(depth), 6))
    out = {}
    for nid in ids:
        doc = (nodes.get(nid) or {}).get("document")
        if not doc:
            out[nid] = {"error": "node không tồn tại / không truy cập được"}
            continue
        out[nid] = {"name": doc.get("name"), "type": doc.get("type"),
                    "specs": walk_specs(doc, max_depth)}
    return {
        "file_key": key,
        "nodes": out,
        "hint": "px/hex/text là giá trị thật từ Figma; box.x/y = toạ độ tuyệt đối trên canvas",
    }


TOOLS = [figma_get_frames, figma_get_specs]


def register(mcp) -> None:
    for fn in TOOLS:
        mcp.tool()(fn)

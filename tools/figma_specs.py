"""Trích spec CHÍNH XÁC từ node tree Figma: size px, màu hex, text, font.

Pure helpers (no HTTP) — figma_tools.figma_get_specs gọi /files/:key/nodes rồi
walk tree qua đây. Tách riêng cho gọn (figma_tools chỉ lo wiring) + dễ test.
"""
from http_common import truncate

# Token guard: tối đa số node trích cho mỗi frame (cây sâu có thể cả nghìn node).
_NODE_CAP = 120


def hex_color(color) -> str | None:
    """rgba float (0-1) → '#RRGGBB' (kèm alpha nếu < 1). None nếu không hợp lệ."""
    if not isinstance(color, dict):
        return None
    r = round(color.get("r", 0) * 255)
    g = round(color.get("g", 0) * 255)
    b = round(color.get("b", 0) * 255)
    a = color.get("a", 1)
    h = f"#{r:02X}{g:02X}{b:02X}"
    return h if a is None or a >= 0.999 else f"{h} ({a:.2f}a)"


def _solid_hex(paints) -> str | None:
    """Màu của paint SOLID nhìn-thấy đầu tiên (fills/strokes)."""
    for p in paints or []:
        if p.get("visible", True) and p.get("type") == "SOLID":
            return hex_color(p.get("color"))
    return None


def node_spec(node: dict) -> dict:
    """1 node → spec gọn: name/type/box + fill/border/radius/opacity, +text/font nếu TEXT."""
    spec = {"name": node.get("name"), "type": node.get("type")}
    bb = node.get("absoluteBoundingBox") or {}
    box = {k: round(bb[k]) for k in ("x", "y", "width", "height") if bb.get(k) is not None}
    if box:
        spec["box"] = box
    fill = _solid_hex(node.get("fills"))
    if fill:
        spec["fill"] = fill
    if node.get("cornerRadius"):
        spec["radius"] = node["cornerRadius"]
    sw = node.get("strokeWeight")
    if sw:
        stroke = _solid_hex(node.get("strokes"))
        spec["border"] = f"{sw}px {stroke}" if stroke else f"{sw}px"
    opacity = node.get("opacity")
    if opacity is not None and opacity < 1:
        spec["opacity"] = round(opacity, 2)
    if node.get("type") == "TEXT":
        spec["text"] = truncate(node.get("characters"), 200)
        st = node.get("style") or {}
        font = {
            k: st[k]
            for k in ("fontFamily", "fontSize", "fontWeight", "lineHeightPx",
                      "letterSpacing", "textAlignHorizontal")
            if st.get(k) is not None
        }
        if font:
            spec["font"] = font
    return spec


def walk_specs(node: dict, max_depth: int, cap: int = _NODE_CAP) -> list:
    """DFS node tree → list spec, giới hạn depth + cap node (token-efficient)."""
    out: list = []

    def _rec(n: dict, depth: int) -> None:
        if len(out) >= cap:
            return
        out.append(node_spec(n))
        if depth < max_depth:
            for ch in n.get("children") or []:
                if len(out) >= cap:
                    break
                _rec(ch, depth + 1)

    _rec(node, 0)
    if len(out) >= cap:
        out.append({"_note": f"đã cắt ở {cap} node — giảm phạm vi/độ sâu nếu cần thêm"})
    return out

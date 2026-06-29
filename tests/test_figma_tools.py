"""Tests for Figma render tool: URL parse, render→download, list frames, mask."""
import os

import httpx
import respx

import tools.figma_tools as ft

FAPI = "https://api.figma.com/v1"
SECRET = os.environ["FIGMA_TOKEN"]


def test_parse_url_node():
    key, nodes = ft._parse("https://figma.com/design/ABC123/Banner?node-id=12-34")
    assert key == "ABC123" and nodes == ["12:34"]


def test_render_frame_downloads_png():
    url = "https://figma.com/design/ABC123/Banner?node-id=12-34"
    img = "https://s3.figma.com/img/xyz.png"
    with respx.mock() as mock:
        mock.get(f"{FAPI}/images/ABC123").mock(
            return_value=httpx.Response(200, json={"images": {"12:34": img}})
        )
        mock.get(img).mock(return_value=httpx.Response(200, content=b"\x89PNGfake"))
        out = ft.figma_get_frames(url)
    fr = out["frames"][0]
    assert out["file_key"] == "ABC123"
    assert fr["node"] == "12:34"
    assert os.path.isfile(fr["path"])
    with open(fr["path"], "rb") as fh:
        assert fh.read() == b"\x89PNGfake"
    os.remove(fr["path"])


def test_lists_frames_when_no_node():
    doc = {"document": {"children": [{"children": [{"id": "1:2", "name": "Frame A"}]}]}}
    with respx.mock() as mock:
        mock.get(f"{FAPI}/files/ABC123").mock(return_value=httpx.Response(200, json=doc))
        out = ft.figma_get_frames("ABC123")  # no node id anywhere
    assert out["need_node_id"] is True
    assert out["frames"][0]["name"] == "Frame A"


def test_error_masks_secret():
    with respx.mock() as mock:
        mock.get(f"{FAPI}/images/ABC123").mock(return_value=httpx.Response(403, text="no"))
        out = ft.figma_get_frames("ABC123", node_ids="12:34")
    assert "error" in out
    assert SECRET not in str(out)


def test_not_configured(monkeypatch):
    monkeypatch.setattr(ft, "figma_client", None)
    out = ft.figma_get_frames("ABC123", node_ids="1:2")
    assert out == ft.NOT_CONFIGURED

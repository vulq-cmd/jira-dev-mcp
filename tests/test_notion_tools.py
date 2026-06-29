"""Tests for Notion read tool: id parsing, block flatten, mask, not-configured."""
import os

import httpx
import respx

import tools.notion_tools as nt

BASE = "https://api.notion.com/v1"
SECRET = os.environ["NOTION_TOKEN"]
PID = "12345678-90ab-cdef-1234-567890abcdef"
URL = "https://notion.so/Banner-Spec-1234567890abcdef1234567890abcdef"

META = {"properties": {"Name": {"type": "title", "title": [{"plain_text": "Banner Spec"}]}}}
CHILDREN = {
    "results": [
        {"id": "b1", "type": "heading_2", "has_children": False,
         "heading_2": {"rich_text": [{"plain_text": "Mục tiêu"}]}},
        {"id": "b2", "type": "bulleted_list_item", "has_children": False,
         "bulleted_list_item": {"rich_text": [{"plain_text": "Banner cuối trang"}]}},
    ],
    "has_more": False,
    "next_cursor": None,
}


def test_get_page_flattens_blocks():
    with respx.mock(base_url=BASE) as mock:
        mock.get(f"/pages/{PID}").mock(return_value=httpx.Response(200, json=META))
        mock.get(f"/blocks/{PID}/children").mock(return_value=httpx.Response(200, json=CHILDREN))
        out = nt.notion_get_page(URL)
    assert out["page_id"] == PID
    assert out["title"] == "Banner Spec"
    assert "Mục tiêu" in out["content"] and "Banner cuối trang" in out["content"]
    assert SECRET not in str(out)


def test_error_masks_secret():
    with respx.mock(base_url=BASE) as mock:
        mock.get(f"/pages/{PID}").mock(return_value=httpx.Response(200, json=META))
        mock.get(f"/blocks/{PID}/children").mock(return_value=httpx.Response(500, text="boom"))
        out = nt.notion_get_page(URL)
    assert "error" in out
    assert SECRET not in str(out) and "Bearer" not in str(out)


def test_not_configured(monkeypatch):
    monkeypatch.setattr(nt, "notion_client", None)
    out = nt.notion_get_page(URL)
    assert out == nt.NOT_CONFIGURED
    assert SECRET not in str(out)

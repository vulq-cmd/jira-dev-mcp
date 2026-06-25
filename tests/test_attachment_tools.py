"""Tests for Jira attachment tools: metadata listing + secure local download."""
import os

import httpx
import respx

from tools import jira_attachment_tools as att

BASE = "https://jira.example.com"
SECRET = os.environ["JIRA_PAT"]

ATTACH_FIELD = {
    "key": "PROJ-123",
    "fields": {
        "attachment": [
            {
                "id": "10001",
                "filename": "mockup.png",
                "mimeType": "image/png",
                "size": 2048,
                "content": f"{BASE}/secure/attachment/10001/mockup.png",
            },
            {
                "id": "10002",
                "filename": "notes.txt",
                "mimeType": "text/plain",
                "size": 12,
                "content": f"{BASE}/secure/attachment/10002/notes.txt",
            },
        ]
    },
}


def test_list_attachments_flags_images():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=httpx.Response(200, json=ATTACH_FIELD)
        )
        out = att.jira_get_attachments("PROJ-123")
    assert out["count"] == 2
    assert out["has_images"] is True
    img = next(a for a in out["attachments"] if a["filename"] == "mockup.png")
    assert img["is_image"] is True


def test_download_writes_local_file():
    png_bytes = b"\x89PNG\r\n\x1a\nFAKEIMAGE"
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=httpx.Response(200, json=ATTACH_FIELD)
        )
        mock.get("/secure/attachment/10001/mockup.png").mock(
            return_value=httpx.Response(200, content=png_bytes)
        )
        out = att.jira_download_attachment("PROJ-123", "10001")

    assert out["filename"] == "mockup.png"
    assert out["is_image"] is True
    assert os.path.isfile(out["path"])
    with open(out["path"], "rb") as fh:
        assert fh.read() == png_bytes
    # cleanup
    os.remove(out["path"])


def test_download_missing_attachment_is_clean():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=httpx.Response(200, json=ATTACH_FIELD)
        )
        out = att.jira_download_attachment("PROJ-123", "99999")
    assert "not found" in out["error"]
    assert SECRET not in str(out)

"""Safety tests for Jira write tools: allowlist, no-delete, no silent POST, masking."""
import json as _json
import os

import httpx
import respx

from tools import jira_write_tools

BASE = "https://jira.example.com"
SECRET = os.environ["JIRA_PAT"]

TRANSITIONS = {
    "transitions": [
        {"id": "21", "name": "Start", "to": {"name": "Doing"}},
        {"id": "31", "name": "Ready for QA", "to": {"name": "Waiting To Test"}},
    ]
}


def test_transition_allowlisted_and_available_posts_correct_id():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(200, json=TRANSITIONS)
        )
        route = mock.post("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(204)
        )
        out = jira_write_tools.jira_transition_issue("PROJ-1", "Doing")
    assert out["ok"] is True and out["transitioned_to"] == "Doing"
    assert route.called
    body = _json.loads(route.calls[0].request.content)
    assert body["transition"]["id"] == "21"  # matched destination 'Doing'
    # GUARANTEE: body chỉ có transition.id — KHÔNG fields/update/assignee/bất kỳ thứ gì khác
    assert set(body.keys()) == {"transition"}
    assert set(body["transition"].keys()) == {"id"}
    assert "fields" not in body and "update" not in body
    assert "assignee" not in str(body).lower()


def test_transition_not_allowlisted_rejected_with_NO_http():
    with respx.mock(base_url=BASE, assert_all_called=False) as mock:
        gett = mock.get("/rest/api/2/issue/PROJ-1/transitions")
        post = mock.post("/rest/api/2/issue/PROJ-1/transitions")
        out = jira_write_tools.jira_transition_issue("PROJ-1", "Done")  # not allowlisted
    assert "allowlist" in out["error"]
    assert not gett.called and not post.called  # short-circuits BEFORE any request


def test_transition_not_available_in_workflow_no_post():
    only_doing = {"transitions": [{"id": "21", "name": "Start", "to": {"name": "Doing"}}]}
    with respx.mock(base_url=BASE, assert_all_called=False) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(200, json=only_doing)
        )
        post = mock.post("/rest/api/2/issue/PROJ-1/transitions")
        out = jira_write_tools.jira_transition_issue("PROJ-1", "Waiting To Test")  # allowed but not available
    assert "không cho chuyển" in out["error"]
    assert not post.called


def test_no_delete_or_edit_capability():
    # Write surface must be EXACTLY the 2 transition tools — nothing else.
    names = {f.__name__ for f in jira_write_tools.TOOLS}
    assert names == {"jira_get_transitions", "jira_transition_issue"}
    src = open(jira_write_tools.__file__, encoding="utf-8").read()
    # No HTTP DELETE / PUT anywhere.
    assert ".delete(" not in src and ".put(" not in src
    # The ONLY mutating endpoint is /transitions — never assignee/comment/field edit.
    assert "/assignee" not in src
    assert "/comment" not in src
    # POST body must NEVER carry a fields/update payload (= no field/assignee mutation).
    assert '"fields"' not in src and "'fields'" not in src
    assert '"update"' not in src and "'update'" not in src
    # Exactly ONE write call, and it targets the /transitions endpoint (status only).
    assert src.count(".post(") == 1
    assert "/transitions" in src


def test_transition_error_masks_secret():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(200, json=TRANSITIONS)
        )
        mock.post("/rest/api/2/issue/PROJ-1/transitions").mock(
            return_value=httpx.Response(500, text="boom")
        )
        out = jira_write_tools.jira_transition_issue("PROJ-1", "Doing")
    assert SECRET not in str(out) and "Bearer" not in str(out)
    assert "error" in out

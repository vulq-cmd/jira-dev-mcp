"""Jira WRITE tools — OPT-IN (JIRA_ENABLE_WRITE=true), deliberately NARROW.

The ONLY mutation allowed = move an issue to an ALLOWLISTED status via the
transitions API. There is **no delete, no field edit, no comment** — by design,
because the Jira Server PAT inherits the account's full permissions, so the tool
surface IS the security boundary. The /devflow skill calls these only AFTER an
explicit dev confirm (never silently).
"""
from config import JIRA_ALLOWED_TRANSITIONS, jira_client
from http_common import build_tool_safe
from jira_client import get_json

tool_safe = build_tool_safe("Jira")
_ALLOWED = {s.lower() for s in JIRA_ALLOWED_TRANSITIONS}


@tool_safe
def jira_get_transitions(key: str) -> dict:
    """List status transitions currently AVAILABLE for an issue (read-only).

    Lets the skill show what's possible before proposing a change.
    """
    data = get_json(f"/rest/api/2/issue/{key}/transitions")
    return {
        "key": key,
        "available": [
            {"to": (t.get("to") or {}).get("name"), "transition": t.get("name")}
            for t in data.get("transitions", []) or []
        ],
    }


@tool_safe
def jira_transition_issue(key: str, to_status: str) -> dict:
    """Move an issue to an ALLOWLISTED status — the ONLY write op (confirm-gated).

    Refuses any target not in JIRA_ALLOWED_TRANSITIONS (default: To Do / Doing /
    Waiting To Test). Never deletes or edits fields.

    Args:
        key: Issue key, e.g. 'PROJ-123'.
        to_status: Target status name (must be allowlisted).
    """
    target = (to_status or "").strip()
    if target.lower() not in _ALLOWED:
        return {
            "error": f"'{target}' không nằm trong allowlist transition (bị chặn)",
            "allowed": sorted(JIRA_ALLOWED_TRANSITIONS),
        }
    # Find the transition whose destination matches the requested status.
    data = get_json(f"/rest/api/2/issue/{key}/transitions")
    transitions = data.get("transitions", []) or []
    match = next(
        (t for t in transitions if ((t.get("to") or {}).get("name") or "").lower() == target.lower()),
        None,
    )
    if not match:
        return {
            "error": f"Workflow Jira không cho chuyển '{key}' sang '{target}' từ trạng thái hiện tại",
            "available": [(t.get("to") or {}).get("name") for t in transitions],
        }
    # The sole write call: POST a transition by id (Jira returns 204 No Content).
    resp = jira_client.post(
        f"/rest/api/2/issue/{key}/transitions", json={"transition": {"id": match["id"]}}
    )
    resp.raise_for_status()
    return {"key": key, "transitioned_to": target, "ok": True}


TOOLS = [jira_get_transitions, jira_transition_issue]


def register(mcp) -> None:
    """Register Jira write tools (only when JIRA_ENABLE_WRITE=true)."""
    for fn in TOOLS:
        mcp.tool()(fn)

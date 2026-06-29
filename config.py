"""Configuration + shared HTTP client for devflow-mcp.

SECURITY: Secrets (PAT/tokens) are read from environment variables ONLY.
They are never accepted as tool arguments and never returned in tool output.
See README.md / .env.example for setup.
"""
import os
import sys

import httpx

# Load .env from THIS package directory (not CWD) so creds are found regardless
# of where Claude Code launches the server from. Real env vars still win over .env.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:  # pragma: no cover - optional dependency
    pass


def _require(name: str) -> str:
    """Read a required env var or exit with a NON-SECRET error message."""
    val = os.getenv(name)
    if not val:
        # Never print the value of any secret here.
        sys.stderr.write(
            f"[devflow-mcp] Missing required environment variable: {name}\n"
            f"              Set it in your shell or .env (see .env.example).\n"
        )
        sys.exit(1)
    # Normalize URLs (strip trailing slash); leave secrets untouched.
    return val.rstrip("/") if name.endswith("URL") else val


JIRA_BASE_URL = _require("JIRA_BASE_URL")
JIRA_PAT = _require("JIRA_PAT")

# Optional: disable TLS verification for trusted internal self-signed certs.
# Default = verify (secure). Set JIRA_VERIFY_SSL=false ONLY when you trust the host.
JIRA_VERIFY_SSL = os.getenv("JIRA_VERIFY_SSL", "true").lower() not in ("false", "0", "no")
JIRA_HTTP_TIMEOUT = float(os.getenv("JIRA_HTTP_TIMEOUT", "30"))

# Long-lived client with auth baked into the default headers. The token lives
# only inside this client object, never in tool signatures or return values.
jira_client = httpx.Client(
    base_url=JIRA_BASE_URL,
    headers={
        "Authorization": f"Bearer {JIRA_PAT}",
        "Accept": "application/json",
    },
    timeout=JIRA_HTTP_TIMEOUT,
    verify=JIRA_VERIFY_SSL,
    limits=httpx.Limits(max_keepalive_connections=5),
)

# --- GitLab (self-hosted) — OPTIONAL ---------------------------------------
# If GITLAB_URL/GITLAB_TOKEN are unset, gitlab_client stays None and GitLab
# tools return a friendly "not configured" message (server still runs Jira-only).
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_VERIFY_SSL = os.getenv("GITLAB_VERIFY_SSL", "true").lower() not in ("false", "0", "no")

gitlab_client = None
if GITLAB_URL and GITLAB_TOKEN:
    gitlab_client = httpx.Client(
        # Self-hosted GitLab REST v4 lives under <host>/api/v4.
        base_url=GITLAB_URL.rstrip("/") + "/api/v4",
        headers={"PRIVATE-TOKEN": GITLAB_TOKEN, "Accept": "application/json"},
        timeout=JIRA_HTTP_TIMEOUT,
        verify=GITLAB_VERIFY_SSL,
        limits=httpx.Limits(max_keepalive_connections=5),
    )

# --- Jira WRITE (opt-in) — default OFF nên server vẫn read-only -------------
# Jira Server PAT kế thừa full quyền account (không có scope) → an toàn nằm ở
# tool surface: chỉ transition status, allowlist, KHÔNG delete/edit field.
JIRA_ENABLE_WRITE = os.getenv("JIRA_ENABLE_WRITE", "false").lower() in ("true", "1", "yes")
JIRA_ALLOWED_TRANSITIONS = [
    s.strip()
    for s in os.getenv("JIRA_ALLOWED_TRANSITIONS", "To Do,Doing,Waiting To Test").split(",")
    if s.strip()
]

# --- Notion (OPTIONAL) — đọc spec/docs đính trong ticket --------------------
# Tạo internal integration + share page → token. Tools self-disable nếu chưa set.
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
notion_client = None
if NOTION_TOKEN:
    notion_client = httpx.Client(
        base_url="https://api.notion.com/v1",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Accept": "application/json",
        },
        timeout=JIRA_HTTP_TIMEOUT,
        limits=httpx.Limits(max_keepalive_connections=5),
    )

# --- Figma (OPTIONAL) — render frame design ra ảnh để xem bằng vision -------
# /images render server-side, frame to ở scale cao có thể >30s → timeout rộng hơn.
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_HTTP_TIMEOUT = float(os.getenv("FIGMA_HTTP_TIMEOUT", "120"))
figma_client = None
if FIGMA_TOKEN:
    figma_client = httpx.Client(
        base_url="https://api.figma.com/v1",
        headers={"X-Figma-Token": FIGMA_TOKEN, "Accept": "application/json"},
        timeout=FIGMA_HTTP_TIMEOUT,
        limits=httpx.Limits(max_keepalive_connections=5),
    )

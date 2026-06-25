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

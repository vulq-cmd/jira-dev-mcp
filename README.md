# devflow-mcp

Local, **read-only** MCP server that securely serves **Jira (Server/Data Center)** data to Claude Code — **without ever exposing your PAT/token** to the model. (GitLab tools + the `/devflow` skill land in later phases; see the plan.)

> Plan: `plans/260625-1353-jira-ai-dev-mcp/`

## Why
The token lives only inside this server's HTTP client (read from an env var). Claude calls tools like `jira_get_ticket_bundle("PROJ-123")` and gets back trimmed JSON — it never sees the credential, and the credential is never a tool argument.

## Requirements
- Python ≥ 3.10
- A Jira **Server/DC** Personal Access Token (Bearer). Profile → Personal Access Tokens.

## Setup
```bash
cd devflow-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .            # or: pip install -e ".[dev]" for tests

cp .env.example .env        # then edit JIRA_BASE_URL + JIRA_PAT
```

`.env` (gitignored) for local runs:
```
JIRA_BASE_URL=https://jira.your-company.com
JIRA_PAT=xxxxxxxxxxxx
```

## Smoke test (MCP Inspector)
```bash
fastmcp dev server.py
# open the Inspector URL, call jira_get_ticket_bundle with a real issue key
```
First, call **`jira_get_fields`** once and note the custom field IDs for Sprint / Epic Link / Story Points — needed in later phases.

## Register in Claude Code
Add to your project `.mcp.json` (commit this — it has NO secrets, only `${VAR}` refs):
```json
{
  "mcpServers": {
    "devflow": {
      "command": "/ABS/PATH/devflow-mcp/.venv/bin/python",
      "args": ["/ABS/PATH/devflow-mcp/server.py"],
      "env": {
        "JIRA_BASE_URL": "${JIRA_BASE_URL}",
        "JIRA_PAT": "${JIRA_PAT}",
        "GITLAB_URL": "${GITLAB_URL}",
        "GITLAB_TOKEN": "${GITLAB_TOKEN}"
      }
    }
  }
}
```
Put the real values in your shell (`~/.zshrc`). GitLab is optional — omit it and GitLab tools self-disable:
```bash
export JIRA_BASE_URL="https://jira.your-company.com"
export JIRA_PAT="xxxxxxxxxxxx"
export GITLAB_URL="https://gitlab.your-company.com"   # self-hosted; /api/v4 appended automatically
export GITLAB_TOKEN="glpat-xxxxx"                       # scopes: read_api, read_repository
```
Restart Claude Code, then the tools appear.

## Tools (21, all read-only)
**Jira core**
| Tool | Purpose |
|------|---------|
| `jira_get_ticket_bundle(key)` | **primary**: issue + subtasks + links + comments + attachment metadata in one call |
| `jira_get_issue(key, fields?)` | single issue, trimmed |
| `jira_get_comments(key, limit?)` | recent comments |
| `jira_get_subtasks(key)` / `jira_get_linked_issues(key)` | subtasks / linked issues |
| `jira_search(jql, fields?, limit?)` | JQL search (paginated, capped) |
| `jira_get_fields()` | resolve custom field IDs (setup) |

**Jira agile** — `jira_get_epic`, `jira_get_epic_issues`, `jira_get_sprint`, `jira_get_sprint_issues`

**Jira attachments (image analysis)** — `jira_get_attachments(key)`, `jira_download_attachment(key, attachment_id)` → downloads to a local path (token hidden) so Claude can read mockups/screenshots with vision.

**GitLab** (self-hosted, optional) — `gitlab_search_mrs(ticket_key)`, `gitlab_get_mr`, `gitlab_get_mr_commits`, `gitlab_get_commits`, `gitlab_get_commit_diff`, `gitlab_get_pipeline_status`, `gitlab_search_code`, `gitlab_get_file`.

## Security notes
- Secrets are read from env only; never accepted as args, never returned, masked in errors.
- Read-only: no write/transition/comment endpoints are implemented.
- `JIRA_VERIFY_SSL=false` only for trusted internal self-signed certs.

## Troubleshooting
- **Exits "Missing required environment variable"** → set `JIRA_BASE_URL` / `JIRA_PAT`.
- **401/403** → check PAT validity + project permissions.
- **SSL error on internal host** → set `JIRA_VERIFY_SSL=false` (trusted hosts only).

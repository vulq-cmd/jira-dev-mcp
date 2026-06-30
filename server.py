"""devflow-mcp — local, read-only MCP server exposing Jira (Server/DC) data.

Secrets are read from environment variables only (see config.py / README.md).
Importing `config` validates the environment and builds the authenticated HTTP
client. Tools are registered at module level so the FastMCP CLI (which imports
the `mcp` object rather than running __main__) picks them up.

Run locally:  python server.py                      # stdio (default, Claude spawns it)
              DEVFLOW_TRANSPORT=http python server.py  # persistent HTTP on 127.0.0.1:8787
"""
import os

from fastmcp import FastMCP

import config  # noqa: F401 - import validates env + builds the HTTP client(s)
from tools import (
    diag_tools,
    figma_tools,
    gitlab_tools,
    jira_agile_tools,
    jira_attachment_tools,
    jira_tools,
    notion_tools,
)

mcp = FastMCP("devflow-mcp")

# Register read-only tools. GitLab/Notion/Figma tools self-disable if not configured.
jira_tools.register(mcp)
jira_agile_tools.register(mcp)
jira_attachment_tools.register(mcp)
gitlab_tools.register(mcp)
notion_tools.register(mcp)
figma_tools.register(mcp)
diag_tools.register(mcp)  # devflow_diag: báo code đang chạy có cũ không (no secret)

# Write tools ONLY when explicitly opted in (JIRA_ENABLE_WRITE=true). Default =
# read-only. The only write op is an allowlisted status transition (no delete).
if config.JIRA_ENABLE_WRITE:
    from tools import jira_write_tools

    jira_write_tools.register(mcp)


if __name__ == "__main__":
    # Default = stdio (Claude tự spawn, bulletproof). Opt-in HTTP cho vòng lặp dev
    # không-restart: chạy server nền cố định, sửa code chỉ cần restart tiến trình
    # nền (không phải restart Claude). Bật bằng DEVFLOW_TRANSPORT=http.
    if os.getenv("DEVFLOW_TRANSPORT", "stdio").lower() == "http":
        mcp.run(
            transport="http",
            host=os.getenv("DEVFLOW_HTTP_HOST", "127.0.0.1"),
            port=int(os.getenv("DEVFLOW_HTTP_PORT", "8787")),
        )
    else:
        mcp.run()

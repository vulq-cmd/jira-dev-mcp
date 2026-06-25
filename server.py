"""devflow-mcp — local, read-only MCP server exposing Jira (Server/DC) data.

Secrets are read from environment variables only (see config.py / README.md).
Importing `config` validates the environment and builds the authenticated HTTP
client. Tools are registered at module level so the FastMCP CLI (which imports
the `mcp` object rather than running __main__) picks them up.

Run locally:  python server.py        # stdio transport
"""
from fastmcp import FastMCP

import config  # noqa: F401 - import validates env + builds the HTTP client(s)
from tools import jira_agile_tools, jira_attachment_tools, jira_tools, gitlab_tools

mcp = FastMCP("devflow-mcp")

# Register read-only tools. GitLab tools self-disable if GitLab is not configured.
jira_tools.register(mcp)
jira_agile_tools.register(mcp)
jira_attachment_tools.register(mcp)
gitlab_tools.register(mcp)


if __name__ == "__main__":
    mcp.run()

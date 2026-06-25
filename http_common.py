"""Shared HTTP helpers used by both the Jira and GitLab clients.

Centralizes the security-critical bits — text truncation and error masking —
so every service masks errors identically and no auth token can ever leak into
tool output.
"""
import functools
import inspect

import httpx

# Hard cap on free-text fields returned to Claude (token efficiency).
MAX_TEXT = 1500


def truncate(text, limit: int = MAX_TEXT):
    """Truncate long text, noting how much was dropped. Safe on None."""
    if not text:
        return text
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def mask_error(exc: Exception, service: str = "API") -> dict:
    """Convert an exception into a safe error dict that never leaks secrets.

    We avoid str(exc) for status errors (it can include the request URL) and
    never touch request headers (where the token lives).
    """
    if isinstance(exc, httpx.HTTPStatusError):
        return {
            "error": f"{service} API returned HTTP {exc.response.status_code}",
            "detail": truncate(exc.response.text, 300),
        }
    if isinstance(exc, httpx.TimeoutException):
        return {"error": f"{service} API request timed out"}
    if isinstance(exc, httpx.RequestError):
        return {"error": f"Network error contacting {service}: {type(exc).__name__}"}
    return {"error": f"Unexpected error: {type(exc).__name__}"}


def build_tool_safe(service: str):
    """Build a decorator that masks ANY failure into a safe error dict.

    Preserves the wrapped function's signature/docstring so FastMCP can still
    build the correct tool schema.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - intentional catch-all masking
                return mask_error(exc, service)

        wrapper.__signature__ = inspect.signature(fn)
        return wrapper

    return decorator

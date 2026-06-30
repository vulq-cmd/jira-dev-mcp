"""Shared HTTP helpers used by every service client (Jira, GitLab, Notion, Figma).

Centralizes the security-critical bits — text truncation and error masking — so
every service masks errors identically and no auth token can ever leak into tool
output. Also provides a transient-only retry for idempotent GETs.
"""
import functools
import inspect
import os
import time

import httpx

# Hard cap on free-text fields returned to Claude (token efficiency).
MAX_TEXT = 1500

# --- transient-retry config (idempotent GET only) --------------------------
# Total attempts = 1 + RETRIES. Tunable via env; tests set RETRIES=0 for speed.
RETRIES = int(os.getenv("DEVFLOW_HTTP_RETRIES", "2"))
BACKOFF = float(os.getenv("DEVFLOW_HTTP_BACKOFF", "0.5"))
# Statuses worth retrying: rate-limit + transient server errors.
_RETRY_STATUSES = {429, 500, 502, 503, 504}


def truncate(text, limit: int = MAX_TEXT):
    """Truncate long text, noting how much was dropped. Safe on None."""
    if not text:
        return text
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


# Status code → (short cause, actionable fix). Generic; service nuance added below.
_STATUS_HINTS = {
    400: ("bad request", "kiểm tra tham số gửi lên (key/JQL/ids)"),
    401: ("unauthorized", "token sai/hết hạn — gen lại PAT rồi RESTART Claude"),
    403: ("forbidden", "token thiếu quyền tới resource này"),
    404: ("not found", "sai key/id hoặc resource không tồn tại"),
    409: ("conflict", "trạng thái resource không cho thao tác này"),
    429: ("rate limited", "bị giới hạn tần suất — chờ rồi thử lại"),
}


def _service_hint(service: str, code: int):
    """Service-specific, more actionable fix for the common confusing cases."""
    s = (service or "").lower()
    if code == 404 and s == "notion":
        return ("page chưa share cho integration — hoặc page ở workspace khác "
                "(guest content cần Notion OAuth MCP, không phải internal token)")
    if code in (401, 403) and s == "figma":
        return ("Figma token sai/thiếu quyền — gen lại ở Figma → Settings → "
                "Security → Personal access tokens (scope: File content read)")
    if code == 429 and s == "figma":
        return "Figma rate-limit — render ít frame/scale thấp hơn, server đã tự retry"
    if code == 401 and s == "jira":
        return "Jira PAT sai/hết hạn — gen lại rồi RESTART Claude"
    if code == 403 and s == "gitlab":
        return "GitLab token thiếu scope (cần read_api, read_repository)"
    return None


def _clean_detail(text, limit: int = 200):
    """Short body snippet for debugging — drop HTML error/login pages (just noise)."""
    if not text:
        return None
    t = str(text).strip()
    if not t:
        return None
    head = t[:200].lower()
    if t[:1] == "<" or "<html" in head or "<!doctype" in head:
        return None  # HTML login/error page — useless noise, skip it
    return truncate(t, limit)


def mask_error(exc: Exception, service: str = "API") -> dict:
    """Convert an exception into a safe error dict that never leaks secrets.

    Maps status → an actionable `fix` hint and flags `transient` (retryable)
    errors so callers/skill can react. Never touches request headers (the token)
    and drops HTML body noise.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        cause, fix = _STATUS_HINTS.get(code, (None, None))
        if code >= 500 and not cause:
            cause, fix = "server error", "lỗi tạm phía server — thử lại sau"
        fix = _service_hint(service, code) or fix
        out = {"error": f"{service} HTTP {code}" + (f" ({cause})" if cause else "")}
        if fix:
            out["fix"] = fix
        if code in _RETRY_STATUSES:
            out["transient"] = True
        # Body snippet only when plausibly useful (skip auth pages + HTML noise).
        if code not in (401, 403):
            detail = _clean_detail(exc.response.text)
            if detail:
                out["detail"] = detail
        return out
    if isinstance(exc, httpx.TimeoutException):
        return {
            "error": f"{service} request timed out",
            "fix": "mạng chậm hoặc payload lớn — thử lại / giảm phạm vi",
            "transient": True,
        }
    if isinstance(exc, httpx.RequestError):
        return {
            "error": f"Network error contacting {service}: {type(exc).__name__}",
            "fix": "kiểm tra kết nối/VPN tới host",
            "transient": True,
        }
    return {"error": f"Unexpected error: {type(exc).__name__}"}


def get_with_retry(client, url, *, params=None, follow_redirects=False,
                   retries=None, backoff=None):
    """GET with limited retry on TRANSIENT failures only (GET is idempotent → safe).

    Retries timeout / network errors / 429 / 5xx with linear backoff. NEVER retries
    other 4xx (auth/not-found — retrying won't help). Returns the httpx Response
    (caller still calls raise_for_status); re-raises the last transport error.
    """
    retries = RETRIES if retries is None else retries
    backoff = BACKOFF if backoff is None else backoff
    attempt = 0
    while True:
        try:
            resp = client.get(url, params=params, follow_redirects=follow_redirects)
        except httpx.TransportError:  # timeouts + network errors (TimeoutException ⊂ this)
            if attempt >= retries:
                raise
            attempt += 1
            if backoff:
                time.sleep(backoff * attempt)
            continue
        if resp.status_code in _RETRY_STATUSES and attempt < retries:
            attempt += 1
            if backoff:
                time.sleep(backoff * attempt)
            continue
        return resp


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

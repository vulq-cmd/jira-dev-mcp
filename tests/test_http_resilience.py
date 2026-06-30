"""Covers Q1 (mask_error → actionable fix/transient) and Q4 (transient-only retry).

These are the two reliability fixes: errors must carry a `fix` hint and a
`transient` flag, and idempotent GETs must retry transient failures only.
"""
import httpx
import respx

from http_common import get_with_retry, mask_error

BASE = "https://retry.example.com"


def _status_exc(code: int, text: str = "") -> httpx.HTTPStatusError:
    req = httpx.Request("GET", BASE + "/x")
    resp = httpx.Response(code, request=req, text=text)
    return httpx.HTTPStatusError("boom", request=req, response=resp)


# --- Q1: mask_error -------------------------------------------------------

def test_mask_error_maps_status_to_actionable_fix():
    out = mask_error(_status_exc(401, "Unauthorized"), "Jira")
    assert "401" in out["error"]
    assert "fix" in out  # tells the user what to actually do
    assert "transient" not in out  # auth is not retryable


def test_mask_error_flags_429_and_5xx_transient():
    assert mask_error(_status_exc(429), "Figma").get("transient") is True
    assert mask_error(_status_exc(503), "Jira").get("transient") is True


def test_mask_error_service_specific_hint():
    # Notion 404 = sharing/workspace issue, not "wrong id".
    assert "share" in mask_error(_status_exc(404), "Notion")["fix"].lower()
    # Figma 429 explains the rate-limit explicitly.
    assert "rate-limit" in mask_error(_status_exc(429), "Figma")["fix"].lower()


def test_mask_error_drops_html_noise_and_auth_body():
    # HTML login/error page body is noise → not surfaced.
    assert "detail" not in mask_error(_status_exc(500, "<html>login</html>"), "Jira")
    # Auth bodies never surfaced regardless of content.
    assert "detail" not in mask_error(_status_exc(403, "denied"), "Jira")
    # Useful plain-text body IS surfaced for non-auth errors.
    assert "detail" in mask_error(_status_exc(400, "field 'jql' invalid"), "Jira")


def test_mask_error_timeout_is_transient_with_fix():
    out = mask_error(httpx.TimeoutException("t"), "Figma")
    assert out.get("transient") is True and "fix" in out


# --- Q4: get_with_retry ---------------------------------------------------

def test_retries_transient_5xx_then_succeeds():
    with respx.mock(base_url=BASE) as mock:
        route = mock.get("/x").mock(side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ])
        with httpx.Client(base_url=BASE) as c:
            resp = get_with_retry(c, "/x", retries=2, backoff=0)
        assert resp.status_code == 200
        assert route.call_count == 3


def test_does_not_retry_4xx():
    with respx.mock(base_url=BASE) as mock:
        route = mock.get("/x").mock(return_value=httpx.Response(404))
        with httpx.Client(base_url=BASE) as c:
            resp = get_with_retry(c, "/x", retries=2, backoff=0)
        assert resp.status_code == 404
        assert route.call_count == 1  # retrying a 404 is pointless


def test_retries_timeout_then_reraises():
    with respx.mock(base_url=BASE) as mock:
        route = mock.get("/x").mock(side_effect=httpx.TimeoutException("t"))
        with httpx.Client(base_url=BASE) as c:
            try:
                get_with_retry(c, "/x", retries=2, backoff=0)
                assert False, "should have re-raised after exhausting retries"
            except httpx.TimeoutException:
                pass
        assert route.call_count == 3  # 1 initial + 2 retries

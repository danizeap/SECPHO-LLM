"""Integration tests for POST /api/report: the PII auth gate, the download, and error paths.

Boots the real app (ThreadingHTTPServer + Handler) on a random localhost port with a test
password configured, then drives it over HTTP. Run: python -m pytest tests/test_report_api.py
"""
import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

import pytest


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # keep the 303 (and its Set-Cookie) instead of following it


@pytest.fixture(scope="module")
def base_url():
    os.environ["SECPHO_APP_PASSWORD"] = "testpass"
    os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
    sys.path.insert(0, "backend_api")
    import mvp_web_app as app

    httpd = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()


def _post_json(url, path, data, cookie=None):
    headers = {"Content-Type": "application/json", "Origin": url}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url + path, data=json.dumps(data).encode(), method="POST", headers=headers)
    try:
        with urllib.request.build_opener(_NoRedirect).open(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def _login(url):
    body = urllib.parse.urlencode({"email": "t@t.com", "password": "testpass"}).encode()
    req = urllib.request.Request(url + "/login", data=body, method="POST", headers={"Origin": url})
    try:
        with urllib.request.build_opener(_NoRedirect).open(req) as r:
            sc = r.headers.get("Set-Cookie", "")
    except urllib.error.HTTPError as e:
        sc = e.headers.get("Set-Cookie", "")
    return sc.split(";")[0] if sc else ""


def test_report_endpoint_requires_auth(base_url):
    # The PII gate: an unauthenticated POST must be rejected before any document is generated.
    status, _, _ = _post_json(base_url, "/api/report", {"type": "person", "id": 74663})
    assert status == 401


def test_report_download_for_authenticated_staff(base_url):
    cookie = _login(base_url)
    assert cookie, "login did not set a session cookie"
    status, headers, data = _post_json(base_url, "/api/report", {"type": "person", "id": 74663}, cookie=cookie)
    assert status == 200
    assert "wordprocessingml" in headers.get("Content-Type", "")
    assert "attachment" in headers.get("Content-Disposition", "")
    assert data[:2] == b"PK"  # a .docx is a zip archive


def test_report_bad_type_is_rejected(base_url):
    cookie = _login(base_url)
    status, _, _ = _post_json(base_url, "/api/report", {"type": "bogus"}, cookie=cookie)
    assert status == 400

"""HTTP-level test of the /api/org/users endpoints (rbac-user-management, P4d) — hermetic. Starts the
real Handler on an ephemeral port and drives it over HTTP with app-signed session cookies. The Render
writer is disabled (no RENDER secrets) so create/delete run in-memory only; no network, no LLM.
Run: python -m pytest tests/test_org_users_endpoint.py
"""
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

os.environ.setdefault("SECPHO_APP_PASSWORD", "testpass")
os.environ.setdefault("SECPHO_SESSION_SECRET", "testsecret_integration_0123456789")
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)
os.environ.pop("RENDER_API_KEY", None)     # writer disabled -> in-memory only, no network
os.environ.pop("RENDER_SERVICE_ID", None)
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402

_HASH = app.hash_password("irrelevant-but-valid")


@pytest.fixture
def port(monkeypatch):
    monkeypatch.setattr(app, "ADMIN_ENABLED", True)
    monkeypatch.setattr(app, "AUTH_REQUIRED", True)
    monkeypatch.setattr(app, "USERS", {
        "sergio@secpho.org": {"role": "admin", "pw": _HASH, "grants": app.ALL_GRANTS},
        "u@secpho.org": {"role": "user", "pw": _HASH, "grants": app.DEFAULT_USER_GRANTS},
    })
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    httpd.RequestHandlerClass.log_message = lambda *a, **k: None  # quiet
    p = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield p
    httpd.shutdown()


def _req(method, p, path, cookie=None, body=None):
    url = f"http://127.0.0.1:{p}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Origin", f"http://127.0.0.1:{p}")
    if data is not None:
        r.add_header("Content-Type", "application/json")
    if cookie:
        r.add_header("Cookie", f"{app.SESSION_COOKIE_NAME}={cookie}")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return exc.code, {}


def _admin():
    return app.make_session_cookie("admin", "sergio@secpho.org")


def _user():
    return app.make_session_cookie("user", "u@secpho.org")


def test_get_requires_admin(port):
    assert _req("GET", port, "/api/org/users", cookie=_user())[0] == 403


def test_post_requires_admin(port):
    status, _ = _req("POST", port, "/api/org/users", cookie=_user(),
                     body={"action": "create", "email": "y@secpho.org", "role": "user", "grants": []})
    assert status == 403


def test_admin_lists_users_and_catalog(port):
    status, data = _req("GET", port, "/api/org/users", cookie=_admin())
    assert status == 200
    assert any(u["email"] == "sergio@secpho.org" for u in data["users"])
    assert {c["key"] for c in data["catalog"]} == set(app.ALL_GRANTS)
    assert all("pw" not in u for u in data["users"])           # never leak hashes


def test_admin_creates_user_in_memory(port):
    status, data = _req("POST", port, "/api/org/users", cookie=_admin(),
                        body={"action": "create", "email": "nuevo@secpho.org", "role": "user",
                              "grants": ["tool.chat", "data.eventos"]})
    assert status == 200 and data["ok"] and data.get("one_time_password")
    assert data["persisted"] is False                          # writer disabled -> in-memory
    _, listing = _req("GET", port, "/api/org/users", cookie=_admin())
    new = [u for u in listing["users"] if u["email"] == "nuevo@secpho.org"]
    assert new and set(new[0]["grants"]) == {"tool.chat", "data.eventos"}


def test_create_rejects_non_secpho_email(port):
    status, data = _req("POST", port, "/api/org/users", cookie=_admin(),
                        body={"action": "create", "email": "x@gmail.com", "role": "user", "grants": []})
    assert status == 400 and data["error"] == "email_must_be_secpho"


def test_admin_cannot_assign_dev(port):
    status, data = _req("POST", port, "/api/org/users", cookie=_admin(),
                        body={"action": "create", "email": "boss@secpho.org", "role": "dev", "grants": []})
    assert status == 403 and data["error"] == "dev_requires_dev"


def test_cannot_delete_last_admin(port):
    # u@ is a user; sergio@ is the only admin -> deleting sergio would lock out
    status, data = _req("POST", port, "/api/org/users", cookie=_admin(),
                        body={"action": "delete", "email": "sergio@secpho.org"})
    assert status == 403 and data["error"] == "would_lock_out"


def test_create_refused_when_authoritative_read_is_empty(port, monkeypatch):
    # Writer enabled but the fresh roster read comes back empty while we hold a populated roster ->
    # refuse rather than clobber every credential (the HIGH finding from the security review).
    import render_env
    monkeypatch.setattr(render_env, "write_enabled", lambda: True)
    monkeypatch.setattr(render_env, "read_users_env", lambda *a, **k: "")   # recognized-empty
    status, data = _req("POST", port, "/api/org/users", cookie=_admin(),
                        body={"action": "create", "email": "nuevo@secpho.org", "role": "user", "grants": []})
    assert status == 409 and data["error"] == "roster_read_empty"


def test_agent_fallback_denies_ungranted_data(port, monkeypatch):
    # A tool.chat-only user (no data.socios) hitting the heuristic fallback (LLM unavailable) must be
    # refused, not served member rows / PII (the MEDIUM fail-open finding from the security review).
    monkeypatch.setitem(app.USERS, "limited@secpho.org",
                        {"role": "user", "pw": _HASH, "grants": frozenset({"tool.chat"})})
    cookie = app.make_session_cookie("user", "limited@secpho.org")
    status, data = _req("POST", port, "/api/agent", cookie=cookie, body={"message": "quien trabaja en ACME"})
    assert status == 200 and data.get("mode") == "restricted"
    assert "people" not in data and "@" not in json.dumps(data.get("answer", ""))

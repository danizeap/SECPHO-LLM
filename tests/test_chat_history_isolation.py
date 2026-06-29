"""Conversation-history per-user isolation (chat-history-isolation, #7) — hermetic. Covers the
server-side opaque per-user tag, its injection into the served chat page, and that two different
users get DIFFERENT tags (so the client-side purge isolates their localStorage history). The
client-side JS itself is syntax-guarded by test_inline_js_syntax.py. No network, no LLM.
Run: python -m pytest tests/test_chat_history_isolation.py
"""
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

os.environ.setdefault("SECPHO_APP_PASSWORD", "testpass")
os.environ.setdefault("SECPHO_SESSION_SECRET", "testsecret_integration_0123456789")
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402

_HASH = app.hash_password("irrelevant-but-valid")


# --------------------------------------------------------------------------- #
# _user_tag — opaque, stable, per-user
# --------------------------------------------------------------------------- #
def test_user_tag_stable_and_per_user():
    a1 = app._user_tag("alice@secpho.org")
    a2 = app._user_tag("ALICE@secpho.org")          # case-insensitive
    b = app._user_tag("bob@secpho.org")
    assert a1 == a2                                  # stable, normalized
    assert a1 != b                                   # different users -> different tags
    assert len(a1) == 16 and all(c in "0123456789abcdef" for c in a1)


def test_user_tag_opaque_and_anon():
    tag = app._user_tag("alice@secpho.org")
    assert "alice" not in tag and "@" not in tag     # never leaks the email
    assert app._user_tag("") == "anon" and app._user_tag("   ") == "anon"


def test_user_tag_keyed_by_session_secret(monkeypatch):
    base = app._user_tag("alice@secpho.org")
    monkeypatch.setattr(app, "SESSION_SECRET", app.SESSION_SECRET + "_rotated")
    assert app._user_tag("alice@secpho.org") != base  # not a bare hash of the email -> not enumerable


# --------------------------------------------------------------------------- #
# Page wiring — placeholder present in the template, replaced per request
# --------------------------------------------------------------------------- #
def test_chat_html_has_uid_placeholder_and_purge_logic():
    assert "{{UID}}" in app.CHAT_HTML
    assert 'name="secpho-uid"' in app.CHAT_HTML
    # the client purges (clears, not hides) on a different user before loading history
    assert "purgeIfDifferentUser" in app.CHAT_HTML
    assert "removeItem(CONV_KEY)" in app.CHAT_HTML and "UID_KEY" in app.CHAT_HTML


@pytest.fixture
def port(monkeypatch):
    monkeypatch.setattr(app, "ADMIN_ENABLED", True)
    monkeypatch.setattr(app, "AUTH_REQUIRED", True)
    monkeypatch.setattr(app, "USERS", {
        "alice@secpho.org": {"role": "user", "pw": _HASH, "grants": app.DEFAULT_USER_GRANTS},
        "bob@secpho.org": {"role": "user", "pw": _HASH, "grants": app.DEFAULT_USER_GRANTS},
    })
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    httpd.RequestHandlerClass.log_message = lambda *a, **k: None  # quiet
    p = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield p
    httpd.shutdown()


def _get_root(p, email, role="user"):
    cookie = app.make_session_cookie(role, email)
    r = urllib.request.Request(f"http://127.0.0.1:{p}/", method="GET")
    r.add_header("Cookie", f"{app.SESSION_COOKIE_NAME}={cookie}")
    with urllib.request.urlopen(r, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")


def test_served_page_injects_callers_tag_and_no_placeholder(port):
    status, body = _get_root(port, "alice@secpho.org")
    assert status == 200
    assert "{{UID}}" not in body                                  # placeholder was replaced
    assert app._user_tag("alice@secpho.org") in body              # caller's own tag is embedded
    assert app._user_tag("bob@secpho.org") not in body            # not someone else's


def test_two_users_get_different_served_tags(port):
    _, a = _get_root(port, "alice@secpho.org")
    _, b = _get_root(port, "bob@secpho.org")
    assert app._user_tag("alice@secpho.org") in a
    assert app._user_tag("bob@secpho.org") in b
    assert a != b                                                 # the pages differ by owner tag


# --------------------------------------------------------------------------- #
# _history_tag — stable per named account; per-login (unforgeable) otherwise
# (adversarial-review finding: a self-asserted email must NOT determine the tag
# in shared-password mode, or a user could forge a privileged user's namespace.)
# --------------------------------------------------------------------------- #
def test_history_tag_named_account_stable_and_nonce_independent(monkeypatch):
    monkeypatch.setattr(app, "USERS", {
        "alice@secpho.org": {"role": "user", "pw": _HASH, "grants": app.DEFAULT_USER_GRANTS}})
    s1 = {"sub": "alice@secpho.org", "role": "user", "nonce": "n1"}
    s2 = {"sub": "alice@secpho.org", "role": "user", "nonce": "n2"}   # a later login
    # roster-validated account -> stable per user (same user keeps their history), nonce ignored
    assert app._history_tag(s1) == app._history_tag(s2) == app._user_tag("alice@secpho.org")


def test_history_tag_shared_password_is_per_login_not_forgeable(monkeypatch):
    monkeypatch.setattr(app, "USERS", {})                            # shared-password mode
    # SAME self-asserted email, two different logins -> DIFFERENT tags (bound to the per-login nonce),
    # so a user cannot reuse a privileged user's typed email to land on their namespace.
    admin_login = {"sub": "boss@secpho.org", "role": "admin", "nonce": "nonceA"}
    user_login = {"sub": "boss@secpho.org", "role": "user", "nonce": "nonceB"}
    assert app._history_tag(admin_login) != app._history_tag(user_login)
    # the email alone no longer determines the tag (this was the pre-fix bug)
    assert app._history_tag(user_login) != app._user_tag("boss@secpho.org")


def test_history_tag_anon_without_nonce(monkeypatch):
    monkeypatch.setattr(app, "USERS", {})
    assert app._history_tag({"sub": "x@y.org", "role": "user"}) == "anon"  # no nonce -> anon
    assert app._history_tag(None) == "anon"


def test_save_active_has_multitab_guard():
    # INFO finding: a stale tab must not re-stamp its conversation under a new user's namespace.
    assert "Multi-tab guard" in app.CHAT_HTML
    assert "localStorage.getItem(UID_KEY) !== CONV_UID" in app.CHAT_HTML


@pytest.fixture
def shared_pw_port(monkeypatch):
    monkeypatch.setattr(app, "ADMIN_ENABLED", True)
    monkeypatch.setattr(app, "AUTH_REQUIRED", True)
    monkeypatch.setattr(app, "USERS", {})                            # shared-password mode
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    httpd.RequestHandlerClass.log_message = lambda *a, **k: None
    p = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield p
    httpd.shutdown()


def test_shared_password_same_email_two_logins_get_different_pages(shared_pw_port):
    # Two logins typing the SAME email (e.g. an admin-tier and a user-tier login) must receive
    # DIFFERENT served tags, so neither can inherit the other's history on a shared browser.
    _, a = _get_root(shared_pw_port, "boss@secpho.org", role="admin")
    _, b = _get_root(shared_pw_port, "boss@secpho.org", role="user")
    assert "{{UID}}" not in a and "{{UID}}" not in b
    assert a != b

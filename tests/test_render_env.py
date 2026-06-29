"""Render env-var writer (rbac-user-management, P4c) — hermetic. The single network choke point
(render_env._request) is monkeypatched, so nothing here touches the network.
Run: python -m pytest tests/test_render_env.py
"""
import sys
import urllib.error

sys.path.insert(0, "backend_api")
import render_env as rv  # noqa: E402


def _enable(monkeypatch):
    monkeypatch.setenv("RENDER_API_KEY", "rnd_testkey")
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-test123")


def test_write_disabled_without_secrets(monkeypatch):
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    assert rv.write_enabled() is False
    assert rv.update_users_env("x|user|h") == {"ok": False, "error": "render_writer_disabled"}
    assert rv.read_users_env() is None


def test_write_enabled_with_both_secrets(monkeypatch):
    _enable(monkeypatch)
    assert rv.write_enabled() is True


def test_update_users_env_happy_path(monkeypatch):
    _enable(monkeypatch)
    calls = []

    def fake_request(method, url, payload=None, timeout=15):
        calls.append((method, url, payload))
        if method == "PUT":
            return 200, {"key": "SECPHO_USERS", "value": payload["value"]}
        return 201, {"id": "dep-123"}        # POST /deploys

    monkeypatch.setattr(rv, "_request", fake_request)
    out = rv.update_users_env("a@secpho.org|user|hash|tool.chat")
    assert out["ok"] is True and out["deploy_triggered"] is True and out["deploy_id"] == "dep-123"
    put = calls[0]
    assert put[0] == "PUT" and put[1].endswith("/env-vars/SECPHO_USERS")
    assert put[2] == {"value": "a@secpho.org|user|hash|tool.chat"}
    assert calls[1][0] == "POST" and calls[1][1].endswith("/deploys")


def test_update_users_env_no_deploy(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, {"value": "v"}))
    out = rv.update_users_env("v", trigger_deploy=False)
    assert out["ok"] is True and out["deploy_triggered"] is False


def test_update_users_env_handles_api_error(monkeypatch):
    _enable(monkeypatch)

    def boom(method, url, payload=None, timeout=15):
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)

    monkeypatch.setattr(rv, "_request", boom)
    out = rv.update_users_env("v")
    assert out == {"ok": False, "error": "render_api_error", "status": 403}


def test_read_users_env_returns_value(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, {"value": "x@secpho.org|admin|h"}))
    assert rv.read_users_env() == "x@secpho.org|admin|h"


def test_read_users_env_404_is_empty(monkeypatch):
    _enable(monkeypatch)

    def not_found(method, url, payload=None, timeout=15):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(rv, "_request", not_found)
    assert rv.read_users_env() == ""


def test_read_users_env_unreachable_is_none(monkeypatch):
    _enable(monkeypatch)

    def down(method, url, payload=None, timeout=15):
        raise OSError("connection refused")

    monkeypatch.setattr(rv, "_request", down)
    assert rv.read_users_env() is None


def test_read_users_env_unrecognized_200_is_none(monkeypatch):
    # A 200 whose shape _extract_value does not recognize MUST fail closed (None), not "" — otherwise
    # the caller would treat it as an empty roster and clobber every credential on the next write.
    _enable(monkeypatch)
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, [{"key": "SECPHO_USERS", "value": "x"}]))
    assert rv.read_users_env() is None
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, {"unexpected": "shape"}))
    assert rv.read_users_env() is None


def test_read_users_env_envvar_wrapper_and_empty(monkeypatch):
    _enable(monkeypatch)
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, {"envVar": {"value": "a@secpho.org|admin|h"}}))
    assert rv.read_users_env() == "a@secpho.org|admin|h"
    monkeypatch.setattr(rv, "_request", lambda *a, **k: (200, {"value": ""}))   # recognized-empty
    assert rv.read_users_env() == ""

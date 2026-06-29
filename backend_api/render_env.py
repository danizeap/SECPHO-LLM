"""Zero-persistence user-store writer (rbac-user-management, P4c).

The staff roster lives in the Render service's ``SECPHO_USERS`` environment variable. This module is
the ONLY thing that mutates it, via the Render API, so admins/Eli (who have no Render dashboard) can
self-serve user creation. It adds NO new datastore — the env var stays the durable store.

Security:
- Flag-gated on ``RENDER_API_KEY`` + ``RENDER_SERVICE_ID``. If either is missing the writer is
  disabled and the roster is read-only (the UI says so).
- ``RENDER_API_KEY`` is privileged (it can reconfigure the service). It lives ONLY in the Render
  environment — never in the repo, never sent to the client or the LLM, never logged.
- It updates a SINGLE env var (``SECPHO_USERS``) so it cannot clobber other configuration.

Network calls go through ``_request``; tests monkeypatch that one function, so nothing here touches
the network under test.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

RENDER_API_BASE = "https://api.render.com/v1"
ENV_VAR_KEY = "SECPHO_USERS"


def _api_key() -> str:
    return (os.getenv("RENDER_API_KEY") or "").strip()


def _service_id() -> str:
    return (os.getenv("RENDER_SERVICE_ID") or "").strip()


def write_enabled() -> bool:
    """True only when both the privileged API key and the service id are configured."""
    return bool(_api_key() and _service_id())


def _request(method: str, url: str, payload: dict | None = None, timeout: int = 15):
    """Single network choke point (monkeypatched in tests). Returns (status_code, parsed_json|None).
    Raises urllib.error.HTTPError on non-2xx so callers can branch on .code."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_api_key()}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed api.render.com host)
        body = resp.read().decode("utf-8")
        return resp.status, (json.loads(body) if body else None)


def _extract_value(body):
    """Parse the env-var value from a RECOGNIZED Render GET shape. Returns the string value (possibly
    "" for a recognized-empty var), or None when the success payload shape is UNRECOGNIZED. Failing
    closed here is critical: an unparseable 200 must NOT be mistaken for an empty roster, or a
    subsequent write would clobber every credential."""
    if isinstance(body, dict):
        if "value" in body:
            return body.get("value") or ""
        inner = body.get("envVar")
        if isinstance(inner, dict) and "value" in inner:
            return inner.get("value") or ""
    return None


def read_users_env(timeout: int = 15) -> str | None:
    """Fetch the current ``SECPHO_USERS`` value from Render — a fresh read taken immediately before a
    write so concurrent edits last-writer-win on current data. Returns the string ("" for a
    recognized-empty var or a 404 not-set), or None when the writer is disabled, Render is
    unreachable, OR the 200 response shape is unrecognized (fail closed — the caller keeps its known
    roster rather than treating an unparseable read as empty)."""
    if not write_enabled():
        return None
    url = f"{RENDER_API_BASE}/services/{_service_id()}/env-vars/{ENV_VAR_KEY}"
    try:
        status, body = _request("GET", url, timeout=timeout)
    except urllib.error.HTTPError as exc:
        return "" if exc.code == 404 else None
    except Exception:
        return None
    return _extract_value(body) if status == 200 else None


def update_users_env(new_value: str, trigger_deploy: bool = True, timeout: int = 15) -> dict:
    """Set ``SECPHO_USERS`` to ``new_value`` on the Render service (single-var PUT) and, by default,
    trigger a redeploy so the new roster goes live (~1-2 min). Returns ``{"ok": bool, ...}``. Never
    logs the value (it carries password hashes)."""
    if not write_enabled():
        return {"ok": False, "error": "render_writer_disabled"}
    url = f"{RENDER_API_BASE}/services/{_service_id()}/env-vars/{ENV_VAR_KEY}"
    try:
        status, _ = _request("PUT", url, {"value": new_value}, timeout=timeout)
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": "render_api_error", "status": exc.code}
    except Exception as exc:
        return {"ok": False, "error": "render_unreachable", "detail": type(exc).__name__}
    if status not in (200, 201):
        return {"ok": False, "error": "render_api_status", "status": status}

    result = {"ok": True, "deploy_triggered": False}
    if trigger_deploy:
        try:
            d_status, d_body = _request(
                "POST", f"{RENDER_API_BASE}/services/{_service_id()}/deploys", {}, timeout=timeout
            )
            result["deploy_triggered"] = d_status in (200, 201, 202)
            if isinstance(d_body, dict):
                result["deploy_id"] = d_body.get("id")
        except Exception:
            result["deploy_triggered"] = False  # env-var change usually auto-deploys anyway
    return result

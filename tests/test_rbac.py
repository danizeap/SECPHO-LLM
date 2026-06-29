"""RBAC role + grant core (P4a, rbac-user-management) — hermetic. Exercises the pure role/grant
primitives via load_users()/grants_for()/resolve_grants()/role_at_least() with controlled env and a
monkeypatched USERS map, so it is independent of test import order. No network, no LLM.
Run: python -m pytest tests/test_rbac.py
"""
import os
import sys

os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)   # live off -> no refresher/network on import
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402

HASH = "pbkdf2_sha256$1$00$00"   # shape only; verify_password is not exercised here


# ---- grants_for ---------------------------------------------------------------------------------

def test_grants_for_admin_and_dev_get_everything():
    assert app.grants_for("admin", None) == app.ALL_GRANTS
    assert app.grants_for("dev", None) == app.ALL_GRANTS
    assert app.grants_for("admin", "tool.chat") == app.ALL_GRANTS   # stored field ignored (implicit *)


def test_grants_for_user_default_is_nonsensitive():
    g = app.grants_for("user", None)
    assert g == app.DEFAULT_USER_GRANTS
    assert app.SENSITIVE_GRANTS.isdisjoint(g)        # no financial/PII/scoring/feedback by default


def test_grants_for_user_explicit_set_is_exact():
    assert app.grants_for("user", "tool.chat,data.financiero") == frozenset({"tool.chat", "data.financiero"})


def test_grants_for_drops_unknown_keys_fail_closed():
    assert app.grants_for("user", "tool.chat,tool.NOPE,data.bogus") == frozenset({"tool.chat"})


# ---- load_users -----------------------------------------------------------------------------------

def test_load_users_parses_dev_role(monkeypatch):
    monkeypatch.setenv("SECPHO_USERS", f"dani@x.com|dev|{HASH}")
    users = app.load_users()
    assert users["dani@x.com"]["role"] == "dev"
    assert users["dani@x.com"]["grants"] == app.ALL_GRANTS


def test_load_users_legacy_3_field_gets_default_grants(monkeypatch):
    monkeypatch.setenv("SECPHO_USERS", f"u@secpho.org|user|{HASH}")
    assert app.load_users()["u@secpho.org"]["grants"] == app.DEFAULT_USER_GRANTS


def test_load_users_4_field_grants(monkeypatch):
    monkeypatch.setenv("SECPHO_USERS", f"u@secpho.org|user|{HASH}|tool.chat,data.financiero")
    assert app.load_users()["u@secpho.org"]["grants"] == frozenset({"tool.chat", "data.financiero"})


def test_load_users_rejects_bad_role(monkeypatch):
    monkeypatch.setenv("SECPHO_USERS", f"u@secpho.org|superuser|{HASH}")
    assert app.load_users() == {}


# ---- role_at_least --------------------------------------------------------------------------------

def test_role_precedence():
    dev, admin, user = {"role": "dev"}, {"role": "admin"}, {"role": "user"}
    assert app.role_at_least(dev, "admin") and app.role_at_least(dev, "dev")
    assert app.role_at_least(admin, "admin") and not app.role_at_least(admin, "dev")
    assert app.role_at_least(user, "user") and not app.role_at_least(user, "admin")
    assert not app.role_at_least(None, "user")                    # fail-closed
    assert app.role_at_least({"auth_disabled": True}, "user")     # open mode counts as user
    assert not app.role_at_least({"auth_disabled": True}, "admin")


# ---- resolve_grants -------------------------------------------------------------------------------

def test_resolve_grants_named_user_is_authoritative(monkeypatch):
    monkeypatch.setitem(app.USERS, "u@secpho.org",
                        {"role": "user", "pw": HASH, "grants": frozenset({"tool.chat"})})
    assert app.resolve_grants({"role": "user", "sub": "u@secpho.org"}) == frozenset({"tool.chat"})


def test_resolve_grants_shared_admin_gets_all():
    assert app.resolve_grants({"role": "admin", "sub": "shared"}) == app.ALL_GRANTS


def test_resolve_grants_open_mode_is_nonsensitive():
    assert app.resolve_grants({"auth_disabled": True}) == app.DEFAULT_USER_GRANTS


def test_resolve_grants_no_session_is_empty():
    assert app.resolve_grants(None) == frozenset()                # fail-closed


def test_role_revalidated_against_live_roster(monkeypatch):
    # A cookie minted with role=admin must NOT grant admin once the live roster demotes the account.
    monkeypatch.setitem(app.USERS, "mallory@secpho.org",
                        {"role": "user", "pw": HASH, "grants": app.DEFAULT_USER_GRANTS})
    stale = {"role": "admin", "sub": "mallory@secpho.org"}        # cookie still claims admin
    assert app.role_at_least(stale, "admin") is False            # re-derived from USERS -> user
    assert app.resolve_grants(stale) == app.DEFAULT_USER_GRANTS


def test_deleted_named_account_has_no_role(monkeypatch):
    # USERS is non-empty (named-account mode); the cookie's account is gone (deleted).
    monkeypatch.setitem(app.USERS, "real@secpho.org",
                        {"role": "admin", "pw": HASH, "grants": app.ALL_GRANTS})
    ghost = {"role": "admin", "sub": "ghost@secpho.org"}
    assert app.role_at_least(ghost, "user") is False             # account gone -> unprivileged
    assert app.resolve_grants(ghost) == frozenset()


# ---- cookie round-trip ----------------------------------------------------------------------------

def test_dev_role_survives_cookie_roundtrip():
    payload = app.parse_session_cookie(app.make_session_cookie("dev", "dani@x.com"))
    assert payload and payload["role"] == "dev" and payload["sub"] == "dani@x.com"


# ---- P4b: fail-closed tool enforcement ------------------------------------------------------------

def test_dispatch_tool_denies_without_grant():
    out = app.dispatch_tool("list_projects", {}, {"grants": frozenset()})
    assert out == {"error": "forbidden", "tool": "list_projects", "required_grant": "data.proyectos"}


def test_dispatch_tool_allows_with_grant():
    out = app.dispatch_tool("list_projects", {}, {"grants": frozenset({"data.proyectos"})})
    assert out.get("error") != "forbidden"        # executed (empty data -> {"projects": [], "total": 0})


def test_dispatch_tool_ungated_without_grants_key():
    out = app.dispatch_tool("list_projects", {}, {})   # internal/test caller, no "grants" -> not gated
    assert out.get("error") != "forbidden"


def test_dispatch_tool_matchmaking_grant_required():
    out = app.dispatch_tool("recommend_contacts", {"member_id": 1}, {"grants": frozenset({"data.socios"})})
    assert out["error"] == "forbidden" and out["required_grant"] == "tool.matchmaking"


def test_every_agent_tool_has_a_required_grant():
    names = {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    missing = names - set(app.TOOL_REQUIRED_GRANT)
    assert not missing, f"agent tools missing a grant mapping (would be ungated): {missing}"


def test_agent_chat_threads_grants_into_ctx(monkeypatch):
    captured = {}

    def fake_run_agent(input_items, ctx, max_steps=4):
        captured["ctx"] = dict(ctx)
        return "ok", "stub", []

    monkeypatch.setattr(app, "run_agent", fake_run_agent)
    app.agent_chat("hola", [], None, grants=frozenset({"tool.chat", "data.socios"}))
    assert captured["ctx"]["grants"] == frozenset({"tool.chat", "data.socios"})


# ---- P4d: roster (de)serialization, passwords, validation -----------------------------------------

def test_serialize_parse_roundtrip():
    users = {
        "dani@x.com": {"role": "dev", "pw": "H1", "grants": app.ALL_GRANTS},
        "sergio@secpho.org": {"role": "admin", "pw": "H2", "grants": app.ALL_GRANTS},
        "u@secpho.org": {"role": "user", "pw": "H3", "grants": frozenset({"tool.chat", "data.eventos"})},
    }
    back = app.parse_users_string(app.serialize_users(users))
    assert back["dani@x.com"]["role"] == "dev" and back["dani@x.com"]["grants"] == app.ALL_GRANTS
    assert back["sergio@secpho.org"]["grants"] == app.ALL_GRANTS
    assert back["u@secpho.org"]["grants"] == frozenset({"tool.chat", "data.eventos"})


def test_hash_password_roundtrip():
    h = app.hash_password("S3cret-value")
    assert h.startswith("pbkdf2_sha256$") and app.verify_password("S3cret-value", h)
    assert not app.verify_password("wrong", h)


def test_gen_password_strength():
    pw = app.gen_password(14)
    assert len(pw) == 14 and all(c in app._PW_ALPHABET for c in pw)


def test_valid_secpho_email():
    assert app.valid_secpho_email("Nombre.Apellido@secpho.org")
    assert not app.valid_secpho_email("x@gmail.com")
    assert not app.valid_secpho_email("x@secpho.org.evil.com")
    assert not app.valid_secpho_email("@secpho.org")
    assert not app.valid_secpho_email("")


# ---- P4d: authorization guard ---------------------------------------------------------------------

_ADMIN = app.ROLE_RANK["admin"]
_DEV = app.ROLE_RANK["dev"]


def _roster():
    return {
        "dani@x.com": {"role": "dev", "pw": "h", "grants": app.ALL_GRANTS},
        "sergio@secpho.org": {"role": "admin", "pw": "h", "grants": app.ALL_GRANTS},
        "u@secpho.org": {"role": "user", "pw": "h", "grants": app.DEFAULT_USER_GRANTS},
    }


def test_guard_requires_admin():
    assert app.org_user_guard(app.ROLE_RANK["user"], "create", "new@secpho.org", "user", _roster()) == "forbidden"


def test_guard_create_existing_and_new():
    assert app.org_user_guard(_ADMIN, "create", "u@secpho.org", "user", _roster()) == "already_exists"
    assert app.org_user_guard(_ADMIN, "create", "new@secpho.org", "user", _roster()) is None


def test_guard_update_missing():
    assert app.org_user_guard(_ADMIN, "update", "ghost@secpho.org", "user", _roster()) == "not_found"


def test_guard_admin_cannot_assign_or_touch_dev():
    assert app.org_user_guard(_ADMIN, "create", "new@secpho.org", "dev", _roster()) == "dev_requires_dev"
    assert app.org_user_guard(_ADMIN, "delete", "dani@x.com", None, _roster()) == "dev_requires_dev"


def test_guard_dev_can_assign_dev():
    assert app.org_user_guard(_DEV, "create", "new@secpho.org", "dev", _roster()) is None


def test_guard_lockout_last_privileged():
    solo = {"sergio@secpho.org": {"role": "admin", "pw": "h", "grants": app.ALL_GRANTS}}
    assert app.org_user_guard(_ADMIN, "delete", "sergio@secpho.org", None, solo) == "would_lock_out"
    assert app.org_user_guard(_ADMIN, "update", "sergio@secpho.org", "user", solo) == "would_lock_out"


def test_guard_delete_one_of_two_admins_ok():
    two = {
        "a@secpho.org": {"role": "admin", "pw": "h", "grants": app.ALL_GRANTS},
        "b@secpho.org": {"role": "admin", "pw": "h", "grants": app.ALL_GRANTS},
    }
    assert app.org_user_guard(_ADMIN, "delete", "a@secpho.org", None, two) is None


# ---- P4d: action applier --------------------------------------------------------------------------

def test_apply_create_mints_password_and_grants():
    users, otp = app.apply_org_user_action("create", "new@secpho.org", "user", ["tool.chat", "data.financiero"], {})
    rec = users["new@secpho.org"]
    assert otp and rec["role"] == "user" and app.verify_password(otp, rec["pw"])
    assert rec["grants"] == frozenset({"tool.chat", "data.financiero"})


def test_apply_update_changes_grants_keeps_pw():
    base = {"u@secpho.org": {"role": "user", "pw": "KEEP", "grants": app.DEFAULT_USER_GRANTS}}
    users, otp = app.apply_org_user_action("update", "u@secpho.org", "user", ["tool.chat"], base)
    assert otp is None and users["u@secpho.org"]["pw"] == "KEEP"
    assert users["u@secpho.org"]["grants"] == frozenset({"tool.chat"})


def test_apply_reset_password_rehashes_keeps_grants():
    base = {"u@secpho.org": {"role": "user", "pw": "OLD", "grants": app.DEFAULT_USER_GRANTS}}
    users, otp = app.apply_org_user_action("reset_password", "u@secpho.org", None, [], base)
    assert otp and users["u@secpho.org"]["pw"] != "OLD" and app.verify_password(otp, users["u@secpho.org"]["pw"])
    assert users["u@secpho.org"]["grants"] == app.DEFAULT_USER_GRANTS


def test_apply_delete_removes():
    base = {"u@secpho.org": {"role": "user", "pw": "h", "grants": app.DEFAULT_USER_GRANTS}}
    users, otp = app.apply_org_user_action("delete", "u@secpho.org", None, [], base)
    assert "u@secpho.org" not in users and otp is None

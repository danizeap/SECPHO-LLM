"""Health/churn engagement tools (P5h-a, health-churn-intelligence) — hermetic. Injects a synthetic
activity feed into DATA and pins today_utc so recency is deterministic. Checks the engagement signals
+ the data.socios gating. No network, no LLM.
Run: python -m pytest tests/test_health_churn.py
"""
import os
import sys

import pandas as pd

os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402


def _pin_today(monkeypatch):
    monkeypatch.setattr(app, "today_utc", lambda: pd.Timestamp("2026-06-29"))


def _acts():
    return pd.DataFrame([
        {"activity_id": "1", "socio": "ACME", "date": "01/06/2026", "type": "Reunión", "author": "A", "description": "x"},
        {"activity_id": "2", "socio": "ACME", "date": "15/05/2026", "type": "Evento", "author": "A", "description": "y"},
        {"activity_id": "3", "socio": "STALE", "date": "01/01/2025", "type": "Reunión", "author": "B", "description": "z"},
        {"activity_id": "4", "socio": "GONE", "date": "01/01/2024", "type": "Reunión", "author": "C", "description": "w"},
    ])


def test_socio_engagement_recency(monkeypatch):
    _pin_today(monkeypatch)
    eng = app._socio_engagement(_acts())
    by = {r["socio"]: r for _, r in eng.iterrows()}
    assert by["ACME"]["days_since_last"] == 28 and by["ACME"]["activities_total"] == 2
    assert by["ACME"]["activities_180d"] == 2 and by["ACME"]["last_activity"] == "01/06/2026"
    assert by["STALE"]["days_since_last"] >= 120 and by["GONE"]["days_since_last"] > by["STALE"]["days_since_last"]


def test_at_risk_socios_threshold_and_ranking(monkeypatch):
    _pin_today(monkeypatch)
    monkeypatch.setitem(app.DATA, "actividades", _acts())
    out = app.at_risk_socios(days=120)
    assert out["total"] == 2 and out["threshold_days"] == 120
    socios = [r["socio"] for r in out["socios"]]
    assert socios == ["GONE", "STALE"]              # stalest first
    assert "ACME" not in socios                      # active (28 days) excluded


def test_socio_health(monkeypatch):
    _pin_today(monkeypatch)
    monkeypatch.setitem(app.DATA, "actividades", _acts())
    acme = app.socio_health("ACME")
    assert acme["days_since_last"] == 28 and acme["going_quiet"] is False and acme["activities_total"] == 2
    assert app.socio_health("GONE")["going_quiet"] is True
    assert app.socio_health("ZZZ").get("found") is False


def test_health_overview_activity_feed_basis(monkeypatch):
    # No membership data injected -> activity-feed basis, and NO rate (avoids a misleading denominator).
    _pin_today(monkeypatch)
    monkeypatch.setitem(app.DATA, "actividades", _acts())
    monkeypatch.setitem(app.DATA, "cuotas", pd.DataFrame())
    out = app.health_overview()
    assert out["available"] is True and out["basis"] == "activity_feed"
    assert out["socios_with_activity"] == 3 and out["active_recently"] == 1 and out["going_quiet"] == 2
    assert "going_quiet_pct" not in out


def test_health_overview_membership_basis(monkeypatch):
    # With membership data -> grounded on ACTIVE members + a deterministic, correctly-denominated rate.
    _pin_today(monkeypatch)
    monkeypatch.setitem(app.DATA, "actividades", _acts())   # ACME recent(28d), STALE quiet, GONE quiet
    monkeypatch.setitem(app.DATA, "cuotas", pd.DataFrame([
        {"altabaja_id": "1", "socio": "ACME", "status": "activo"},
        {"altabaja_id": "2", "socio": "STALE", "status": "activo"},
        {"altabaja_id": "3", "socio": "GONE", "status": "baja"},
    ]))
    out = app.health_overview()
    assert out["basis"] == "active_members"
    assert out["active_members"] == 2 and out["active_recently"] == 1 and out["going_quiet"] == 1
    assert out["going_quiet_pct"] == 50.0                   # 1 of 2 active members going quiet


def test_prompt_forbids_deriving_figures():
    instr = app.AGENT_INSTRUCTIONS.lower()
    assert "derive" in instr and ("percentage" in instr or "rate" in instr or "ratio" in instr)


def test_engagement_tools_gated_data_socios():
    for tool in ("at_risk_socios", "socio_health", "health_overview"):
        assert app.TOOL_REQUIRED_GRANT[tool] == "data.socios"
        assert tool in {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    out = app.dispatch_tool("health_overview", {}, {"grants": frozenset({"data.eventos"})})
    assert out == {"error": "forbidden", "tool": "health_overview", "required_grant": "data.socios"}


def test_engagement_allowed_with_grant(monkeypatch):
    monkeypatch.setitem(app.DATA, "actividades", _acts())
    out = app.dispatch_tool("at_risk_socios", {"days": 120}, {"grants": frozenset({"data.socios"})})
    assert out.get("error") != "forbidden" and "socios" in out


# ---- P5h-b: churn analysis (data.financiero) + active-only refinement ----

def _cuotas():
    return pd.DataFrame([
        {"altabaja_id": "1", "socio": "ACME", "status": "activo", "join_date": "01/01/2020",
         "leave_date": "", "churn_reason_type": "", "churn_reason": ""},
        {"altabaja_id": "2", "socio": "OLD1", "status": "baja", "join_date": "01/01/2015",
         "leave_date": "01/01/2023", "churn_reason_type": "Económico", "churn_reason": "Recortes"},
        {"altabaja_id": "3", "socio": "OLD2", "status": "baja", "join_date": "01/01/2018",
         "leave_date": "01/06/2024", "churn_reason_type": "No creen en secpho", "churn_reason": "Sin valor"},
        {"altabaja_id": "4", "socio": "OLD3", "status": "baja", "join_date": "01/01/2019",
         "leave_date": "01/01/2024", "churn_reason_type": "Económico", "churn_reason": "Crisis"},
    ])


def test_churn_breakdown(monkeypatch):
    monkeypatch.setitem(app.DATA, "cuotas", _cuotas())
    out = app.churn_breakdown()
    assert out["available"] is True and out["total_left"] == 3
    assert out["by_reason"] == {"Económico": 2, "No creen en secpho": 1}
    assert out["recent_leavers"][0]["socio"] == "OLD2"      # newest leave first (01/06/2024)
    assert out["recent_leavers"][0]["reason_type"] == "No creen en secpho"
    tenure = {r["socio"]: r["tenure_years"] for r in out["recent_leavers"]}
    assert tenure["OLD1"] == 8.0                            # 2015 -> 2023


def test_churn_breakdown_gated_data_financiero():
    assert app.TOOL_REQUIRED_GRANT["churn_breakdown"] == "data.financiero"
    out = app.dispatch_tool("churn_breakdown", {}, {"grants": frozenset({"data.socios"})})
    assert out == {"error": "forbidden", "tool": "churn_breakdown", "required_grant": "data.financiero"}


def test_at_risk_active_only_filters_departed(monkeypatch):
    _pin_today(monkeypatch)
    monkeypatch.setitem(app.DATA, "actividades", _acts())   # STALE + GONE are quiet; ACME active
    monkeypatch.setitem(app.DATA, "cuotas", pd.DataFrame([
        {"altabaja_id": "1", "socio": "ACME", "status": "activo"},
        {"altabaja_id": "2", "socio": "STALE", "status": "baja"},
        {"altabaja_id": "3", "socio": "GONE", "status": "baja"},
    ]))
    out = app.at_risk_socios(days=120, active_only=True)
    assert out["active_only"] is True and out["total"] == 0  # STALE/GONE departed -> filtered out
    assert app.at_risk_socios(days=120, active_only=False)["total"] == 2  # includes departed

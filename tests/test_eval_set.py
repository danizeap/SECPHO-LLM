"""Intelligence eval set (intelligence-eval-set) — hermetic. The combined P4+P5 guardrail:
- the FULL tool->grant gating matrix (an access-model snapshot; drift forces a deliberate review),
- cross-concept composition (the per-socio intelligence tools all key on the same socio name, so a
  mixed-concept query like "ACME: finances + engagement + collaborators" composes), and
- fail-closed sensitive gates.
The live mixed-concept STRESS QUESTIONS (run against the real agent) live in
sdd-plus/eval/p5-stress-questions.md. No network, no LLM.
Run: python -m pytest tests/test_eval_set.py
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


# The access model as one snapshot. Every agent tool and the grant that gates it.
EXPECTED_GRANTS = {
    "search_people": "data.socios", "get_person_profile": "data.socios", "search_socios": "data.socios",
    "get_socio_profile": "data.socios", "rank_socios": "data.socios", "ecosystem_overview": "data.socios",
    "aggregate_stats": "data.socios", "list_events": "data.eventos", "list_activities": "data.eventos",
    "list_retos": "data.retos", "list_projects": "data.proyectos", "search_success_cases": "data.casos",
    "recommend_contacts": "tool.matchmaking", "rerank_contacts": "tool.matchmaking",
    "financial_overview": "data.financiero", "socio_financials": "data.financiero",
    "cuota_status": "data.financiero", "list_invoices": "data.financiero",
    "top_socios_by_turnover": "data.financiero",
    "at_risk_socios": "data.socios", "socio_health": "data.socios", "health_overview": "data.socios",
    "churn_breakdown": "data.financiero",
    "socio_network": "data.socios", "network_overview": "data.socios", "connection_between": "data.socios",
}


def test_gating_matrix_snapshot():
    # If this fails, a tool's gate changed — review it deliberately and update the snapshot.
    assert app.TOOL_REQUIRED_GRANT == EXPECTED_GRANTS


def test_every_schema_tool_is_gated():
    names = {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    assert names <= set(app.TOOL_REQUIRED_GRANT), names - set(app.TOOL_REQUIRED_GRANT)


def test_sensitive_tools_refused_to_data_socios_only():
    # Engagement/network grants do NOT unlock financial/churn data — fail-closed, before the tool runs.
    ctx = {"grants": frozenset({"data.socios", "data.eventos", "data.retos", "data.proyectos", "tool.chat"})}
    for tool in ("financial_overview", "socio_financials", "cuota_status", "list_invoices", "churn_breakdown"):
        out = app.dispatch_tool(tool, {"socio": "X"}, ctx)
        assert out["error"] == "forbidden" and out["required_grant"] == "data.financiero"


def test_cross_concept_composition(monkeypatch):
    # The SAME socio across the intelligence sources -> the per-socio tools all key on its name, so a
    # "show me ACME: finances + engagement + collaborators" query composes deterministically.
    monkeypatch.setattr(app, "today_utc", lambda: pd.Timestamp("2026-06-29"))
    monkeypatch.setattr(app, "_NETWORK", {"sig": None, "adj": None})
    monkeypatch.setitem(app.DATA, "actividades", pd.DataFrame([
        {"activity_id": "1", "socio": "ACME", "date": "01/01/2025", "type": "R", "author": "a", "description": "x"}]))
    monkeypatch.setitem(app.DATA, "cuotas", pd.DataFrame([
        {"altabaja_id": "1", "socio": "ACME", "status": "activo", "cuota_amount": "3.000,00 €",
         "join_date": "01/01/2018", "churn_reason": ""}]))
    monkeypatch.setitem(app.DATA, "invoices", pd.DataFrame([
        {"invoice_id": "1", "invoice_no": "A1", "socio": "ACME", "status": "Vencida", "concept": "Cuota",
         "invoice_date": "01/02/2025", "due_date": "01/03/2025", "payment_date": "", "net": "2000", "total": "2.420,00 €"}]))
    monkeypatch.setitem(app.DATA, "negocio_financiero", pd.DataFrame([
        {"socio": "ACME", "revenue": "1.000.000,00 €", "investment_received": "", "employees": "30"}]))
    monkeypatch.setitem(app.DATA, "contributions", pd.DataFrame())
    monkeypatch.setitem(app.DATA, "proyectos", pd.DataFrame([
        {"proyecto_id": "1", "acronym": "P", "title": "P", "partners": "ACME, BETA"}]))
    monkeypatch.setitem(app.DATA, "retos", pd.DataFrame())

    assert app.socio_health("ACME")["going_quiet"] is True                       # engagement: drifting
    assert app.socio_financials("ACME")["invoices"]["outstanding"] == "2.420,00 €"  # financial: overdue
    assert app.socio_network("ACME")["collaborators"][0]["socio"] == "BETA"       # network: collaborator
    # all three keyed on the same socio name -> the agent can chain them into one answer

"""Financial tools (P5f-b, live-financial-views) — hermetic. Injects synthetic financial frames into
DATA and checks the DETERMINISTIC aggregates + the data.financiero fail-closed gating. No network,
no LLM. Run: python -m pytest tests/test_financial_tools.py
"""
import os
import sys

import pandas as pd

os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)   # live off
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402


# ---- number parsing/formatting ----

def test_parse_eur_formats():
    assert app._parse_eur("1.234,56 €") == 1234.56
    assert app._parse_eur("-1.234,56 €") == -1234.56
    assert app._parse_eur("1.500.000,00 €") == 1500000.0
    assert app._parse_eur("7500000") == 7500000.0
    assert app._parse_eur("75.000") == 75000.0          # dot thousands, no comma
    assert app._parse_eur("No definido") is None
    assert app._parse_eur("") is None


def test_fmt_eur():
    assert app._fmt_eur(1234.5) == "1.234,50 €"
    assert app._fmt_eur(-1000) == "-1.000,00 €"
    assert app._fmt_eur(None) == "—"


def test_inv_status_handles_multivalue():
    assert app._inv_status("Pagada") == "paid"
    assert app._inv_status("Vencida") == "overdue"
    assert app._inv_status("Enviada") == "sent"
    assert app._inv_status("Cancelada") == "cancelled"
    assert app._inv_status("Pagada, Vencida") == "overdue"   # multi-value: not silently 'unknown'
    assert app._inv_status("") == "unknown"


def _invoices():
    return pd.DataFrame([
        {"invoice_id": "1", "invoice_no": "A1", "socio": "ACME", "status": "Pagada", "concept": "Cuota",
         "invoice_date": "01/02/2025", "due_date": "01/03/2025", "payment_date": "15/02/2025", "net": "1000", "total": "1.210,00 €"},
        {"invoice_id": "2", "invoice_no": "A2", "socio": "ACME", "status": "Vencida", "concept": "Actividad",
         "invoice_date": "01/01/2024", "due_date": "01/02/2024", "payment_date": "", "net": "500", "total": "605,00 €"},
        {"invoice_id": "3", "invoice_no": "A3", "socio": "BETA", "status": "Enviada", "concept": "Cuota",
         "invoice_date": "01/02/2025", "due_date": "01/03/2025", "payment_date": "", "net": "100", "total": "121,00 €"},
        {"invoice_id": "4", "invoice_no": "A4", "socio": "BETA", "status": "Cancelada", "concept": "Feria",
         "invoice_date": "01/02/2025", "due_date": "", "payment_date": "", "net": "999", "total": "999,00 €"},
    ])


def _cuotas():
    return pd.DataFrame([
        {"altabaja_id": "10", "socio": "ACME", "cuota_amount": "1.200,00 €", "status": "activo",
         "join_date": "01/01/2020", "churn_reason": ""},
        {"altabaja_id": "11", "socio": "OLD", "cuota_amount": "600,00 €", "status": "baja",
         "join_date": "01/01/2019", "churn_reason": "No renueva"},
    ])


def _negocio():
    return pd.DataFrame([
        {"socio": "ACME", "revenue": "1.500.000,00 €", "investment_received": "500000", "employees": "42"},
        {"socio": "BETA", "revenue": "No definido", "investment_received": "", "employees": "5"},
    ])


def test_financial_overview_exact(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    monkeypatch.setitem(app.DATA, "cuotas", _cuotas())
    monkeypatch.setitem(app.DATA, "negocio_financiero", _negocio())
    out = app.financial_overview()
    inv = out["invoices"]
    assert inv["count"] == 4 and inv["socios_billed"] == 2
    assert inv["total_paid"] == "1.210,00 €"            # only Pagada
    assert inv["total_outstanding"] == "726,00 €"       # 605 Vencida + 121 Enviada
    assert inv["overdue_amount"] == "605,00 €" and inv["overdue_count"] == 1
    assert inv["total_invoiced"] == "1.936,00 €"        # excludes Cancelada (999)
    assert inv["paid_by_concept"] == {"Cuota": "1.210,00 €"}
    assert out["membership"] == {"active_members": 1, "left_members": 1, "annual_cuota_base": "1.200,00 €"}
    assert out["turnover"]["socios_with_turnover"] == 1
    assert out["turnover"]["median_turnover"] == "1.500.000,00 €"
    assert out["turnover"]["max_turnover"] == "1.500.000,00 €"
    assert "total_turnover" not in out["turnover"]            # robust stats, not a misleading sum


def test_turnover_robust_to_outliers(monkeypatch):
    # A few normal socios + one giant outlier (e.g. a member reporting group/global turnover).
    # The cluster summary must NOT present a raw sum (the outlier dominates it); median stays sane.
    monkeypatch.setitem(app.DATA, "invoices", pd.DataFrame())
    monkeypatch.setitem(app.DATA, "cuotas", pd.DataFrame())
    monkeypatch.setitem(app.DATA, "negocio_financiero", pd.DataFrame([
        {"socio": "A", "revenue": "2.000.000,00 €", "investment_received": "", "employees": "10"},
        {"socio": "B", "revenue": "2.500.000,00 €", "investment_received": "", "employees": "11"},
        {"socio": "C", "revenue": "3.000.000,00 €", "investment_received": "", "employees": "12"},
        {"socio": "D", "revenue": "3.500.000,00 €", "investment_received": "", "employees": "13"},
        {"socio": "E", "revenue": "100.000.000.000,00 €", "investment_received": "", "employees": "9"},
    ]))
    t = app.financial_overview()["turnover"]
    assert t["socios_with_turnover"] == 5
    assert t["median_turnover"] == "3.000.000,00 €"           # unmoved by the outlier
    assert t["max_turnover"] == "100.000.000.000,00 €"        # surfaces the outlier instead
    assert "total_turnover" not in t                          # no €100B-style misleading sum


def test_socio_financials(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    monkeypatch.setitem(app.DATA, "cuotas", _cuotas())
    monkeypatch.setitem(app.DATA, "negocio_financiero", _negocio())
    monkeypatch.setitem(app.DATA, "contributions", pd.DataFrame())
    out = app.socio_financials("ACME")
    assert out["invoices"]["total_paid"] == "1.210,00 €" and out["invoices"]["outstanding"] == "605,00 €"
    assert out["membership"]["status"] == "activo" and out["business"]["employees"] == "42"


def test_socio_financials_not_found(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    for k in ("cuotas", "negocio_financiero", "contributions"):
        monkeypatch.setitem(app.DATA, k, pd.DataFrame())
    assert app.socio_financials("ZZZ").get("found") is False


def test_cuota_status(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    out = app.cuota_status()                             # default pending = overdue + sent
    by = {r["socio"]: r for r in out["socios"]}
    assert by["ACME"]["outstanding"] == "605,00 €" and by["BETA"]["outstanding"] == "121,00 €"
    assert out["total_outstanding"] == "726,00 €"
    assert {r["socio"] for r in app.cuota_status("overdue")["socios"]} == {"ACME"}


def test_list_invoices_filters(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    assert app.list_invoices(socio="ACME")["total"] == 2
    out_y = app.list_invoices(year="2024")
    assert out_y["total"] == 1 and out_y["invoices"][0]["socio"] == "ACME"
    out_s = app.list_invoices(status="paid")
    assert out_s["total"] == 1 and out_s["invoices"][0]["invoice_no"] == "A1"


# ---- fail-closed gating ----

def test_financial_tools_require_data_financiero():
    for tool in ("financial_overview", "socio_financials", "cuota_status", "list_invoices"):
        assert app.TOOL_REQUIRED_GRANT[tool] == "data.financiero"
    out = app.dispatch_tool("financial_overview", {}, {"grants": frozenset({"data.socios"})})
    assert out == {"error": "forbidden", "tool": "financial_overview", "required_grant": "data.financiero"}


def test_financial_tool_allowed_with_grant(monkeypatch):
    monkeypatch.setitem(app.DATA, "invoices", _invoices())
    monkeypatch.setitem(app.DATA, "cuotas", _cuotas())
    monkeypatch.setitem(app.DATA, "negocio_financiero", _negocio())
    out = app.dispatch_tool("financial_overview", {}, {"grants": frozenset({"data.financiero"})})
    assert out.get("available") is True and out["invoices"]["count"] == 4


def test_financial_tools_registered():
    names = {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    for tool in ("financial_overview", "socio_financials", "cuota_status", "list_invoices"):
        assert tool in names and tool in app.TOOL_REQUIRED_GRANT

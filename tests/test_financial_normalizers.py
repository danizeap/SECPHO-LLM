"""Financial normalizers (P5f-a, live-financial-views) — hermetic. Feeds synthetic reports/v1
payloads using the EXACT live field names (verified via a schema-only probe) and checks the canonical
frames. No network, no LLM, live layer off.
Run: python -m pytest tests/test_financial_normalizers.py
"""
import os
import sys

os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)   # live off
sys.path.insert(0, "backend_api")
import live_data as ld  # noqa: E402


def test_normalize_negocio_financiero():
    raw = [{"Socio": "ACME", "Cifra de negocio": "1500000", "Inversion recibida": "500000",
            "Inversion buscada": "0", "Num. de empleados": "42", "Exportación": "Sí",
            "Fecha ult. act.": "30/03/2026"}]
    df = ld.normalize_negocio_financiero(raw)
    row = df.iloc[0]
    assert row["socio"] == "ACME" and row["revenue"] == "1500000"
    assert row["investment_received"] == "500000" and row["employees"] == "42"
    assert {"socio", "revenue", "investment_received", "investment_sought", "employees",
            "exportation", "last_updated"} <= set(df.columns)


def test_normalize_cuotas_dict_keyed_and_status():
    raw = {
        "10": {"Socio": "ACME", "Tipo de empresa": "Pyme", "Importe Cuota": "1200",
               "Fecha de incorporación": "01/01/2020", "Fecha de welcome": "05/01/2020",
               "Persona welcome": "X", "Fecha solicitud baja": "", "Fecha de baja definitiva": "",
               "Tipo motivo de baja": "", "Descripción motivo": ""},
        "11": {"Socio": "OLDCO", "Tipo de empresa": "Startup", "Importe Cuota": "600",
               "Fecha de incorporación": "01/01/2019", "Fecha de baja definitiva": "30/06/2023",
               "Tipo motivo de baja": "Económico", "Descripción motivo": "No renueva"},
        # "No consta" (not recorded) is the source's placeholder for an ACTIVE member, NOT a leave.
        "12": {"Socio": "NOWCO", "Tipo de empresa": "Pyme", "Importe Cuota": "900",
               "Fecha de incorporación": "01/01/2021", "Fecha de baja definitiva": "No consta",
               "Tipo motivo de baja": "", "Descripción motivo": ""},
    }
    df = ld.normalize_cuotas(raw)
    by_socio = {r["socio"]: r for _, r in df.iterrows()}
    assert by_socio["ACME"]["cuota_amount"] == "1200" and by_socio["ACME"]["status"] == "activo"
    assert by_socio["OLDCO"]["status"] == "baja" and by_socio["OLDCO"]["churn_reason"] == "No renueva"
    assert by_socio["NOWCO"]["status"] == "activo"       # 'No consta' is active, not a leave
    assert set(df["altabaja_id"]) == {"10", "11", "12"}  # source dict id -> stable diff key


def test_normalize_invoices_joins_list_fields():
    raw = {
        "f1": {"Número": "2025-001", "ID": 1, "Socio": "ACME", "Estado": ["Pagada"],
               "Concepto": ["Cuota", "2025"], "Fecha Factura": "01/02/2025", "Vencimiento": "01/03/2025",
               "Fecha de pago": "15/02/2025", "Neto": "1000", "Total": "1210"},
        "f2": {"Número": "2025-002", "ID": 2, "Socio": "BETA", "Estado": ["Pendiente"],
               "Concepto": ["Cuota"], "Fecha Factura": "01/02/2025", "Vencimiento": "01/03/2025",
               "Fecha de pago": "", "Neto": "500", "Total": "605"},
    }
    df = ld.normalize_invoices(raw)
    by_no = {r["invoice_no"]: r for _, r in df.iterrows()}
    assert by_no["2025-001"]["status"] == "Pagada" and by_no["2025-001"]["concept"] == "Cuota, 2025"
    assert by_no["2025-001"]["total"] == "1210" and by_no["2025-001"]["due_date"] == "01/03/2025"
    assert by_no["2025-002"]["status"] == "Pendiente" and by_no["2025-002"]["payment_date"] == ""
    assert set(df["invoice_id"]) == {"f1", "f2"}


def test_normalize_contributions_year_dict():
    raw = [{"Socio": "ACME", "Participación": "Alta", "Ranking": "3", "TOTAL": "36000",
            "Finan. 2024": "12000", "Finan. 2025": "12000", "Finan. 2026": "12000",
            "Act. 2024": 5, "Act. 2025": 6, "Quociente act/meses": 0.5}]
    df = ld.normalize_contributions(raw)
    row = df.iloc[0]
    assert row["socio"] == "ACME" and row["total_contribution"] == "36000"
    assert row["contributions_by_year"] == {"2024": "12000", "2025": "12000", "2026": "12000"}


def test_financial_sources_registered():
    for s in ("negocio_financiero", "cuotas", "invoices", "contributions"):
        assert s in ld.SOURCES and s in ld.KEY_COLUMNS and s in ld.SENSITIVE_SOURCES
    assert ld.KEY_COLUMNS["invoices"] == "invoice_id"     # diffs on a key the frame actually has


def test_financial_sources_dont_load_when_live_off():
    # Hermetic guarantee: with the live layer off, nothing fetches.
    assert ld.live_enabled() is False
    assert ld.load_all() == {}


def test_change_feed_omits_sensitive_keys():
    # P5f-c: 🔴 sources keep change COUNTS but never leak the changed key values (socio names / ids).
    d = {"added": ["ACME", "BETA"], "modified": ["GAMMA"], "removed": []}
    sens = ld._change_entry("negocio_financiero", d)
    assert sens["added"] == 2 and sens["modified"] == 1 and sens["sensitive"] is True
    assert sens["keys"] == {}                              # no socio names in the feed
    nonsens = ld._change_entry("retos", d)
    assert nonsens["sensitive"] is False and nonsens["keys"]["added"] == ["ACME", "BETA"]

"""Live-data layer (Phase 1) — hermetic. Fixtures use the real endpoint field SHAPES with made-up
values; no real confidential data, no network. Run: python -m pytest tests/test_live_data.py
"""
import os
import sys

import requests

# Default to live DISABLED -> no network. Opt-in needs both a token AND the SECPHO_LIVE_DATA flag.
for _v in ("SECPHO_API_AUTH_TOKEN", "SECPHO_REPORTS_API_TOKEN", "SECPHO_LIVE_DATA"):
    os.environ.pop(_v, None)
sys.path.insert(0, "backend_api")
import live_data as ld  # noqa: E402

RETOS_FIXTURE = {
    "76263": {
        "Num. reto": "0220", "Título": "Láser industrial",
        "Descripción": "<h2>Descripción</h2>\r\nCERN busca proveedores",
        "Sector/es": "Sector energético", "Entidad emisora": "CDTI",
        "Fecha envío": "16/06/2026", "Fecha cierre": "22/06/2026",
        "Entidades que aplican": "", "Tipo de conexión": "",
        "¿Surge proyecto?": "No sabemos", "Socio beneficiado": "",
    }
}
PROY_FIXTURE = {
    "152": {
        "ID": 152, "Acrónimo": "ACME", "Título idea/proyecto": "Proyecto X",
        "Inicio": "2024", "Final": "2026", "Origen Fondos": "EU",
        "Programa financiación": "Horizon", "Partners": "A | B", "Tecnologías": "Fotónica",
        "Sectores": "Salud", "Ámbitos": "Industria 4.0", "Tipo": "I+D", "Etapa": "En curso",
        "Tamaño": "Grande", "Responsable": "X", "Progreso (%)": "50",
        "Presupuesto total (€)": "1000000", "Ayuda recibida (€)": "500000",
        "Capital inyectado (€)": "0", "Impacto": "<p>Alto</p>", "URL": "http://x",
    }
}
CASOS_FIXTURE = [{
    "Título": "BILASURF", "Resumen": "<p>Superficies funcionalizadas</p>", "Año": "2026",
    "AEI": "No", "EU": "Sí", "Tecnologías": "['Fotónica', 'IA']", "Ámbitos": "['Industria 4.0']",
    "ODS": "['07']", "Sectores": "['Espacio']", "Entidades": "{'1': 'CEIT'}",
}]

CANONICAL_RETOS_COLS = [
    "reto_id", "reto_number", "title", "description_clean", "sectors", "issuing_entities",
    "submission_date", "closing_date", "applying_entities", "connection_type",
    "creates_project", "beneficiary_socio", "reto_text",
]


def test_retos_normalizer_matches_canonical_schema():
    df = ld.normalize_retos(RETOS_FIXTURE)
    assert list(df.columns) == CANONICAL_RETOS_COLS  # exact match to retos_normalized.csv
    row = df.iloc[0]
    assert row["reto_id"] == "76263" and row["reto_number"] == "0220"
    assert row["closing_date"] == "22/06/2026"            # date format preserved for consumers
    assert "<h2>" not in row["description_clean"] and "CERN" in row["description_clean"]  # HTML stripped


def test_proyectos_normalizer():
    df = ld.normalize_proyectos(PROY_FIXTURE)
    row = df.iloc[0]
    assert row["proyecto_id"] == "152" and row["acronym"] == "ACME"
    assert row["budget_total"] == "1000000"
    assert "<p>" not in row["impact"] and row["impact"] == "Alto"


def test_casos_normalizer_parses_repr_lists():
    row = ld.normalize_casos(CASOS_FIXTURE).iloc[0]
    assert row["technologies"] == ["Fotónica", "IA"]      # repr-string -> real list
    assert row["entities"] == {"1": "CEIT"}               # repr-string -> real dict
    assert "<p>" not in row["summary"]


def test_live_off_by_default_even_with_token(monkeypatch):
    # A token alone must NOT enable live (a .env token shouldn't trigger network in tests).
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "test-token")
    monkeypatch.delenv("SECPHO_LIVE_DATA", raising=False)
    assert ld.live_enabled() is False                     # flag off -> disabled
    assert ld.load_all() == {}                            # no request


def test_load_all_isolates_failures(monkeypatch):
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("SECPHO_LIVE_DATA", "1")           # explicit opt-in

    def fake_fetch(endpoint, extra=""):
        if endpoint == "retos":
            return RETOS_FIXTURE
        raise requests.RequestException("simulated source failure")

    monkeypatch.setattr(ld, "_fetch_json", fake_fetch)
    out = ld.load_all(["retos", "proyectos", "casos_exito"])
    assert "retos" in out                                  # the good source loads
    assert "proyectos" not in out and "casos_exito" not in out  # failed sources just absent (fallback)
    assert "retos" in ld.freshness()                       # freshness stamped on success

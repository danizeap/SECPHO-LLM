"""Live-data layer (Phase 1) — hermetic. Fixtures use the real endpoint field SHAPES with made-up
values; no real confidential data, no network. Run: python -m pytest tests/test_live_data.py
"""
import os
import sys

import pandas as pd
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


ACTIV_FIXTURE = [{
    "Socio": "ACME", "Tipo socio": "Pleno", "Fecha": "15/03/2026", "Autor": "Ana",
    "[QN]": "Q1", "Tipo": "Reunión", "Descripción": "<p>Llamada de seguimiento</p>",
}]


def test_actividades_normalizer():
    df = ld.normalize_actividades(ACTIV_FIXTURE)
    expected = {"activity_id", "socio", "socio_type", "date", "author", "qn", "type", "description"}
    assert expected.issubset(set(df.columns))
    row = df.iloc[0]
    assert row["socio"] == "ACME" and row["date"] == "15/03/2026" and row["type"] == "Reunión"
    assert "<p>" not in row["description"] and "seguimiento" in row["description"]   # HTML stripped
    assert len(row["activity_id"]) == 16 and ld.KEY_COLUMNS["actividades"] == "activity_id"  # synthetic key


def test_live_off_by_default_even_with_token(monkeypatch):
    # A token alone must NOT enable live (a .env token shouldn't trigger network in tests).
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "test-token")
    monkeypatch.delenv("SECPHO_LIVE_DATA", raising=False)
    assert ld.live_enabled() is False                     # flag off -> disabled
    assert ld.load_all() == {}                            # no request


def test_load_all_isolates_failures(monkeypatch):
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("SECPHO_LIVE_DATA", "1")           # explicit opt-in

    def fake_fetch(endpoint, extra="", timeout=None):
        if endpoint == "retos":
            return RETOS_FIXTURE
        raise requests.RequestException("simulated source failure")

    monkeypatch.setattr(ld, "_fetch_json", fake_fetch)
    out = ld.load_all(["retos", "proyectos", "casos_exito"])
    assert "retos" in out                                  # the good source loads
    assert "proyectos" not in out and "casos_exito" not in out  # failed sources just absent (fallback)
    assert "retos" in ld.freshness()                       # freshness stamped on success


# --------------------------------------------------------------------------- #
# Phase 2: refresher + in-RAM change-feed
# --------------------------------------------------------------------------- #
def _reset_refresher_state():
    ld._LAST.clear()
    ld._LAST_REFRESH.clear()
    ld._CHANGES.clear()


def test_diff_frames_detects_add_modify_remove():
    old = pd.DataFrame([{"reto_id": "1", "title": "A"}, {"reto_id": "2", "title": "B"}])
    new = pd.DataFrame([{"reto_id": "2", "title": "B2"}, {"reto_id": "3", "title": "C"}])
    d = ld.diff_frames(old, new, "reto_id")
    assert d["added"] == ["3"] and d["removed"] == ["1"] and d["modified"] == ["2"]


def test_refresh_cycle_baseline_then_change(monkeypatch):
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "t")
    monkeypatch.setenv("SECPHO_LIVE_DATA", "1")
    _reset_refresher_state()
    seq = {"i": 0}
    frames = [
        pd.DataFrame([{"reto_id": "1", "title": "A"}]),                                   # baseline
        pd.DataFrame([{"reto_id": "1", "title": "A"}, {"reto_id": "2", "title": "B"}]),   # +1 added
    ]
    monkeypatch.setattr(ld, "load_source", lambda name: frames[min(seq["i"], len(frames) - 1)])
    applied = {}

    out1 = ld._refresh_once(["retos"], apply_fn=lambda n, df: applied.__setitem__(n, df))
    assert out1 == [] and "retos" in applied          # first pull is the baseline: no change emitted
    seq["i"] = 1
    out2 = ld._refresh_once(["retos"], apply_fn=lambda n, df: applied.__setitem__(n, df))
    assert len(out2) == 1 and out2[0]["source"] == "retos" and out2[0]["added"] == 1
    assert ld.changes()[0]["added"] == 1              # the change is on the in-RAM feed


def test_refresh_cycle_stale_while_revalidate_on_failure(monkeypatch):
    monkeypatch.setenv("SECPHO_API_AUTH_TOKEN", "t")
    monkeypatch.setenv("SECPHO_LIVE_DATA", "1")
    _reset_refresher_state()
    calls = {"i": 0}
    good = pd.DataFrame([{"reto_id": "1", "title": "A"}])

    def load(name):
        if calls["i"] == 0:
            return good
        raise requests.RequestException("source down")

    monkeypatch.setattr(ld, "load_source", load)
    applied = {}
    ld._refresh_once(["retos"], apply_fn=lambda n, df: applied.__setitem__(n, df))
    before = applied["retos"]
    calls["i"] = 1
    out = ld._refresh_once(["retos"], apply_fn=lambda n, df: applied.__setitem__(n, df))
    assert out == []                                  # failed cycle emits nothing
    assert applied["retos"] is before                 # SWR: last-good view left untouched

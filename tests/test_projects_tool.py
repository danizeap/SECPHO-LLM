"""list_projects agent tool (P3) — hermetic. Injects an in-memory proyectos table and exercises
the tool directly. No network (live off), no LLM. Run: python -m pytest tests/test_projects_tool.py
"""
import os
import sys

import pandas as pd

os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
os.environ["OPENAI_API_KEY"] = ""          # hermetic
os.environ.pop("SECPHO_LIVE_DATA", None)   # live off -> no refresher/network on import
sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402


def _sample_projects() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "proyecto_id": "1", "acronym": "PHOTON", "title": "Proyecto de fotónica",
            "technologies": "Fotónica", "sectors": "Salud", "ambitos": "Industria 4.0",
            "partners": "AIMEN | CEIT", "type": "I+D", "stage": "En curso", "start": "2024",
            "end": "2026", "lead": "X", "funding_program": "Horizon", "url": "http://x",
            "budget_total": "1000000", "aid_received": "500000", "capital": "0",
        },
        {
            "proyecto_id": "2", "acronym": "AGRO", "title": "Proyecto agro", "technologies": "IA",
            "sectors": "Agroalimentación", "ambitos": "", "partners": "", "type": "", "stage": "",
            "start": "", "end": "", "lead": "", "funding_program": "", "url": "",
            "budget_total": "2000000", "aid_received": "", "capital": "",
        },
    ])


def test_list_projects_filters_by_query(monkeypatch):
    monkeypatch.setitem(app.DATA, "proyectos", _sample_projects())
    out = app.list_projects(query="fotónica", limit=10)
    assert out["total"] == 1 and out["projects"][0]["acronym"] == "PHOTON"


def test_list_projects_excludes_financial_fields(monkeypatch):
    monkeypatch.setitem(app.DATA, "proyectos", _sample_projects())
    out = app.list_projects(limit=10)
    assert out["total"] == 2
    project = out["projects"][0]
    for banned in ("budget_total", "aid_received", "capital"):
        assert banned not in project          # financials gated until the access model (P4)
    assert "partners" in project and "technologies" in project and "stage" in project


def test_list_projects_empty_when_no_live_data(monkeypatch):
    monkeypatch.setitem(app.DATA, "proyectos", pd.DataFrame())
    assert app.list_projects(query="x") == {"projects": [], "total": 0}


def test_list_projects_is_a_registered_agent_tool():
    names = {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    assert "list_projects" in names           # the agent can actually call it


def _sample_activities() -> pd.DataFrame:
    return pd.DataFrame([
        {"activity_id": "a1", "socio": "ACME", "socio_type": "Pleno", "date": "15/03/2026",
         "author": "Ana", "qn": "Q1", "type": "Reunión", "description": "Llamada sobre fotónica"},
        {"activity_id": "a2", "socio": "AGRO", "socio_type": "Pleno", "date": "20/01/2026",
         "author": "Beto", "qn": "Q1", "type": "Evento", "description": "Webinar de IA"},
    ])


def test_list_activities_filters_by_socio(monkeypatch):
    monkeypatch.setitem(app.DATA, "actividades", _sample_activities())
    out = app.list_activities(socio="ACME")
    assert out["total"] == 1 and out["activities"][0]["socio"] == "ACME"


def test_list_activities_most_recent_first(monkeypatch):
    monkeypatch.setitem(app.DATA, "actividades", _sample_activities())
    out = app.list_activities(limit=10)
    assert out["total"] == 2 and out["activities"][0]["date"] == "15/03/2026"  # 15/03 newer than 20/01


def test_list_activities_empty_and_registered(monkeypatch):
    monkeypatch.setitem(app.DATA, "actividades", pd.DataFrame())
    assert app.list_activities(query="x") == {"activities": [], "total": 0}
    assert "list_activities" in {t["name"] for t in app.AGENT_TOOL_SCHEMAS}


def _sample_cases() -> pd.DataFrame:
    return pd.DataFrame([
        {"title": "BILASURF", "summary": "Superficies funcionalizadas con fotónica avanzada",
         "year": "2026", "technologies": ["Fotónica"], "sectors": ["Espacio"]},
        {"title": "AGROAI", "summary": "Inteligencia artificial para agricultura de precisión",
         "year": "2025", "technologies": ["IA"], "sectors": ["Agroalimentación"]},
    ])


def test_search_success_cases_keyword_fallback(monkeypatch):
    # OPENAI_API_KEY is "" for this module -> no embeddings -> deterministic keyword fallback.
    app._CASOS_RAG.update(hash=None, vecs=None, rows=None)
    monkeypatch.setitem(app.DATA, "casos_exito", _sample_cases())
    out = app.search_success_cases(query="fotónica")
    assert out["mode"] == "keyword" and out["total"] >= 1
    assert any("fotónica" in (c["title"] + c["summary"]).lower() for c in out["cases"])


def test_search_success_cases_returns_summary_for_citation(monkeypatch):
    app._CASOS_RAG.update(hash=None, vecs=None, rows=None)
    monkeypatch.setitem(app.DATA, "casos_exito", _sample_cases())
    out = app.search_success_cases(query="agricultura")
    assert any("agricultura" in c["summary"].lower() for c in out["cases"])  # the matched text is returned


def test_search_success_cases_empty_and_registered(monkeypatch):
    monkeypatch.setitem(app.DATA, "casos_exito", pd.DataFrame())
    assert app.search_success_cases(query="x")["cases"] == []
    assert "search_success_cases" in {t["name"] for t in app.AGENT_TOOL_SCHEMAS}

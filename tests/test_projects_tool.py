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

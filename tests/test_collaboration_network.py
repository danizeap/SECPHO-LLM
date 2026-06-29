"""Collaboration network (P5n-a, collaboration-network) — hermetic. Injects synthetic proyectos/retos
frames, resets the network cache, and checks edge construction, weights, the legal-form rejoin, and the
data.socios gating. No network, no LLM.
Run: python -m pytest tests/test_collaboration_network.py
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


def _proj():
    return pd.DataFrame([
        {"proyecto_id": "1", "acronym": "PHOTON", "title": "P1", "partners": "ACME | BETA | GAMMA"},
        {"proyecto_id": "2", "acronym": "OPTO", "title": "P2", "partners": "ACME, BETA"},
        {"proyecto_id": "3", "acronym": "SOLO", "title": "P3", "partners": "DELTA"},          # single -> no edge
        {"proyecto_id": "4", "acronym": "LEGAL", "title": "P4", "partners": "Lasercare, SL, ACME"},  # legal form
    ])


def _ret():
    return pd.DataFrame([
        {"reto_id": "r1", "reto_number": "R1", "title": "Reto1", "issuing_entities": "BETA",
         "applying_entities": "ACME, GAMMA", "beneficiary_socio": ""},
    ])


def _wire(monkeypatch):
    monkeypatch.setattr(app, "_NETWORK", {"sig": None, "adj": None})   # fresh cache
    monkeypatch.setitem(app.DATA, "proyectos", _proj())
    monkeypatch.setitem(app.DATA, "retos", _ret())


def test_split_entities_legal_form_rejoin():
    assert app._split_entities("ACME | BETA") == ["ACME", "BETA"]
    assert app._split_entities("Lasercare, SL, ACME") == ["Lasercare, SL", "ACME"]   # 'SL' rejoined
    assert app._split_entities("A, B, C") == ["A", "B", "C"]
    assert app._split_entities("") == []


def test_socio_network_ranking_and_via(monkeypatch):
    _wire(monkeypatch)
    out = app.socio_network("ACME")
    assert out["degree"] == 3                                  # BETA, GAMMA, "Lasercare, SL"
    top = out["collaborators"][0]
    assert top["socio"] == "BETA" and top["shared"] == 3       # 2 projects + 1 reto
    assert top["via_projects"] == 2 and top["via_retos"] == 1
    socios = {c["socio"] for c in out["collaborators"]}
    assert "Lasercare, SL" in socios                           # legal-form entity kept whole


def test_network_overview_hubs(monkeypatch):
    _wire(monkeypatch)
    out = app.network_overview()
    assert out["available"] is True and out["socios"] == 4     # ACME, BETA, GAMMA, Lasercare,SL (DELTA isolated)
    assert out["connections"] == 4                              # ACME-BETA, ACME-GAMMA, BETA-GAMMA, ACME-Lasercare
    assert out["top_hubs"][0]["socio"] == "ACME"               # highest weighted degree


def test_connection_between(monkeypatch):
    _wire(monkeypatch)
    out = app.connection_between("ACME", "GAMMA")
    assert out["connected"] is True and out["shared"] == 2     # 1 project + 1 reto
    assert {v["type"] for v in out["via"]} == {"project", "reto"}
    assert app.connection_between("ACME", "ZZZ")["found"] is False


def test_connection_between_withholds_gated_labels(monkeypatch):
    _wire(monkeypatch)
    # ACME-GAMMA share 1 project (PHOTON) + 1 reto (Reto1). data.socios WITHOUT data.retos/proyectos
    # must NOT see the reto/project labels (those are gated by list_retos/list_projects).
    out = app.connection_between("ACME", "GAMMA", grants=frozenset({"data.socios"}))
    labels = [v.get("label") for v in out["via"]]
    assert "Reto1" not in labels and "PHOTON" not in labels       # both withheld
    assert {v["type"] for v in out["via"]} == {"project", "reto"}  # structure preserved
    full = app.connection_between("ACME", "GAMMA",
                                  grants=frozenset({"data.socios", "data.retos", "data.proyectos"}))
    flabels = {v["label"] for v in full["via"]}
    assert "Reto1" in flabels and "PHOTON" in flabels             # granted -> labels shown
    assert any(v["label"] == "Reto1" for v in app.connection_between("ACME", "GAMMA")["via"])  # internal


def test_connection_between_dispatch_threads_grants(monkeypatch):
    _wire(monkeypatch)
    out = app.dispatch_tool("connection_between", {"socio_a": "ACME", "socio_b": "GAMMA"},
                            {"grants": frozenset({"data.socios"})})
    assert out["connected"] is True and "Reto1" not in [v.get("label") for v in out["via"]]


def test_net_find_deterministic():
    adj = {"Tech SL Madrid": {}, "Tech SL Bilbao": {}, "Tech": {}}
    assert app._net_find(adj, "Tech SL") == "Tech SL Bilbao"     # equal length -> alphabetical, stable
    assert app._net_find(adj, "Tech") == "Tech"                  # exact match wins over substrings


def test_network_tools_gated_data_socios(monkeypatch):
    _wire(monkeypatch)
    for tool in ("socio_network", "network_overview", "connection_between"):
        assert app.TOOL_REQUIRED_GRANT[tool] == "data.socios"
        assert tool in {t["name"] for t in app.AGENT_TOOL_SCHEMAS}
    out = app.dispatch_tool("network_overview", {}, {"grants": frozenset({"data.eventos"})})
    assert out == {"error": "forbidden", "tool": "network_overview", "required_grant": "data.socios"}
    ok = app.dispatch_tool("socio_network", {"socio": "ACME"}, {"grants": frozenset({"data.socios"})})
    assert ok.get("error") != "forbidden" and ok["degree"] == 3

"""Asking the chat for a report yields the UNIFIED report (same as the tuner/download),
never the old free-form LLM briefing. Hermetic: no API key -> deterministic, no prose.

Run: python -m pytest tests/test_chat_report_unified.py
"""
import os
import sys

os.environ["SECPHO_APP_PASSWORD"] = "testpass"
os.environ["SECPHO_SESSION_SECRET"] = "testsecret_integration_0123456789"
# Set (don't pop) to "" before import: the app calls load_dotenv() on import, which would
# RESTORE a popped key from a .env. An existing (empty) var is left alone -> deterministic, no LLM.
os.environ["OPENAI_API_KEY"] = ""

sys.path.insert(0, "backend_api")
import mvp_web_app as app  # noqa: E402


def test_chat_report_is_the_unified_report():
    app.set_request_lang("es")
    res = app.chat_flow("dame el informe de David Santana", None)
    assert res.get("kind") == "report"
    h = res.get("answer_html", "")
    assert 'class="rep"' in h                        # the unified report fragment
    assert "Informe de Valor y Oportunidades" in h   # unified heading, not "Matchmaker Brief"
    assert "Contactos recomendados" in h
    assert "rep-download" in h and "downloadReportFromBtn" in h  # same download affordance
    assert "Matchmaker Brief" not in h               # NOT the old free-form report


def test_unified_helper_returns_html_not_markdown():
    app.set_request_lang("es")
    resp = app.unified_report_chat_response(74638)
    assert resp and resp["kind"] == "report"
    assert resp["answer_html"].startswith('<div class="rep">')
    # plain-text fallback is a title, not a full markdown document
    assert resp["answer"].startswith("Informe de Valor y Oportunidades")


def test_free_form_report_function_is_gone():
    # The last "LLM writes the whole report" function must no longer exist.
    assert not hasattr(app, "llm_report_for_person")

"""Unified-report invariants: the chat HTML and the downloaded .docx are the same report,
the injected ranking is honored, and no sensitive personal field is ever structurally included.

Run: python -m pytest tests/test_unified_report.py
"""
import html as H
import re

import report_engine as RE
from report_engine import data_access as da
from report_engine import render_docx, render_html
from report_engine import report as rg


def _valid_target() -> int:
    mem = {int(x) for x in da.members()["member_id"].tolist()}
    return next(int(t) for t in da.matches()["target_member_id"].tolist() if int(t) in mem)


def _socio_with_members() -> str:
    counts = da.members()["socio"].astype(str).str.lower().value_counts()
    return next(s for s in da.socios()["socio"].tolist() if counts.get(str(s).lower(), 0) >= 1)


def _docx_text(model) -> list:
    d = render_docx.render(model)
    return [p.text.strip() for p in d.paragraphs if p.text.strip()]


def _html_text(model) -> list:
    s = render_html.render(model)
    s = re.sub(r"</?strong>", "", s)   # inline runs stay on their line
    s = re.sub(r"<[^>]+>", "\n", s)    # block tags -> line breaks
    return [H.unescape(x).strip() for x in s.split("\n") if x.strip()]


def test_html_equals_docx_person():
    m = rg.build_person_report(_valid_target())
    assert _html_text(m) == _docx_text(m)
    assert len(_docx_text(m)) > 10  # not a degenerate empty render


def test_html_equals_docx_company():
    m = rg.build_company_report(_socio_with_members())
    assert _html_text(m) == _docx_text(m)


def test_injected_contact_order_is_honored():
    # The app injects the ranked contacts; the report must render them in exactly that order.
    tid = _valid_target()
    default = da.contacts_for_person(tid)
    assert len(default) >= 2
    reversed_rows = list(reversed(default))
    m = rg.build_person_report(tid, contacts=reversed_rows)
    assert [c["name"] for c in m.contacts] == [da._clean(r["candidate_name"]) for r in reversed_rows]


def test_no_sensitive_fields_are_structurally_included():
    # children / gender / food_preferences must never reach the report model — privacy by allowlist.
    m = rg.build_person_report(_valid_target())
    labels = {lbl.lower() for lbl, _ in m.ficha}
    for banned in ("hijos", "género", "genero", "comida", "gender", "children", "food"):
        assert not any(banned in lbl for lbl in labels), f"sensitive ficha label leaked: {banned}"
    allowed_contact_keys = {
        "candidate_member_id", "name", "socio", "role", "rationale",
        "shared_tech", "shared_sectors", "shared_ambitos", "shared_needs", "shared_location",
        "shared_hobbies", "shared_sports", "shared_languages", "shared_university",
    }
    for c in m.contacts:
        assert set(c).issubset(allowed_contact_keys), f"unexpected contact field(s): {set(c) - allowed_contact_keys}"


def test_generate_html_is_a_safe_escaped_fragment():
    frag = RE.generate_html("person", _valid_target())
    assert frag.startswith('<div class="rep">') and frag.endswith("</div>")
    assert "<script" not in frag.lower()


def test_llm_prose_slots_render_identically_in_html_and_docx():
    # P2: when the LLM prose is filled (exec summary + per-contact rationale), both renderers must
    # show it identically — proving the narrative goes through the same single layout.
    tid = _valid_target()
    m = rg.build_person_report(tid)
    m.exec_summary = "Resumen ejecutivo de prueba para verificar el render."
    if m.contacts:
        m.contacts[0]["rationale"] = "Esta persona encaja por su solapamiento tecnológico y de necesidades."
    assert _html_text(m) == _docx_text(m)
    text = "\n".join(_docx_text(m))
    assert "Resumen ejecutivo de prueba" in text
    if m.contacts:
        assert "encaja por su solapamiento" in text


def test_weighting_note_renders_when_present():
    tid = _valid_target()
    note = "Ordenado con una ponderación personalizada elegida por un curador de SECPHO."
    frag = RE.generate_html("person", tid, weighting_note=note)
    assert H.escape(note) in frag
    # and it is absent by default
    assert "ponderación personalizada" not in RE.generate_html("person", tid)

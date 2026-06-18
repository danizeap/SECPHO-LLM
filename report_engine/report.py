"""Assemble the full report content (structured), then hand it to the renderer."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import data_access as da
from . import render_docx
from . import render_html
from . import scoring
from . import sections as sec


@dataclass
class Report:
    title: str
    subject_name: str
    kind: str  # "person" | "company"
    entity_for_retos: str  # socio name used in the retos-emitted/applied wording
    indice: list
    intro: list
    ficha_label: str
    ficha: list
    contacts: list
    events_rec: list = field(default_factory=list)
    attended: list = field(default_factory=list)
    retos_rec: list = field(default_factory=list)
    retos_emit: list = field(default_factory=list)
    retos_appl: list = field(default_factory=list)
    # Optional LLM prose (filled in P2) and the curator's weighting note (set when a custom
    # weighting was applied). Both are model data so HTML and .docx render them identically.
    exec_summary: str = ""
    weighting_note: str = ""


def build_person_report(member_id: int, contacts: list | None = None) -> Report:
    """Build the person report model.

    `contacts`, when provided, is a pre-ranked list of matcher-shaped dicts
    (candidate_member_id / candidate_name / candidate_socio / candidate_role) — used so the
    in-app report honors the SAME ranking the chat shows (default or curator-tuned). When
    None, the deterministic default order from the matcher file is used (CLI/tests).
    """
    p = da.get_person(member_id)
    if p is None:
        raise ValueError(f"No person with member_id {member_id}")
    name = da._clean(p.get("full_name"))
    socio = da._clean(p.get("socio"))
    profile = da.person_profile(p)
    attended = da.attended_for_person(p)
    contact_rows = contacts if contacts is not None else da.contacts_for_person(member_id)
    return Report(
        title=f"Informe de Valor y Oportunidades para {name}",
        subject_name=name,
        kind="person",
        entity_for_retos=socio,  # empty for a person with no socio -> reto subsections omitted
        indice=sec.INDICE,
        intro=sec.intro(name),
        ficha_label="Ficha del contacto",
        ficha=sec.ficha_person(p),
        contacts=sec.contactos(contact_rows, profile),
        events_rec=sec.eventos_recomendados(scoring.recommend_events(profile, attended)),
        attended=sec.eventos_asistidos(attended),
        retos_rec=sec.retos_recomendados(scoring.recommend_retos(profile)),
        retos_emit=sec.retos_from_df(da.retos_issued_by(socio)) if socio else [],
        retos_appl=sec.retos_from_df(da.retos_applied_by(socio)) if socio else [],
    )


def build_company_report(socio_name: str) -> Report:
    s = da.get_socio(socio_name)
    if s is None:
        raise ValueError(f"No socio named {socio_name!r}")
    name = da._clean(s.get("socio"))
    profile = da.socio_profile(name, s)
    attended = da.attended_for_socio(name)
    return Report(
        title=f"Informe de Valor y Oportunidades para {name}",
        subject_name=name,
        kind="company",
        entity_for_retos=name,
        indice=sec.INDICE,
        intro=sec.intro(name),
        ficha_label="Ficha de socio",
        ficha=sec.ficha_company(s, da.socio_aggregate_attributes(name)),
        contacts=sec.contactos(da.contacts_for_socio(name), profile),
        events_rec=sec.eventos_recomendados(scoring.recommend_events(profile, attended)),
        attended=sec.eventos_asistidos(attended),
        retos_rec=sec.retos_recomendados(scoring.recommend_retos(profile)),
        retos_emit=sec.retos_from_df(da.retos_issued_by(name)),
        retos_appl=sec.retos_from_df(da.retos_applied_by(name)),
    )


def _build(kind: str, ident, contacts=None, weighting_note: str = "", exec_summary: str = ""):
    """Build the report model for either kind, attaching optional curator weighting note
    and LLM executive summary (both empty by default)."""
    if kind == "person":
        report = build_person_report(int(ident), contacts=contacts)
    elif kind == "company":
        report = build_company_report(str(ident))  # company reports are default-weighting
    else:
        raise ValueError("kind must be 'person' or 'company'")
    report.weighting_note = weighting_note or ""
    report.exec_summary = exec_summary or ""
    return report


def generate(kind: str, ident, out_path: str) -> str:
    """Build and write a report .docx. `ident` is a member_id (person) or socio name (company)."""
    render_docx.render(_build(kind, ident)).save(out_path)
    return out_path


def generate_html(kind: str, ident, contacts=None, weighting_note: str = "", exec_summary: str = "") -> str:
    """Build a report and return it as an HTML fragment for the in-chat preview (no LLM here;
    prose slots are filled by the caller). Identical content to `generate_bytes`."""
    return render_html.render(_build(kind, ident, contacts, weighting_note, exec_summary))


def render_html_of(report) -> str:
    """Render an already-built (and possibly prose-filled) report model to an HTML fragment."""
    return render_html.render(report)


def render_docx_bytes_of(report) -> tuple[bytes, str]:
    """Render an already-built report model to (.docx bytes, filename). Same model -> identical
    to `render_html_of`, so the in-chat preview and the download never diverge."""
    import io

    buf = io.BytesIO()
    render_docx.render(report).save(buf)
    return buf.getvalue(), _safe_filename(report.subject_name)


def _safe_filename(name: str) -> str:
    import re
    import unicodedata

    ascii_name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_name).strip("_") or "informe"
    return f"Informe_{slug}.docx"


def generate_bytes(kind: str, ident, contacts=None, weighting_note: str = "", exec_summary: str = "") -> tuple[bytes, str]:
    """Build a report in memory and return (.docx bytes, suggested filename). No disk write.

    `contacts`/`weighting_note`/`exec_summary` let the app render the SAME tuned/narrated report
    it showed in chat, so the download matches the on-screen preview exactly."""
    import io

    report = _build(kind, ident, contacts, weighting_note, exec_summary)
    buf = io.BytesIO()
    render_docx.render(report).save(buf)
    return buf.getvalue(), _safe_filename(report.subject_name)

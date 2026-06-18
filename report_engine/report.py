"""Assemble the full report content (structured), then hand it to the renderer."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import data_access as da
from . import render_docx
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


def build_person_report(member_id: int) -> Report:
    p = da.get_person(member_id)
    if p is None:
        raise ValueError(f"No person with member_id {member_id}")
    name = da._clean(p.get("full_name"))
    socio = da._clean(p.get("socio"))
    profile = da.person_profile(p)
    attended = da.attended_for_person(p)
    return Report(
        title=f"Informe de Valor y Oportunidades para {name}",
        subject_name=name,
        kind="person",
        entity_for_retos=socio,  # empty for a person with no socio -> reto subsections omitted
        indice=sec.INDICE,
        intro=sec.intro(name),
        ficha_label="Ficha del contacto",
        ficha=sec.ficha_person(p),
        contacts=sec.contactos(da.contacts_for_person(member_id), profile),
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


def generate(kind: str, ident, out_path: str) -> str:
    """Build and write a report .docx. `ident` is a member_id (person) or socio name (company)."""
    if kind == "person":
        report = build_person_report(int(ident))
    elif kind == "company":
        report = build_company_report(str(ident))
    else:
        raise ValueError("kind must be 'person' or 'company'")
    render_docx.render(report).save(out_path)
    return out_path

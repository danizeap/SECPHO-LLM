"""Deterministic builders for each report section: data -> display-ready content.

No rendering and no LLM here. Cleans the matcher's evidence (shared parent
technologies/sectors/ámbitos, recomputed from members and matched by canonical key),
formats Spanish dates day-first, and shapes events/retos rows for the renderer.
"""
from __future__ import annotations

import pandas as pd

from . import data_access as da

# Índice reflects the sections actually rendered. Section 6 (Proyectos) is added
# once the projects data source is available.
INDICE = [
    "1. Introducción",
    "2. Resumen de datos",
    "3. Contactos recomendados",
    "4. Eventos y actividades",
    "5. Retos tecnológicos",
]

_MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def format_date_es(value, unknown: str = "Fecha no disponible") -> str:
    if value is None:
        return unknown
    try:
        ts = value if isinstance(value, pd.Timestamp) else pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(ts):
            return unknown
        return f"{ts.day} de {_MESES[ts.month]} de {ts.year}"
    except Exception:
        return unknown


# --------------------------------------------------------------------------- #
# 1. Introducción
# --------------------------------------------------------------------------- #
def intro(name: str) -> list[str]:
    return [
        f"Este informe tiene como objetivo poner en valor la participación de {name} "
        "en el ecosistema SECPHO, destacando tanto su participación como las "
        "oportunidades que pueden surgir dentro del ecosistema.",
        "Se recogen recomendaciones de potenciales contactos, así como eventos o "
        "actividades y retos tecnológicos, tanto pasados como futuros, alineados con "
        "sus áreas de interés.",
    ]


# --------------------------------------------------------------------------- #
# 2. Resumen de datos (Ficha)
# --------------------------------------------------------------------------- #
def ficha_person(p: dict) -> list[tuple[str, str]]:
    g = lambda k: da._clean(p.get(k)) or da.NA
    return [
        ("Nombre", g("full_name")),
        ("Empresa", g("socio")),
        ("Función", g("role_function")),
        ("Cargo", g("role_title")),
        ("Provincia profesional", g("province")),
        ("Tecnologías", da.clean_list(p.get("technology_parents")) or da.NA),
        ("Sectores", da.clean_list(p.get("sector_parents")) or da.NA),
        ("Ámbitos", da.clean_list(p.get("ambitos")) or da.NA),
    ]


def ficha_company(s: dict, agg: dict) -> list[tuple[str, str]]:
    g = lambda k: da._clean(s.get(k)) or da.NA
    return [
        ("Socio", g("socio")),
        ("Tipo de empresa", g("company_type")),
        ("Tipo de socio", g("member_type")),
        ("Público o privado", g("public_private")),
        ("Cadena de valor", da.clean_list(s.get("value_chain")) or da.NA),
        ("Provincia", g("province")),
        ("Readiness", g("readiness_label")),
        ("Tecnologías", agg.get("technologies") or da.NA),
        ("Sectores", agg.get("sectors") or da.NA),
        ("Ámbitos", agg.get("ambitos") or da.NA),
    ]


# --------------------------------------------------------------------------- #
# 3. Contactos recomendados (the matchmaker)
# --------------------------------------------------------------------------- #
def _shared_from_members(target_set: set, candidate_member_id, col: str, limit: int = 8) -> str:
    """Clean shared items = target_set ∩ candidate's own list, matched by canonical key.

    Recomputed from members so the evidence is clean and consistently cased. The
    matcher still decides the ranking; this only explains it.
    """
    if not candidate_member_id or not target_set:
        return ""
    try:
        cand = da.get_person(int(candidate_member_id))
    except (TypeError, ValueError):
        return ""
    if not cand:
        return ""
    items = [it for it in da.list_items(cand.get(col)) if da._canon(it) in target_set]
    return da.SEP.join(items[:limit])


def _clean_location(value) -> str:
    """Matcher location string -> short Spanish phrase ('same municipality: X' -> 'misma localidad: X')."""
    s = da._clean(value)
    if not s:
        return ""
    low = s.lower()
    if low.startswith("same municipality:"):
        return "misma localidad: " + s.split(":", 1)[1].strip()
    if low.startswith("same province:"):
        return "misma provincia: " + s.split(":", 1)[1].strip()
    if low.startswith("same country:"):
        return "mismo país: " + s.split(":", 1)[1].strip()
    return s


def _clean_needs(value, limit: int = 4) -> str:
    """Matcher needs string ('cat: detail | detail | cat2: detail') -> the shared need CATEGORIES.

    The feed flattens 'category: details' pipe-joined; we keep the segments that carry a category
    (the part before ':'), de-duplicate, and cap — that is the meaningful 'what you both need'.
    """
    s = da._clean(value)
    if not s:
        return ""
    seen: set[str] = set()
    cats: list[str] = []
    for seg in s.split("|"):
        seg = seg.strip()
        if ":" in seg:
            cat = seg.split(":", 1)[0].strip()
            key = da._canon(cat)
            if cat and key not in seen:
                seen.add(key)
                cats.append(cat)
    return da.SEP.join(cats[:limit])


def contactos(contacts: list[dict], profile: dict) -> list[dict]:
    out = []
    for c in contacts:
        cid = c.get("candidate_member_id")
        out.append(
            {
                "candidate_member_id": cid,
                "name": da._clean(c.get("candidate_name")),
                "socio": da._clean(c.get("candidate_socio")),
                "role": da._clean(c.get("candidate_role")),
                "shared_tech": _shared_from_members(profile["tech"], cid, "technology_parents"),
                "shared_sectors": _shared_from_members(profile["sectors"], cid, "sector_parents"),
                "shared_ambitos": _shared_from_members(profile["ambitos"], cid, "ambitos"),
                # Professional drivers from the matcher row (what actually ranks them): the shared
                # needs and same-location signal. These are the substance the rationale leads with.
                "shared_needs": _clean_needs(c.get("shared_needs")),
                "shared_location": _clean_location(c.get("shared_location")),
                # Benign personal-affinity overlap (icebreakers). Sensitive fields are never read.
                "shared_hobbies": _shared_from_members(profile.get("hobbies", set()), cid, "hobbies"),
                "shared_sports": _shared_from_members(profile.get("sports", set()), cid, "sports"),
                "shared_languages": _shared_from_members(profile.get("languages", set()), cid, "languages"),
                "shared_university": _shared_from_members(profile.get("university", set()), cid, "university"),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# 4. Eventos y actividades
# --------------------------------------------------------------------------- #
def eventos_recomendados(events_rec: list[dict]) -> list[dict]:
    out = []
    for e in events_rec:
        out.append(
            {
                "title": e["title"],
                "score": e["score"],
                "date": format_date_es(e.get("date")),
                "technologies": e.get("technologies") or da.NA,
                "sectors": e.get("sectors") or da.NA,
                "ambitos": e.get("ambitos") or da.NA,
                "location": e.get("location") or da.NA,
            }
        )
    return out


def eventos_asistidos(attended: list[dict]) -> list[dict]:
    out = []
    for a in attended:
        item = {"title": a["title"], "date": format_date_es(a.get("date"))}
        if a.get("attendees"):
            item["attendees"] = a["attendees"]
        out.append(item)
    return out


# --------------------------------------------------------------------------- #
# 5. Retos tecnológicos
# --------------------------------------------------------------------------- #
def retos_recomendados(retos_rec: list[dict]) -> list[dict]:
    out = []
    for r in retos_rec:
        out.append(
            {
                "number": r.get("number"),
                "title": r.get("title"),
                "description": r.get("description"),
                "sectors": r.get("sectors") or da.NA,
                "issuer": r.get("issuer") or da.NA,
                "applicants": r.get("applicants") or da.NA,
                "closing": format_date_es(r.get("closing")),
            }
        )
    return out


def retos_from_df(df: pd.DataFrame, limit: int = 8) -> list[dict]:
    if not df.empty and "closing" in df.columns:
        df = df.sort_values("closing", ascending=False, na_position="last")
    out = []
    for _, r in df.head(limit).iterrows():
        out.append(
            {
                "number": da._clean(r.get("reto_number")),
                "title": da._clean(r.get("title")),
                "sectors": da.clean_list(r.get("sectors")) or da.NA,
                "issuer": da.clean_list(r.get("issuing_entities")) or da.NA,
                "applicants": da.clean_list(r.get("applying_entities")) or da.NA,
                "closing": format_date_es(r.get("closing")),
            }
        )
    return out

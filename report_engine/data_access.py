"""Read-only access to the project's normalized data for report generation.

Loads only what the report needs, from the same CSVs the rest of the system uses.
Text is normalized at the edge (HTML entities unescaped, internal whitespace
collapsed, pipe-lists split, vocabulary canonicalized for cross-source matching);
dates are parsed robustly. Nothing is mutated or written here.
"""
from __future__ import annotations

import html
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED = BASE_DIR / "data" / "processed"
OUTPUTS = BASE_DIR / "recommendation_engine" / "outputs"

NA = "N/D"
SEP = " · "  # list display separator (unambiguous vs the comma inside compound ámbitos)
_FILE_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_ALL_TECH = {"todas", "todos"}
# Ámbitos whose names legitimately contain a comma, so comma-splitting must keep them whole.
_COMPOUND_TERMS = ("New Space, defensa y seguridad", "Agricultura, bosques y océanos")
# Canonical aliases for the few parent labels that differ in spelling between the
# member directory and the events/retos feeds (after accent-stripping + '&'->'y').
_ALIASES = {
    "sistemas comunicacion y transmision datos": "sistemas de comunicacion y transmision de datos",
    "telecomunicaciones y ciberseguridad": "telecomunicaciones",
}


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def _clean(value) -> str:
    """A single cell -> clean string ('' for NaN/None/'nan'); collapses internal whitespace."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = re.sub(r"\s+", " ", html.unescape(str(value))).strip()
    return "" if text.lower() == "nan" else text


def list_items(value) -> list[str]:
    """Pipe-separated cell -> ordered, de-duplicated list of display items (compounds intact)."""
    text = _clean(value)
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for part in (p.strip() for p in re.split(r"[|]", text)):
        if part and part.lower() not in seen:
            seen.add(part.lower())
            out.append(part)
    return out


def clean_list(value, join: str = SEP) -> str:
    """Pipe-separated list cell -> de-duplicated, separator-joined display string."""
    return join.join(list_items(value))


def _canon(item: str) -> str:
    """Canonical key for cross-source matching: lowercase, '&'->'y', accent-stripped, aliased."""
    s = item.strip().lower().replace("&", "y")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s).strip()
    return _ALIASES.get(s, s)


def _split_set(value) -> set[str]:
    """Member cell (pipe-separated) -> set of canonical keys (compounds intact)."""
    return {_canon(it) for it in list_items(value)}


def _split_events(value) -> set[str]:
    """Event/reto cell (comma- or pipe-separated) -> set of canonical keys, keeping the
    comma-containing compound ámbitos intact for correct overlap."""
    text = _clean(value)
    if not text:
        return set()
    placeholders: dict[str, str] = {}
    for i, term in enumerate(_COMPOUND_TERMS):
        ph = f"\x00{i}\x00"
        text = re.sub(re.escape(term), ph, text, flags=re.IGNORECASE)
        placeholders[ph] = term
    out: set[str] = set()
    for part in re.split(r"[|,]", text):
        p = part.strip()
        for ph, term in placeholders.items():
            if ph in p:
                p = p.replace(ph, term)
        if p:
            out.add(_canon(p))
    return out


# --------------------------------------------------------------------------- #
# Core tables: members, socios, matches
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def members() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "members_normalized.csv", encoding="utf-8")


@lru_cache(maxsize=1)
def socios() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "socios_normalized.csv", encoding="utf-8")
    readiness = pd.read_csv(PROCESSED / "official_socios_readiness.csv", encoding="utf-8")
    readiness = readiness[["socio", "readiness_label", "readiness_score"]]
    return df.merge(readiness, on="socio", how="left")


@lru_cache(maxsize=1)
def matches() -> pd.DataFrame:
    return pd.read_csv(OUTPUTS / "people_matches_v1.csv", encoding="utf-8")


def get_person(member_id: int) -> dict | None:
    df = members()
    row = df[df["member_id"] == int(member_id)]
    return None if row.empty else row.iloc[0].to_dict()


def get_socio(name: str) -> dict | None:
    df = socios()
    key = str(name).strip().lower()
    row = df[df["socio"].astype(str).str.lower() == key]
    if row.empty:
        row = df[df["socio_key"].astype(str) == key.replace(" ", "")]
    return None if row.empty else row.iloc[0].to_dict()


def _socio_member_ids(socio_name: str) -> set[int]:
    mem = members()
    sm = mem[mem["socio"].astype(str).str.lower() == str(socio_name).strip().lower()]
    return {int(x) for x in sm["member_id"].tolist()}


# --------------------------------------------------------------------------- #
# Contacts (the matchmaker output) — stable order, faithful to the matcher
# --------------------------------------------------------------------------- #
def contacts_for_person(member_id: int, top_n: int = 5) -> list[dict]:
    df = matches()
    rows = df[df["target_member_id"] == int(member_id)]
    if rows.empty:
        return []
    rows = rows.sort_values("final_score", ascending=False, kind="stable").head(top_n)
    return rows.to_dict("records")


def contacts_for_socio(socio_name: str, top_n: int = 5) -> list[dict]:
    ids = _socio_member_ids(socio_name)
    if not ids:
        return []
    df = matches()
    rows = df[df["target_member_id"].isin(ids)]
    rows = rows[~rows["candidate_member_id"].isin(ids)]
    if rows.empty:
        return []
    rows = rows.sort_values("final_score", ascending=False, kind="stable")
    rows = rows.drop_duplicates(subset=["candidate_member_id"], keep="first").head(top_n)
    return rows.to_dict("records")


# --------------------------------------------------------------------------- #
# Profiles (for event/reto scoring)
# --------------------------------------------------------------------------- #
def person_profile(person: dict) -> dict:
    return {
        "tech": _split_set(person.get("technology_parents")),
        "sectors": _split_set(person.get("sector_parents")),
        "ambitos": _split_set(person.get("ambitos")),
        "province": _clean(person.get("province")).lower(),
        "text": _clean(person.get("profile_text")) or _clean(person.get("full_name")),
    }


def socio_profile(socio_name: str, socio_row: dict | None = None) -> dict:
    mem = members()
    sm = mem[mem["socio"].astype(str).str.lower() == str(socio_name).strip().lower()]
    tech: set[str] = set()
    sectors: set[str] = set()
    ambitos: set[str] = set()
    for _, r in sm.iterrows():
        tech |= _split_set(r.get("technology_parents"))
        sectors |= _split_set(r.get("sector_parents"))
        ambitos |= _split_set(r.get("ambitos"))
    province = _clean((socio_row or {}).get("province")).lower()
    text = _clean((socio_row or {}).get("profile_text")) or socio_name
    return {"tech": tech, "sectors": sectors, "ambitos": ambitos, "province": province, "text": text}


def socio_aggregate_attributes(socio_name: str) -> dict:
    """Display strings (union of the socio's members' tech/sectors/ámbitos), original casing."""
    mem = members()
    sm = mem[mem["socio"].astype(str).str.lower() == str(socio_name).strip().lower()]

    def disp(col: str) -> str:
        seen: set[str] = set()
        out: list[str] = []
        for cell in sm[col].dropna().tolist():
            for item in list_items(cell):
                if item.lower() not in seen:
                    seen.add(item.lower())
                    out.append(item)
        return SEP.join(out)

    return {"technologies": disp("technology_parents"), "sectors": disp("sector_parents"), "ambitos": disp("ambitos")}


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def events() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "events_normalized.csv", encoding="utf-8")
    df["date"] = pd.to_datetime(df["event_date"], dayfirst=True, errors="coerce")
    return df


def future_events(today: pd.Timestamp | None = None) -> pd.DataFrame:
    df = events()
    ref = pd.Timestamp(today).normalize() if today is not None else pd.Timestamp.today().normalize()
    return df[df["date"].notna() & (df["date"] > ref)].copy()


@lru_cache(maxsize=1)
def _event_date_by_title() -> dict:
    """Map (lowercased) event title -> real event date, from the canonical events table."""
    out: dict[str, pd.Timestamp] = {}
    for _, r in events().iterrows():
        title = _clean(r.get("title")).lower()
        date = r.get("date")
        if title and pd.notna(date) and title not in out:
            out[title] = date
    return out


@lru_cache(maxsize=1)
def registrations() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "event_registrations_matched.csv", encoding="utf-8")


def _attended_rows(rows: pd.DataFrame, with_attendees: bool = False) -> list[dict]:
    """Distinct attended events with their REAL date (from the events table), newest first.

    The registration filename only encodes the export timestamp, not the event date, so
    we never display it; titles that aren't in the events table show no date.
    """
    if rows.empty:
        return []
    g = rows.copy()
    g["title"] = g["event_title_from_file"].map(_clean)
    g = g[g["title"] != ""]
    if g.empty:
        return []
    if with_attendees:
        grouped = g.groupby("title", as_index=False).agg(
            attendees=("matched_person_name", lambda s: SEP.join(sorted({_clean(x) for x in s if _clean(x)})))
        )
    else:
        grouped = g.drop_duplicates("title")[["title"]]
    date_map = _event_date_by_title()
    items = []
    for _, r in grouped.iterrows():
        title = r["title"]
        date = date_map.get(title.lower())
        item = {"title": title, "date": date if (date is not None and pd.notna(date)) else None}
        if with_attendees:
            item["attendees"] = r.get("attendees", "")
        items.append(item)
    dated = sorted([i for i in items if i["date"] is not None], key=lambda x: x["date"], reverse=True)
    undated = [i for i in items if i["date"] is None]
    return dated + undated


def attended_for_person(person: dict) -> list[dict]:
    df = registrations()
    email = _clean(person.get("email")).lower()
    name = _clean(person.get("full_name")).lower()
    socio = _clean(person.get("socio")).lower()
    if email:  # email is unique; prefer it and never fall back to ambiguous name matching
        mask = df["matched_email"].astype(str).str.lower() == email
    elif name:
        mask = df["matched_person_name"].astype(str).str.lower() == name
        if socio:  # disambiguate same-name members by their socio
            mask &= df["matched_socio"].astype(str).str.lower() == socio
    else:
        return []
    return _attended_rows(df[mask])


def attended_for_socio(socio_name: str) -> list[dict]:
    df = registrations()
    key = str(socio_name).strip().lower()
    mask = df["matched_socio"].astype(str).str.lower() == key
    return _attended_rows(df[mask], with_attendees=True)


# --------------------------------------------------------------------------- #
# Retos
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def retos() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED / "retos_normalized.csv", encoding="utf-8")
    df["closing"] = pd.to_datetime(df["closing_date"], dayfirst=True, errors="coerce")
    return df


def active_retos(today: pd.Timestamp | None = None) -> pd.DataFrame:
    df = retos()
    ref = pd.Timestamp(today).normalize() if today is not None else pd.Timestamp.today().normalize()
    return df[df["closing"].notna() & (df["closing"] > ref)].copy()


def _entity_tokens(cell) -> list[str]:
    """Pipe-delimited entity cell -> canonical entity names, parenthetical qualifiers removed."""
    out = []
    for tok in re.split(r"[|]", str(cell)):
        base = re.sub(r"\s*\([^)]*\)\s*", " ", tok).strip().lower()
        base = re.sub(r"\s+", " ", base)
        if base:
            out.append(base)
    return out


def _retos_where_entity(column: str, socio_name: str) -> pd.DataFrame:
    """Retos where `socio_name` is a whole-word entity token (not a naive substring).

    Avoids fabricated attributions like 'Roca' matching 'ProCareLight'. Whole-word
    matching still catches legitimate variants ('Repsol' in 'Repsol S.A.').
    """
    df = retos()
    key = str(socio_name).strip().lower()
    key = re.sub(r"\s+", " ", key)
    if not key:
        return df.iloc[0:0]
    pat = re.compile(r"(?<![\w])" + re.escape(key) + r"(?![\w])")

    def matches_entity(cell) -> bool:
        return any(pat.search(tok) for tok in _entity_tokens(cell))

    return df[df[column].astype(str).apply(matches_entity)].copy()


def retos_issued_by(socio_name: str) -> pd.DataFrame:
    return _retos_where_entity("issuing_entities", socio_name)


def retos_applied_by(socio_name: str) -> pd.DataFrame:
    return _retos_where_entity("applying_entities", socio_name)

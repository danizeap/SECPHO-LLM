"""Zero-copy live data layer.

Fetches SECPHO's WordPress `reports/v1` endpoints into memory, normalizes them into the canonical
shapes the app/LLM already query, and persists NOTHING. WordPress stays the system of record; this
module is a stateless processor. It is OPT-IN: enabled only when the ``SECPHO_LIVE_DATA`` flag is
truthy AND a token (``SECPHO_API_AUTH_TOKEN``) is configured — so a token sitting in ``.env`` can
never accidentally trigger real network calls in tests or local runs; otherwise the app keeps using
its CSV snapshot. The token is read from the environment, used server-side only, and is never logged,
returned, or written to disk.

Phase 1 covers three low-sensitivity sources (retos, proyectos, casos-éxito). More sources, the
background refresher, change-diff feed, and access model arrive in later phases.
"""
from __future__ import annotations

import ast
import concurrent.futures
import datetime
import html
import os
import re

import pandas as pd
import requests

API_BASE = os.getenv("SECPHO_REPORTS_API_BASE", "https://secpho.org/wp-json/reports/v1").rstrip("/")
FETCH_TIMEOUT = int(os.getenv("SECPHO_REPORTS_TIMEOUT", "25"))

# source -> ISO-8601 UTC timestamp of the last successful live load (freshness, surfaced to the user)
_FRESHNESS: dict[str, str] = {}


def _token() -> str | None:
    return os.getenv("SECPHO_API_AUTH_TOKEN") or os.getenv("SECPHO_REPORTS_API_TOKEN") or None


def live_enabled() -> bool:
    """Opt-in: requires the SECPHO_LIVE_DATA flag to be truthy AND a token to be configured. Off by
    default so a token in .env can't accidentally enable network calls; the app falls back to CSV."""
    flag = str(os.getenv("SECPHO_LIVE_DATA", "")).strip().lower() in ("1", "true", "yes", "on")
    return flag and bool(_token())


# --------------------------------------------------------------------------- #
# Fetch + small helpers
# --------------------------------------------------------------------------- #
def _fetch_json(endpoint: str, extra: str = ""):
    tok = _token()
    if not tok:
        return None
    resp = requests.get(f"{API_BASE}/{endpoint}?auth={tok}{extra}", timeout=FETCH_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _records(raw):
    """WP endpoints arrive either as a list of records or a dict keyed by id. Normalize to a list
    of (id_or_None, record_dict)."""
    if isinstance(raw, dict):
        return [(str(k), v) for k, v in raw.items() if isinstance(v, dict)]
    if isinstance(raw, list):
        return [(None, v) for v in raw if isinstance(v, dict)]
    return []


def _strip_html(value) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean(value) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def _as_list(value):
    """A Python-repr list/dict string (e.g. "['Fotónica', 'IA']") -> the parsed object; '' -> []."""
    s = str(value or "").strip()
    if not s:
        return []
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s


# --------------------------------------------------------------------------- #
# Normalizers (pure: raw JSON -> canonical DataFrame). No network, no LLM.
# --------------------------------------------------------------------------- #
def normalize_retos(raw) -> pd.DataFrame:
    """Live retos JSON -> the canonical retos schema (matches retos_normalized.csv)."""
    rows = []
    for rid, r in _records(raw):
        desc = _strip_html(r.get("Descripción"))
        rows.append({
            "reto_id": rid,
            "reto_number": _clean(r.get("Num. reto")),
            "title": _clean(r.get("Título")),
            "description_clean": desc,
            "sectors": _clean(r.get("Sector/es")),
            "issuing_entities": _clean(r.get("Entidad emisora")),
            "submission_date": _clean(r.get("Fecha envío")),
            "closing_date": _clean(r.get("Fecha cierre")),
            "applying_entities": _clean(r.get("Entidades que aplican")),
            "connection_type": _clean(r.get("Tipo de conexión")),
            "creates_project": _clean(r.get("¿Surge proyecto?")),
            "beneficiary_socio": _clean(r.get("Socio beneficiado")),
            "reto_text": desc,
        })
    return pd.DataFrame(rows)


def normalize_proyectos(raw) -> pd.DataFrame:
    """Live proyectos JSON -> a canonical projects table (new entity)."""
    rows = []
    for rid, r in _records(raw):
        rows.append({
            "proyecto_id": rid or r.get("ID"),
            "acronym": _clean(r.get("Acrónimo")),
            "title": _clean(r.get("Título idea/proyecto")),
            "start": _clean(r.get("Inicio")),
            "end": _clean(r.get("Final")),
            "funding_source": _clean(r.get("Origen Fondos")),
            "funding_program": _clean(r.get("Programa financiación")),
            "partners": _clean(r.get("Partners")),
            "technologies": _clean(r.get("Tecnologías")),
            "sectors": _clean(r.get("Sectores")),
            "ambitos": _clean(r.get("Ámbitos")),
            "type": _clean(r.get("Tipo")),
            "stage": _clean(r.get("Etapa")),
            "size": _clean(r.get("Tamaño")),
            "lead": _clean(r.get("Responsable")),
            "progress": _clean(r.get("Progreso (%)")),
            "budget_total": _clean(r.get("Presupuesto total (€)")),
            "aid_received": _clean(r.get("Ayuda recibida (€)")),
            "capital": _clean(r.get("Capital inyectado (€)")),
            "impact": _strip_html(r.get("Impacto")),
            "url": _clean(r.get("URL")),
        })
    return pd.DataFrame(rows)


def normalize_casos(raw) -> pd.DataFrame:
    """Live casos-éxito JSON -> a canonical success-cases table (new entity; text-rich)."""
    rows = []
    for _rid, r in _records(raw):
        rows.append({
            "title": _clean(r.get("Título")),
            "summary": _strip_html(r.get("Resumen")),
            "year": _clean(r.get("Año")),
            "aei": _clean(r.get("AEI")),
            "eu": _clean(r.get("EU")),
            "technologies": _as_list(r.get("Tecnologías")),
            "ambitos": _as_list(r.get("Ámbitos")),
            "ods": _as_list(r.get("ODS")),
            "sectors": _as_list(r.get("Sectores")),
            "entities": _as_list(r.get("Entidades")),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Registry + parallel loader
# --------------------------------------------------------------------------- #
# name -> (endpoint, extra query, normalizer)
SOURCES = {
    "retos": ("retos", "", normalize_retos),
    "proyectos": ("proyectos", "", normalize_proyectos),
    "casos_exito": ("casos-exito", "", normalize_casos),
}


def load_source(name: str) -> pd.DataFrame | None:
    """Fetch + normalize one source live. Returns None when live is disabled (no token)."""
    endpoint, extra, normalizer = SOURCES[name]
    raw = _fetch_json(endpoint, extra)
    if raw is None:
        return None
    df = normalizer(raw)
    _FRESHNESS[name] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return df


def load_all(names: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Parallel live load. Returns {name: DataFrame} for sources that loaded; a source that fails
    or is disabled is simply absent, so the caller falls back to its CSV/empty default. A failing
    source never raises out of here and never logs the token or any values."""
    if not live_enabled():
        return {}
    names = names or list(SOURCES)
    out: dict[str, pd.DataFrame] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, max(1, len(names)))) as ex:
        futures = {ex.submit(load_source, n): n for n in names}
        for fut in concurrent.futures.as_completed(futures):
            name = futures[fut]
            try:
                df = fut.result()
                if df is not None:
                    out[name] = df
            except Exception:
                pass  # leave absent; caller falls back
    return out


def freshness() -> dict[str, str]:
    """source -> ISO-8601 UTC timestamp of last successful live load (for freshness stamps)."""
    return dict(_FRESHNESS)

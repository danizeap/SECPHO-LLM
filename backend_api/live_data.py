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
import collections
import concurrent.futures
import datetime
import hashlib
import html
import os
import re
import threading
import time

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
def _fetch_json(endpoint: str, extra: str = "", timeout: int | None = None):
    tok = _token()
    if not tok:
        return None
    resp = requests.get(f"{API_BASE}/{endpoint}?auth={tok}{extra}", timeout=timeout or FETCH_TIMEOUT)
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


def _join_list(value) -> str:
    """A JSON list field (e.g. Estado/Concepto) -> a clean comma-joined string; scalar -> cleaned."""
    if isinstance(value, list):
        return ", ".join(_clean(x) for x in value if _clean(x))
    return _clean(value)


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
def normalize_actividades(raw) -> pd.DataFrame:
    """Live actividades JSON -> a canonical activity log (new entity; the engagement signal). Adds a
    synthetic stable `activity_id` (content hash) since the source has no id, for change detection."""
    rows = []
    for _rid, r in _records(raw):
        socio = _clean(r.get("Socio"))
        date = _clean(r.get("Fecha"))
        atype = _clean(r.get("Tipo"))
        author = _clean(r.get("Autor"))
        desc = _strip_html(r.get("Descripción"))
        aid = hashlib.sha1(f"{socio}|{date}|{atype}|{author}|{desc}".encode("utf-8", "replace")).hexdigest()[:16]
        rows.append({
            "activity_id": aid,
            "socio": socio,
            "socio_type": _clean(r.get("Tipo socio")),
            "date": date,
            "author": author,
            "qn": _clean(r.get("[QN]")),
            "type": atype,
            "description": desc,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Financial normalizers (🔴 sensitive). Loaded into RAM like the rest; EXPOSURE is gated at the tool
# layer behind `data.financiero`. Zero-copy: never persisted. Field names verified against the live
# reports/v1 endpoints (schema-only probe, June 2026).
# --------------------------------------------------------------------------- #
def normalize_negocio_financiero(raw) -> pd.DataFrame:
    """Live datosnegocio JSON -> the FINANCIAL view of each socio: turnover + investment. Key: socio."""
    rows = []
    for _rid, r in _records(raw):
        rows.append({
            "socio": _clean(r.get("Socio")),
            "revenue": _clean(r.get("Cifra de negocio")),
            "investment_received": _clean(r.get("Inversion recibida")),
            "investment_sought": _clean(r.get("Inversion buscada")),
            "employees": _clean(r.get("Num. de empleados")),
            "exportation": _clean(r.get("Exportación")),
            "last_updated": _clean(r.get("Fecha ult. act.")),
        })
    return pd.DataFrame(rows)


_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def normalize_cuotas(raw) -> pd.DataFrame:
    """Live altasbajas JSON -> membership economics: cuota amount, join/leave dates, churn reason.
    Key: altabaja_id (the source's dict id). Also the raw signal for the later health/churn slice.
    A socio counts as 'baja' (left) ONLY if 'Fecha de baja definitiva' is a real date — the source
    uses the literal 'No consta' (not recorded) for active members, so a non-empty value is NOT a
    leave."""
    rows = []
    for rid, r in _records(raw):
        leave = _clean(r.get("Fecha de baja definitiva"))
        left = bool(_DATE_RE.match(leave))
        rows.append({
            "altabaja_id": rid,
            "socio": _clean(r.get("Socio")),
            "company_type": _clean(r.get("Tipo de empresa")),
            "cuota_amount": _clean(r.get("Importe Cuota")),
            "join_date": _clean(r.get("Fecha de incorporación")),
            "welcome_date": _clean(r.get("Fecha de welcome")),
            "leave_request_date": _clean(r.get("Fecha solicitud baja")),
            "leave_date": leave,
            "churn_reason_type": _clean(r.get("Tipo motivo de baja")),
            "churn_reason": _clean(r.get("Descripción motivo")),
            "status": "baja" if left else "activo",
        })
    return pd.DataFrame(rows)


def normalize_invoices(raw) -> pd.DataFrame:
    """Live facturacion-total JSON -> the invoice/billing ledger per socio (status, due, paid,
    amount). Key: invoice_id (the source's dict id). Source for cuota/payment status + invoice lookups."""
    rows = []
    for rid, r in _records(raw):
        rows.append({
            "invoice_id": rid,
            "invoice_no": _clean(r.get("Número")),
            "socio": _clean(r.get("Socio")),
            "status": _join_list(r.get("Estado")),
            "concept": _join_list(r.get("Concepto")),
            "invoice_date": _clean(r.get("Fecha Factura")),
            "due_date": _clean(r.get("Vencimiento")),
            "payment_date": _clean(r.get("Fecha de pago")),
            "net": _clean(r.get("Neto")),
            "total": _clean(r.get("Total")),
        })
    return pd.DataFrame(rows)


def normalize_contributions(raw) -> pd.DataFrame:
    """Live financiacion JSON -> per-socio annual financial contribution history. Key: socio. The
    per-year figures are kept as a {year: amount} dict for trend aggregation."""
    rows = []
    for _rid, r in _records(raw):
        by_year = {
            k.replace("Finan. ", "").strip(): _clean(v)
            for k, v in r.items()
            if isinstance(k, str) and k.startswith("Finan. ")
        }
        rows.append({
            "socio": _clean(r.get("Socio")),
            "participation": _clean(r.get("Participación")),
            "ranking": _clean(r.get("Ranking")),
            "total_contribution": _clean(r.get("TOTAL")),
            "contributions_by_year": by_year,
        })
    return pd.DataFrame(rows)


# name -> (endpoint, extra query, normalizer)
SOURCES = {
    "retos": ("retos", "", normalize_retos),
    "proyectos": ("proyectos", "", normalize_proyectos),
    "casos_exito": ("casos-exito", "", normalize_casos),
    "actividades": ("actividades", "", normalize_actividades),
    # 🔴 financial sources — in RAM like the rest; exposure gated at the tool layer (data.financiero).
    "negocio_financiero": ("datosnegocio", "", normalize_negocio_financiero),
    "cuotas": ("altasbajas", "", normalize_cuotas),
    "invoices": ("facturacion-total", "", normalize_invoices),
    "contributions": ("financiacion", "", normalize_contributions),
}

# 🔴 sources whose data is sensitive (financial). Used to gate change-feed key samples (P5f-c) and to
# signal callers that exposure requires the data.financiero grant.
SENSITIVE_SOURCES = frozenset({"negocio_financiero", "cuotas", "invoices", "contributions"})

# Larger / slower financial endpoints that need a longer fetch timeout than the default.
SLOW_SOURCES = frozenset({"invoices", "contributions", "cuotas"})


def load_source(name: str) -> pd.DataFrame | None:
    """Fetch + normalize one source live. Returns None when live is disabled (no token)."""
    endpoint, extra, normalizer = SOURCES[name]
    raw = _fetch_json(endpoint, extra, timeout=60 if name in SLOW_SOURCES else None)
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


# --------------------------------------------------------------------------- #
# Refresher + in-RAM change-feed (Phase 2)
# --------------------------------------------------------------------------- #
# Per-source cadence (seconds). Default covers all; override per source to make it tiered. These are
# low-volatility reference sources, so hours is plenty.
DEFAULT_REFRESH_SECONDS = int(os.getenv("SECPHO_LIVE_REFRESH_SECONDS", "10800"))  # 3h
REFRESH_INTERVALS: dict[str, int] = {}
_TICK_SECONDS = int(os.getenv("SECPHO_LIVE_TICK_SECONDS", "60"))

# Stable record key per source for diffing (id where available, else a stable field).
KEY_COLUMNS = {
    "retos": "reto_id", "proyectos": "proyecto_id", "casos_exito": "title", "actividades": "activity_id",
    "negocio_financiero": "socio", "cuotas": "altabaja_id", "invoices": "invoice_id", "contributions": "socio",
}

_LAST: dict[str, pd.DataFrame] = {}          # previous pull per source (in RAM, for diffing)
_LAST_REFRESH: dict[str, float] = {}         # monotonic time of last refresh attempt (cadence)
_CHANGES: "collections.deque" = collections.deque(maxlen=int(os.getenv("SECPHO_LIVE_CHANGES_MAX", "200")))
_refresher_started = False


def _row_hash(rec: dict) -> str:
    payload = "|".join(f"{k}={rec[k]!r}" for k in sorted(rec))
    return hashlib.sha1(payload.encode("utf-8", "replace")).hexdigest()


def _index(df: pd.DataFrame | None, key: str) -> dict[str, str]:
    """key value -> row content hash, for one frame."""
    if df is None or df.empty or key not in df.columns:
        return {}
    return {str(rec.get(key, "")): _row_hash(rec) for rec in df.to_dict("records")}


def diff_frames(old_df, new_df, key: str) -> dict[str, list]:
    """Structural diff between two pulls of a source, by record key + content hash."""
    old, new = _index(old_df, key), _index(new_df, key)
    old_k, new_k = set(old), set(new)
    return {
        "added": sorted(new_k - old_k),
        "modified": sorted(k for k in (old_k & new_k) if old[k] != new[k]),
        "removed": sorted(old_k - new_k),
    }


def _change_entry(name: str, d: dict) -> dict:
    """Build a change-feed entry from a diff. For 🔴 SENSITIVE_SOURCES the bounded sample of changed
    key values is OMITTED (their key is the socio name / a financial record id) — only the counts are
    kept, so a surfaced feed can never reveal WHICH socios had financial changes to a non-granted
    caller. Non-sensitive sources keep the key sample for useful digests."""
    keys = {} if name in SENSITIVE_SOURCES else {k: v[:20] for k, v in d.items()}
    return {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": name,
        "added": len(d["added"]),
        "modified": len(d["modified"]),
        "removed": len(d["removed"]),
        "sensitive": name in SENSITIVE_SOURCES,
        "keys": keys,
    }


def _refresh_once(names: list[str] | None = None, apply_fn=None) -> list[dict]:
    """One refresh cycle for the given sources: load → diff vs the previous in-RAM pull → record any
    change → apply (swap into the app's view). The first pull of a source is the baseline (no change
    emitted). A failed source is skipped (stale-while-revalidate: the last-good view stays). Returns
    the change entries emitted this cycle. Persists nothing (everything is in RAM)."""
    names = names or list(SOURCES)
    emitted: list[dict] = []
    for name in names:
        _LAST_REFRESH[name] = time.monotonic()
        try:
            df = load_source(name)
        except Exception:
            df = None
        if df is None:
            continue  # stale-while-revalidate: keep the last-good view
        prev = _LAST.get(name)
        if prev is not None:
            d = diff_frames(prev, df, KEY_COLUMNS.get(name, ""))
            if d["added"] or d["modified"] or d["removed"]:
                entry = _change_entry(name, d)
                _CHANGES.append(entry)
                emitted.append(entry)
        _LAST[name] = df
        if apply_fn is not None:
            apply_fn(name, df)
    return emitted


def _due(name: str) -> bool:
    interval = REFRESH_INTERVALS.get(name, DEFAULT_REFRESH_SECONDS)
    last = _LAST_REFRESH.get(name)
    return last is None or (time.monotonic() - last) >= interval


def start_refresher(apply_fn=None, stop_event: "threading.Event | None" = None):
    """Start the background refresher (daemon): an immediate first load (baseline) then a periodic,
    per-source-cadenced re-pull with the in-RAM change-feed. No-op when live is disabled. Returns the
    stop Event (set it to stop) or None when disabled."""
    global _refresher_started
    if not live_enabled():
        return None
    ev = stop_event or threading.Event()

    def _loop():
        while not ev.is_set():
            due = [n for n in SOURCES if _due(n)]
            if due:
                try:
                    _refresh_once(due, apply_fn=apply_fn)
                except Exception:
                    pass  # best-effort; never logs token/values
            ev.wait(_TICK_SECONDS)

    threading.Thread(target=_loop, daemon=True, name="live-data-refresher").start()
    _refresher_started = True
    return ev


def changes(limit: int = 50) -> list[dict]:
    """Most-recent change-feed entries (in-RAM, bounded). Zero persistence."""
    items = list(_CHANGES)[-limit:]
    return list(reversed(items))

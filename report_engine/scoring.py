"""Deterministic scoring for event and reto recommendations.

Event scoring ports the IVO weighting onto our normalized data; reto scoring uses
TF-IDF cosine similarity (reusing the existing scikit-learn stack — no embeddings
dependency) plus sector overlap. No randomness and no LLM: the math decides.
"""
from __future__ import annotations

import pandas as pd

from . import data_access as da

EVENT_WEIGHTS = {
    "tec": 29.0, "sec": 15.0, "amb": 12.0, "prov": 22.0,
    "tec_hist": 10.0, "sec_hist": 7.0, "amb_hist": 5.0, "online": 22.0,
}


def _prop(event_set: set, profile_set: set) -> float:
    return len(event_set & profile_set) / len(event_set) if event_set else 0.0


def _date_or_none(value):
    return value if value is not None and pd.notna(value) else None


def history_attributes(attended: list[dict]) -> dict:
    """Union of tech/sectors/ámbitos across a person's attended events."""
    titles = {a["title"].lower() for a in attended if a.get("title")}
    out = {"tech": set(), "sectors": set(), "ambitos": set()}
    if not titles:
        return out
    ev = da.events()
    sub = ev[ev["title"].astype(str).str.lower().isin(titles)]
    for _, r in sub.iterrows():
        out["tech"] |= da._split_events(r.get("technologies"))
        out["sectors"] |= da._split_events(r.get("sectors"))
        out["ambitos"] |= da._split_events(r.get("ambitos"))
    return out


def _event_components(profile: dict, hist: dict, event_row) -> tuple[float, float]:
    """Return (topical_base, online_bonus). Topical = real overlap; online = flat convenience bonus."""
    ev_tech = da._split_events(event_row.get("technologies"))
    ev_sec = da._split_events(event_row.get("sectors"))
    ev_amb = da._split_events(event_row.get("ambitos"))
    ev_prov = da._clean(event_row.get("province")).lower()
    loc = (da._clean(event_row.get("location_type")) + " " + da._clean(event_row.get("city"))).lower()
    w = EVENT_WEIGHTS

    base = 0.0
    base += w["tec"] if ev_tech & da._ALL_TECH else _prop(ev_tech, profile["tech"]) * w["tec"]
    base += w["sec"] if ev_sec & da._ALL_TECH else _prop(ev_sec, profile["sectors"]) * w["sec"]
    base += _prop(ev_amb, profile["ambitos"]) * w["amb"]
    if profile["province"] and profile["province"] == ev_prov:
        base += w["prov"]
    base += _prop(ev_tech, hist["tech"]) * w["tec_hist"]
    base += _prop(ev_sec, hist["sectors"]) * w["sec_hist"]
    base += _prop(ev_amb, hist["ambitos"]) * w["amb_hist"]
    online_bonus = w["online"] if "online" in loc else 0.0
    return base, online_bonus


def score_event(profile: dict, hist: dict, event_row) -> float:
    base, online = _event_components(profile, hist, event_row)
    return round(min(base + online, 100.0), 1)


def recommend_events(profile: dict, attended: list[dict], top_n: int = 5) -> list[dict]:
    future = da.future_events()
    if future.empty:
        return []
    hist = history_attributes(attended)
    scored = []
    for _, ev in future.iterrows():
        base, online = _event_components(profile, hist, ev)
        if base <= 0:  # never recommend an event whose only relevance is the online convenience bonus
            continue
        scored.append((round(min(base + online, 100.0), 1), ev))
    scored.sort(key=lambda x: x[0], reverse=True)

    out = []
    for s, ev in scored[:top_n]:
        city = da._clean(ev.get("city"))
        loc_type = da._clean(ev.get("location_type"))
        location = f"{city} ({loc_type})" if (city and loc_type) else (city or loc_type or da.NA)
        out.append({
            "title": da._clean(ev.get("title")),
            "score": s,
            "date": _date_or_none(ev.get("date")),
            "technologies": da.clean_list(ev.get("technologies")) or da.NA,
            "sectors": da.clean_list(ev.get("sectors")) or da.NA,
            "ambitos": da.clean_list(ev.get("ambitos")) or da.NA,
            "location": location,
        })
    return out


def recommend_retos(profile: dict, top_n: int = 5) -> list[dict]:
    active = da.active_retos()
    if active.empty:
        return []
    texts = active["reto_text"].fillna("").astype(str).tolist()
    sims = [0.0] * len(texts)
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        corpus = [profile.get("text") or ""] + texts
        matrix = TfidfVectorizer(strip_accents="unicode", lowercase=True, max_features=5000).fit_transform(corpus)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()
    except (ImportError, ValueError):
        # optional dependency missing, or an empty/degenerate corpus -> fall back to sector overlap only
        pass

    scored = []
    for i, (_, reto) in enumerate(active.iterrows()):
        rsec = da._split_events(reto.get("sectors"))
        sec_overlap = (len(rsec & profile["sectors"]) / len(rsec)) if rsec else 0.0
        score = 0.5 * float(sims[i]) + 0.5 * sec_overlap
        scored.append((score, reto))
    scored.sort(key=lambda x: x[0], reverse=True)

    out = []
    for s, reto in scored[:top_n]:
        if s <= 0:
            continue
        out.append({
            "number": da._clean(reto.get("reto_number")),
            "title": da._clean(reto.get("title")),
            "description": da._clean(reto.get("description_clean")),
            "sectors": da.clean_list(reto.get("sectors")) or da.NA,
            "issuer": da.clean_list(reto.get("issuing_entities")) or da.NA,
            "applicants": da.clean_list(reto.get("applying_entities")) or da.NA,
            "closing": _date_or_none(reto.get("closing")),
            "score": round(float(s), 3),
        })
    return out

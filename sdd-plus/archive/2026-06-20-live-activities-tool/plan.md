# Plan

## Change

live-activities-tool (P3 activities slice)

## Approach

1. `live_data.py`: `normalize_actividades(raw)` → canonical fields (activity_id, socio, socio_type,
   date, author, qn, type, description; HTML stripped). Synthetic `activity_id` = sha1 of
   socio|date|type|author|description (stable key for the change-feed). Register in `SOURCES` and
   `KEY_COLUMNS["actividades"] = "activity_id"` (the refresher + change-feed pick it up automatically).
2. `mvp_web_app.py`: add `"actividades": pd.DataFrame()` to `load_data`; `list_activities(query, socio)`
   filters the in-memory table (socio substring + token search over socio/type/description/author),
   sorts most-recent-first (dayfirst dates), returns socio/date/type/author/description; + schema + dispatch.
3. Tests: normalizer (canonical cols, HTML stripped, key); tool (socio filter, recent-first, empty, registered).

## Files Expected To Change

- `backend_api/live_data.py`, `backend_api/mvp_web_app.py`, `tests/test_live_data.py`,
  `tests/test_projects_tool.py`, agentic-conversation delta.

## Risks

- Odd/variant date formats → `dayfirst=True, errors="coerce"` sorts robustly, no crash.
- 6k-row scan per query → trivial in pandas; bounded result (≤25).
- Member-activity sensitivity → 🟡 (not financial/PII); staff-queryable; revisit gating in P4.

## Rollback

Revert the `live_data.py`/`mvp_web_app.py` hunks + tests. Tool is inert when live is off.

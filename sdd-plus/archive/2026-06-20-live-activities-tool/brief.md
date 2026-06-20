# Brief

## Change

live-activities-tool (P3, activities slice)

## User Need

Make SECPHO's activity log (actividades, ~6,131 rows) queryable by the chat — the engagement signal
that powers the health/churn intelligence later, and a direct answer to "what has socio X done lately?".

## Problem

actividades wasn't ingested and the agent had no activities tool.

## Scope

In scope:
- `normalize_actividades` in `live_data.py` (+ registered in SOURCES, with a synthetic `activity_id`
  content-hash key for the change-feed, since the source has no id).
- `list_activities` deterministic tool (filter by socio and/or topic; most recent first) + schema + dispatch.
- Empty when the live layer is off.

Out of scope:
- The financial/PII sources + access model (P4); RAG; surfacing activities in any UI panel.

## Acceptance Criteria

- [x] actividades normalizes to a canonical activity log (HTML stripped; stable `activity_id`).
- [x] `list_activities` filters by socio/topic, returns most-recent-first, empty when off; registered tool.
- [x] Hermetic tests + live proof (6,131 rows; most recent dated today; 129 match "fotónica").
- [x] Full suite green.

## Impact Areas

- Backend: `live_data.normalize_actividades` + SOURCES/KEY_COLUMNS; `mvp_web_app.list_activities` + schema/dispatch; new DATA key.
- Frontend / API: none.
- AI/model behavior: thirteenth deterministic tool.
- Documentation: agentic-conversation delta.
- Operations/security: actividades is 🟡 (member activity, not financial/PII) → staff-queryable; nothing persisted; change-feed key is an opaque hash.

## Open Questions

- Whether activity descriptions warrant gating for some roles — revisit with the P4 access model if needed.

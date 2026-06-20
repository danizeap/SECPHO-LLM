# Tasks

## Change

live-activities-tool (P3 activities slice)

## Implementation

- [x] `normalize_actividades` + register in SOURCES + KEY_COLUMNS (synthetic activity_id).
- [x] `list_activities` fn (socio/topic filter, most-recent-first) + dispatch + schema + DATA key.
- [x] Tests: normalizer (canonical cols, HTML stripped, key); tool (socio filter, recent-first, empty, registered).
- [x] Live proof: 6,131 activities; most recent dated today; 129 match "fotónica"; tool registered (13 tools).
- [x] agentic-conversation delta + verify + verifier + sync + archive.
- [ ] Owner glance (when live is on): "qué ha hecho [socio] últimamente" → recent activity list.

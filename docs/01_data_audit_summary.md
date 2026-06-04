# SECPHO 01_Data_Audit Summary

## Module
01_Data_Audit

## Session goal
Audit the available SECPHO data sources, confirm which endpoints work, normalize the core tables, check joins between official socios and people/contact data, and define which recommendation signals are feasible for Phase 1.

## Scope decision
The Phase 1 recommendation universe is limited to official socios/companies from `datosnegocio`.

- Official socios are the canonical recommendation universe.
- Wider entities from contacts/subscribers are enrichment only, not primary recommendation targets.
- `datosnegocio` currently contains 192 official socios.

## Endpoint audit

| Endpoint | Rows | Columns |
|---|---:|---:|
| `members` | 414 | 46 |
| `suscriptores` | 7968 | 15 |
| `datosnegocio` | 192 | 34 |
| `datoscontacto` | 2395 | 29 |
| `actosagenda` | 521 | 19 |
| `retos` | 174 | 12 |

All six core endpoints were successfully fetched and saved locally as raw JSON plus processed CSV.

## Normalized outputs created

| File | Rows | Columns |
|---|---:|---:|
| `members_normalized.csv` | 414 | 21 |
| `socios_normalized.csv` | 192 | 22 |
| `retos_normalized.csv` | 174 | 13 |
| `events_normalized.csv` | 521 | 19 |
| `suscriptores_normalized.csv` | 7968 | 18 |
| `entity_universe.csv` | 5370 | 9 |
| `official_socios_coverage.csv` | 192 | 14 |
| `official_socios_readiness.csv` | 192 | 13 |
| `signal_feasibility_matrix.csv` | 10 | 7 |
| `column_profile.csv` | 155 | 7 |

## Official socios coverage

- Official socios: 192
- With member profiles: 108
- With contact records: 192
- With subscriber contacts: 180
- With retos signal: 83

## Official socios readiness

| Readiness label | Count |
|---|---:|
| High | 104 |
| Medium | 53 |
| Low | 35 |

Average readiness score: 70.44 / 100

Interpretation:

- High-readiness socios are the best pilot candidates because they have richer connected data.
- Medium-readiness socios can be included with lower confidence or simpler explanations.
- Low-readiness socios likely need enrichment before strong recommendations can be made.

## Signal feasibility matrix

| Signal | Status | Confidence | Phase 1 decision |
|---|---|---|---|
| Profile similarity | Feasible | High | Use in Phase 1 |
| Technology and sector overlap | Feasible | High | Use in Phase 1 |
| Complementarity | Feasible | Medium-High | Use in Phase 1 with transparent rules |
| Supply-demand matching through retos | Feasible | Medium | Use in Phase 1, but do not rely only on description text |
| Event metadata matching | Feasible | High | Use in Phase 1 |
| Co-attendance graph | Blocked | Low | Do not use until attendance data is provided |
| Subscriber engagement | Partially feasible | Medium | Use as supporting signal, not primary recommender signal |
| Contact availability | Feasible | High | Use for operational handoff and report generation |
| Official socio readiness | Feasible | High | Use to choose pilot socios and confidence levels |
| Churn or retention risk | Partially feasible | Low-Medium | Do not build churn model yet. Keep for later Phase 3. |

## Key findings

- The endpoint data is strong enough to continue into `02_Recommendation_Engine`.
- `members.Tecnologías json` and `members.Sectores json` are 100% parseable and should be preferred over plain text technology/sector columns.
- `datosnegocio.Socio` matches `datoscontacto.Entidad` for all 192 official socios after normalization.
- All official socios have contact records.
- 180 of 192 official socios have subscriber contacts.
- 108 of 192 official socios have rich member/person profiles.
- Retos are usable, but descriptions are sparse: only a small subset has full description text.
- Event metadata is strong, but attendee identities are not available yet.

## Blockers

### Co-attendance graph

Blocked until SECPHO provides attendee-level event data. The current `actosagenda` endpoint includes event metadata and aggregate counts, but not attendee names, emails, or companies.

Needed fields:

- Event title or event ID
- Attendee name
- Attendee surname
- Email
- Company/entity
- Role, if available
- Event date, if available

Once received, this data should be processed in Module 01 first, creating `attendance_normalized.csv`, before being used in Module 02.

## Files touched or created

Main audit scripts are stored in:

`scripts/audit/`

Main generated data files are stored in:

`data/processed/`

Legacy prototype script is stored in:

`legacy/old_code.py`

## Next action

Proceed to `02_Recommendation_Engine` using the normalized tables created in this module. Start with official socios only, prioritize high-readiness socios, and build scoring logic where math decides and the LLM explains.

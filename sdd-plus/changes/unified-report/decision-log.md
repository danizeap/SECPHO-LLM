# Decision Log

## Change

unified-report

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-18 | One report model, two renderers (HTML+docx), LLM in fixed slots only | Chat==download by construction; numbers stay deterministic; kills truncation + the two-generator drift | Keep two generators and try to keep them in sync (rejected: that's the current bug); LLM writes whole doc (rejected: truncation + retyped numbers) |
| 2026-06-18 | LLM prose generated once and cached; download reuses on-screen prose | Guarantees the download equals what the curator saw, despite LLM nondeterminism | Regenerate on download (rejected: would differ run-to-run) |
| 2026-06-18 | LLM prose ALWAYS uses flagship (not the chat's Mini) | Report is a member-facing deliverable going out for feedback — reasoning quality matters more than speed; cache+fallback absorb flagship's latency | Use the chat's selected model (rejected: Mini quality varies, report must be consistently strong); make it a per-call toggle (rejected: reports must be uniformly high-quality) |
| 2026-06-18 | Surface professional + benign personal-affinity (hobbies/sports/languages/university); EXCLUDE children/gender/food_preferences | Warmer, human matchmaking rationale without exposing sensitive personal data; Owner-approved governance | Professional-only (rejected: loses the human angle Owner wants); include all fields (rejected: privacy — sensitive fields) |
| 2026-06-18 | Per-contact "why this is a good match" paragraph + short exec summary | Owner: matchmaking must be explained, not a data dump ("math decides, the LLM explains") | List shared attributes only (rejected: that's the current data-dump) |
| 2026-06-18 | report_engine reads people_matches_v1_1_events.csv (the live app's matcher file) | Report contacts/order must equal the chat's; was reading the older v1 file (#14) | Keep v1 (rejected: disagrees with chat) |
| 2026-06-18 | Phased: P1 deterministic unification (no LLM) → P2 LLM prose → P3 tuned download | P1 alone fixes every current bug and is shippable without LLM risk; layer prose on a correct base | Big-bang all at once (rejected: more risk, slower to fix the live bugs) |

# Decision Log

## Change

06-tuned-weighting-reports

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Deepen the precomputed pool to 50 (`TOP_K` 10 -> 50) | Tuning must be honest — a deeper pool lets a cranked weight surface genuinely buried matches instead of only reshuffling the same 10, so a report from tuned weights is not misleading | Keep top-10 (rejected: re-rank only reshuffles already-good matches); compute the full pool live per request (rejected: heavier, precompute keeps `/api/rerank` fast) |
| 2026-06-16 | The report follows the curator's weighting AND states it plainly via `weighting_text` | Transparency builds trust — the reader must see that a human chose the weighting and exactly how it was set | Silent re-ranking with no weighting statement (rejected: opaque, looks like the model decided) |
| 2026-06-16 | The LLM writes the briefing but the ranking stays pure math (`rerank_for_person`) | Preserve the "math decides, the LLM explains" principle; the human-curated order must not be reinvented by the model | Let the LLM rank from raw signals (rejected: non-deterministic, breaks the principle) |
| 2026-06-16 | Reports follow the chat language and render in the chat only | Match the user's active conversation language; ship the value deliverable without scope creep | ES/EN/both report-download picker and file export (deferred to a future export feature) |

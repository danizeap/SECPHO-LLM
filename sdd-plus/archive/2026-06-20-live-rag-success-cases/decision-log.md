# Decision Log

## Change

live-rag-success-cases (P3 RAG slice)

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-20 | In-RAM embedding index (numpy cosine), rebuilt lazily; persist nothing | Honors the zero-copy posture; 59 cases embed instantly; vectors live only in RAM | Persistent vector store / pgvector (rejected: that's a data store + custody, the whole thing we avoided) |
| 2026-06-20 | Keyword fallback when embeddings are unavailable | The tool must always work (no key, embed failure) and tests must stay hermetic | Fail/empty without embeddings (rejected: brittle); require a key (rejected) |
| 2026-06-20 | Return the matched case summary (+ score) | Grounding: the LLM answers from the actual text and can cite it; math (cosine) ranks, the LLM explains | Return titles only (rejected: not enough to ground an answer) |
| 2026-06-20 | OpenAI `text-embedding-3-small` via the existing requests plumbing | Cheap, good quality, no new dependency (numpy already present); reuses the OpenAI key already in env | A local embedding model (rejected: heavier dep for a PoC) |
| 2026-06-20 | Lazy build + `(len, titles)` staleness hash | Avoid embedding at startup / when off; rebuild when the refresher changes the cases | Rebuild every query (rejected: wasteful); never rebuild (rejected: stale after refresh) |

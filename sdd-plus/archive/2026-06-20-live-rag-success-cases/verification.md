# Verification

## Change

live-rag-success-cases (P3 RAG slice)

## Automated Checks

- [x] `ast.parse` + `-W error::DeprecationWarning` → clean.
- [x] Full suite: 54 passed (51 + 3 RAG), hermetic (slowest 0.52s; no embedding call — key-less keyword path).
- [x] `tests/test_projects_tool.py` RAG: keyword fallback finds "fotónica" (mode=="keyword"); matched
      summary is returned (citation); empty `{cases:[]}` when off; `search_success_cases` in `AGENT_TOOL_SCHEMAS`.

## Manual Checks

- [x] LIVE semantic proof (key + token from env): query "soluciones para el espacio y los satélites" →
      mode=="semantic", top cases DIGISOLAR / Space Giganet / MOSES / GEOLASER (all sector=Espacio),
      cosine-ranked — found by MEANING (titles lack the query words). 59 cases indexed in RAM, nothing persisted.
- [ ] OWNER glance (live + key): "qué casos de éxito tenemos en energía limpia" → relevant stories with summaries.

## Documentation Updates

- [x] agentic-conversation delta: ADD "Semantic search over success stories"; loop now wraps fourteen tools.
- [x] README / project context: no change (numpy already a dependency).

## Result

PASS (static + hermetic suite + live semantic proof). First RAG/embeddings piece in place — semantic
retrieval over success stories with a keyword fallback, in-memory only, grounded by returning the case summary.

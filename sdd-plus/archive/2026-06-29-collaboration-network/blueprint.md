# Build Blueprint — collaboration-network (P5, slice 3)

> Tier: STANDARD (non-sensitive collaboration structure; deterministic; one surfacing decision). No
> product code until the Owner signs off — especially on the surfacing choice (§10).

## 1. Product Goal

Reveal the cluster's COLLABORATION NETWORK — who works with whom via shared projects and retos — so
SECPHO can see its hubs, find a socio's strongest collaborators, and understand how any two members
are connected. Deterministic (math decides, the LLM explains); reuses data already loaded; persists
nothing.

## 2. Users

- **Any staff with `data.socios`** — "who does ACME collaborate with?", "who are our most-connected
  members?", "how are X and Y linked?". It's member-relationship structure — no euros, no PII, no
  candid assessments.

## 3. Core Workflows

1. **One socio's network** → "who does ACME work with?" → ranked collaborators with the shared count
   and via-what (which projects/retos), plus its degree (number of distinct collaborators).
2. **Cluster hubs** → "who are the most connected socios?" → top socios by weighted degree, total
   nodes/edges, and how many are isolated.
3. **How two are linked** → "how are ACME and BETA connected?" → the shared projects/retos between
   them (or "no direct collaboration found").

## 4. MVP Scope

- Build a deterministic, in-memory, undirected **weighted co-participation graph**: nodes = socios,
  an edge between two socios for each shared project (`proyectos.partners`) or shared reto
  (`retos.applying_entities`, plus issuer→applicants and →beneficiary), weight = number of shared
  records.
- Tools: `socio_network`, `network_overview`, `connection_between` — gated `data.socios`.
- All degrees/weights/rankings deterministic; the LLM narrates and must not derive its own metric.

## 5. Non-Goals (this slice)

- No rendered visual graph in v1 (textual/structured output — see §10); a visual is a possible
  follow-on.
- No event co-attendance edges in v1 (noisier — a single event links many socios); projects + retos
  are explicit collaboration. Can add later.
- No heavy centrality (betweenness/eigenvector) in v1 — degree / weighted-degree only.
- No new data sources, no persistence. Eval set is the final P5 slice.

## 6. System Components

- **`backend_api/mvp_web_app.py`** — a graph-builder helper (parse partners/reto entities → weighted
  adjacency, built lazily + cached on the source frames' identity) + 3 gated agent tools
  (`TOOL_REQUIRED_GRANT` + `AGENT_TOOL_SCHEMAS` + `dispatch_tool`). Reuses the in-memory `proyectos` /
  `retos` frames. No `live_data.py` change, no new external service, no new secret.

## 7. Data Model Sketch

- Edge list (computed): `(socio_a, socio_b) -> {weight, via: [{type: project|reto, label}]}`.
- Adjacency: `socio -> {collaborator -> weight}`.
- Node degree: distinct collaborators; weighted degree: sum of edge weights.
- Built from `proyectos.partners` (split on `| ; , /`) and `retos` participant fields.

## 8. Data Flow

Read `proyectos`/`retos` from the in-memory frames → split participant fields → emit co-participation
edges (every pair within a record) → aggregate weights + via-labels → tools query the adjacency and
return ranked rows + an as-of stamp → the agent narrates. Nothing persisted. A caller without
`data.socios` is refused by `dispatch_tool` before the tool runs.

## 9. API / Interface Boundaries

New agent tools (ride `/api/agent`; no new HTTP endpoints):
- `socio_network(socio)` — that socio's collaborators ranked by shared count, with via-what + degree.
- `network_overview()` — top hubs by weighted degree, node/edge counts, isolated count.
- `connection_between(socio_a, socio_b)` — the shared projects/retos linking the two.

## 10. Surfacing — THE KEY DECISION

How does the network reach the user?
- **(a) Textual / structured (recommended for v1):** the tools return ranked collaborators / hubs /
  shared-records; the LLM narrates ("ACME's strongest collaborators are X — 3 shared projects — and
  Y…"). Fits the chat, fully deterministic, ships fast, answers every workflow above.
- **(b) Rendered visual graph in-app:** a network diagram embedded in the chat (SVG/image). Compelling
  for demos, but a meaningfully bigger lift (a new render path in the chat UI) and the data answers
  the questions without it.

**Recommendation:** ship **(a)** now; treat **(b)** as a follow-on (the deterministic graph this slice
builds is exactly what a future visual would render). **Open question for the Owner:** textual v1, or
build the in-app visual now?

## 11. External Services / Integrations

None new. Reuses the live layer + the P4 grant model.

## 12. Risks & Tradeoffs

- **Socio-name consistency** across sources (e.g. "AIMEN" vs "AIMEN Centro Tecnológico") → edges key
  on the participant string as recorded; near-duplicate names may under-merge. v1 matches as-recorded
  and notes this; a normalization pass is a future enhancement.
- **Hallucinated metrics** → degrees/weights deterministic; the LLM quotes them (the no-derive rule
  from the health slice already covers this).
- **Performance** → small graph (≈150 projects, ≈180 retos); trivial in-memory.
- **Zero-copy / non-sensitive** → reuses in-RAM frames, persists nothing; collaboration structure is
  not financial/PII.

## 13. Implementation Phases

- **P5n-a — graph + tools** (gate `data.socios`): the builder + `socio_network`, `network_overview`,
  `connection_between`. Hermetic tests (exact edges/weights/degree + gating) + a live proof.
- **P5n-b — close-out**: verify → verifier subagent → adversarial security review → LaunchGuardian →
  spec sync → archive + commit.

## 14. Testing Strategy

Hermetic (inject synthetic `proyectos`/`retos` frames): exact edge construction (pairs within a
record), weight aggregation across shared records, degree + weighted-degree, top-hub ranking,
connection_between for linked and unlinked pairs, and the `data.socios` gating. Delta spec for
`agentic-conversation` + `access-control`.

## 15. LaunchGuardian Handoff

P5n-b: local scan (Linux/CI for semgrep). Low sensitivity (no euros/PII), but run the gate for
consistency.

## 16. Next Skill Recommendation

On approval → implementation (P5n-a), verified + archived; then the final P5 slice: the **eval set**
(mixed-concept stress questions across financial + health/churn + network + the existing tools).

---

### Evidence note

- **Requirements:** who-works-with-whom (collaborators, hubs, links), deterministic, gated, reuse
  loaded data. Edge data confirmed rich: 62/152 projects ≥2 partners (max 7), 70/179 retos ≥2 applicants.
- **Key decision:** surfacing — textual v1 (rec) vs in-app visual now (Owner to choose).
- **Assumptions:** participant fields are delimiter-separated socio names (confirmed for projects;
  reto fields present); name matching is as-recorded for v1.
- **Open questions:** (a) surfacing (above); (b) add event co-attendance edges later? (rec: not v1);
  (c) gate = `data.socios` (rec — non-sensitive relationship data).
- **Rejected alternatives:** event co-attendance edges in v1 (noisy); heavy centrality (overkill for
  v1); a financial/admin gate (rejected — collaboration structure isn't sensitive).
- **Result:** PASS WITH OPEN QUESTIONS — ready to build on approval; the surfacing choice shapes scope.

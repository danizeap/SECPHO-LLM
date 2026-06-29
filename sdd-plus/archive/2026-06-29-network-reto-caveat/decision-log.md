# Decision Log

## Change

network-reto-caveat

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Surface the project-vs-reto edge split + a reto-dominance note in `network_overview` | The graph is reto-dominated because `proyectos.partners` is sparse; the summary must say so rather than imply rich project collaboration. Honest, data-agnostic (shows whatever the data supports) | Silently leave the summary as a single connection count (overclaims); hard-code a caveat regardless of data (dishonest if projects are later enriched); try to "fix" project data (not ours — zero-copy) |
| 2026-06-29 | Leave the builder + per-socio tools unchanged | `_build_network` is correct and `socio_network`/`connection_between` already expose via-projects/via-retos; only the cluster summary lacked the split | Rework the whole network layer (unnecessary) |

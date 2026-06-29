# Decision Log

## Change

socio-turnover-ranking

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Rank by company turnover (`cifra de negocio`), not SECPHO billing | "Socios de mayor facturación" for the network×financial question means the biggest companies; turnover is the size metric that chains naturally to the collaboration network | A SECPHO-billing rank (invoiced total) — different question ("who we bill most"); can be added later if asked |
| 2026-06-29 | Gate `data.financiero` | Turnover is sensitive financial data, same tier as the other financial tools | Gate `data.socios` (would leak financial magnitude to engagement-only users) |
| 2026-06-29 | Exclude unparseable turnover; deterministic name tiebreak | "Math decides" — only real, parseable figures rank; stable order across live pulls | Include zeros/None (noise); rely on frame order (non-deterministic) |

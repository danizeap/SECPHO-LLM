# Brief

## Change

financial-turnover-robust-stat

## User Need

Admins/dev asking for the cluster financial overview must see trustworthy turnover figures — a
visibly-broken headline number erodes trust in the correct figures next to it.

## Problem

`financial_overview` reported `total_turnover` as a raw `.sum()` of every socio's self-reported
turnover. That field is heavy-tailed (a few members report group/global figures), so on live data the
sum was **~€100 billion** against a sane median of €2.6 M — an obviously-wrong headline (live-test
finding #1). The LLM quoted it verbatim (correctly), but the tool's stat choice was wrong.

## Scope

In scope:

- Drop the raw `total_turnover` sum from `financial_overview`; report robust stats instead — median,
  max, and count.

Out of scope:

- Contributions-total mislabel (#3), at-risk under-count (#5), billing-rank tool (#2), network
  reto-only (#4) — separate / phase-2.

## Acceptance Criteria

- [x] `financial_overview.turnover` no longer contains `total_turnover`.
- [x] It contains `socios_with_turnover`, `median_turnover`, `max_turnover`.
- [x] A giant outlier no longer produces a misleading headline (median stays sane; max surfaces it).

## Impact Areas

- Backend: `financial_overview` turnover block.
- Frontend: none.
- Data model: none.
- API: minor output-shape change to one agent tool (LLM-consumed only).
- AI/model behavior: the LLM presents median/max/count; the existing anti-derivation rule already
  forbids it from re-summing.
- Documentation: agentic-conversation delta (robust-turnover scenario).
- Operations/security: none.

## Open Questions

- None.

# Decision Log

## Change

financial-turnover-robust-stat

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-29 | Drop `total_turnover`; report median + max + count | Self-reported turnover is heavy-tailed (a few members report group/global figures); a raw sum is dominated by outliers and misleads as a "cluster total" (live data → ~€100B). Median is the honest central figure; max surfaces the outlier | Keep the sum with an "outlier-skewed" caveat (still a misleading headline); winsorize/cap outliers (arbitrary threshold); compute total excluding outliers (arbitrary) |

# ADR 005 — Expand Training Data to the Top Five Leagues from Multiple Sources

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The match outcome model trains on one season: Premier League 2023/24, 380 matches from
football-data.co.uk. The model card shows it is data-starved: best iteration 10, test accuracy 0.561
on 57 matches, but cross-validation accuracy 0.442 and log loss 1.616.

Four Kaggle datasets were proposed as extra data. A profile of each (see
[the retraining plan](../plans/multi-league-retraining-plan.md), §2) found:

| Dataset | Content | Unique value |
|---|---|---|
| saife245 | Copy of football-data.co.uk EPL, 2018/19 and 2019/20 truncated | None |
| armin2080 | FBref EPL team-match logs 2020/21–2024/25 | xG, possession |
| enricocattaneo | Sportmonks top-5 leagues 2015/16–2021/22, FIFA ratings, weather | FIFA team ratings |
| adrianjuliusaluoch | football-data.org API snapshots 2023/24 onward, 90% duplicate rows | Champions League fixtures |

Every match result in those datasets is also published by football-data.co.uk, which covers all five
major leagues in one CSV format from 2000/01 onward.

CLAUDE.md lists "covering football leagues beyond the initial scoped dataset" as a non-goal.

## Decision

Expand the training data to the Premier League, Bundesliga, La Liga, Serie A and Ligue 1, seasons
2000/01 to 2025/26, with football-data.co.uk as the primary source of results.

1. **Primary source.** football-data.co.uk divisions `E0`, `D1`, `SP1`, `I1`, `F1`, fetched by the
   existing `FootballDataProvider`. It is the only source that covers every league and season.
2. **Secondary sources**, each behind its own adapter and never on the baseline model's critical path:
   - armin2080: EPL cross-check for scores and dates; source of xG.
   - enricocattaneo: source of FIFA team ratings, used only with as-of dating.
   - adrianjuliusaluoch: source of Champions League fixtures for rest-day features.
   - saife245: not used.
3. **Source precedence** when sources disagree: football-data.co.uk, then armin2080, then
   enricocattaneo, then adrianjuliusaluoch. Disagreement on goals or result fails the run.
4. **Provenance.** Every canonical match row gains `source`, `source_version`, `source_row_id` and
   `match_key`. Every processed file has a metadata JSON with source URL, licence, download date and
   checksum.
5. **Odds** stay out of the feature set. They are used only as an evaluation benchmark.
6. **Scope boundary.** The prediction API and Android app stay Premier League-only until a separate
   ADR changes the API contract.
7. The CLAUDE.md non-goal is amended to name the top five leagues as the scoped dataset.

## Consequences

- Around 30,000 league matches instead of 380, enough to train without early stopping at iteration 10.
- `FootballDataProvider` and `DIVISION_TO_COMPETITION` gain four division codes. No new download
  logic is needed; the URL pattern is the same.
- `ProcessedMatch` gains provenance fields. This is a data schema change.
- Features that assume one season (league position, rest days, Elo start values) must become
  season- and league-aware before training on the new data.
- Kaggle raw files are not committed. Licences for the four Kaggle datasets must be confirmed
  before their adapters are merged.
- xG, FIFA ratings and Champions League fixtures each cover only part of 2000–2026. They are
  evaluated as separate ablations after the baseline, not added to it by default.
- ADR 001 anticipated replacing XGBoost with LightGBM above 10,000 rows. At around 30,000 rows,
  XGBoost trains in well under a minute locally, so no change is made; revisit only if training
  time becomes a problem.

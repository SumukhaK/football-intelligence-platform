# Kaggle Extras: xG, FIFA Ratings and Champions League Rest Days

**Date:** 2026-09-29
**Model:** `20260928_123224` (served configuration, retrained with and without each extra)
**Plan:** [multi-league plan, phase 7](../plans/multi-league-retraining-plan.md)
**Reproduce:** `uv run python -m scripts.kaggle_extras_experiment` from `ai/`

## Summary

None of the three extras improves the model, so none is added. Two of them
could not be served for the current season even if they had helped.

| Extra | Log loss change (new − current) | 95% interval | Can it be served for 2026/27? |
|---|---|---|---|
| Champions League rest days, 2023/24 | −0.0001 | −0.0010 to +0.0008 | Only until the dump's fixtures run out (January 2027) |
| Champions League rest days, 2024/25–2025/26 | −0.0005 | −0.0012 to +0.0002 | |
| … only matches after a CL game (637) | −0.0004 | −0.0021 to +0.0012 | |
| Rolling xG, Premier League 2023/24 (377) | +0.0028 | −0.0004 to +0.0059 | No: the source ends in 2024/25 |
| Rolling xG, Premier League 2024/25 (377) | +0.0020 | −0.0016 to +0.0057 | |
| FIFA ratings, 2020/21–2021/22 (1,276) | +0.0010 | −0.0015 to +0.0036 | No: ratings stop in May 2022 |

Every interval includes zero, so these changes are noise. The extras carry
little that the existing features (Elo, form, goal statistics, league position)
do not already capture.

## The data

| Source | Contents | Cleaning needed |
|---|---|---|
| armin2080 (FBref) | Team-match rows with xG and xGA, Premier League 2020/21–2024/25 | Map 14 FBref spellings (for example "Wolverhampton Wanderers") to ours |
| enricocattaneo (Sportmonks, FIFA) | Cup matches 2011/12–2021/22, including 2,271 Champions League games; weekly FIFA team ratings 2009–May 2022 | 53k rating rows carry scraped dates such as "Sept. 23, 2021", now parsed; FIFA spellings matched automatically with a strict cutoff (130 clubs) |
| adrianjuliusaluoch (football-data.org) | Ten competitions, including the Champions League 2023/24 onwards, snapshot of 27 September 2026 | 135k duplicate rows (the same match in repeated snapshots) collapsed to 13,846 by keeping each match's latest update; 1% of rows have shifted columns and are dropped |

Champions League club names from both sources are mapped with a reviewed alias
table, `datasets/schemas/team_aliases.csv`, as ADR 006 describes: 79 rows, with
no fuzzy matching at run time. There is no Champions League coverage for
2022/23, so that season's rest-day features are left missing.

## Method

- **Champions League rest days:** days since each team's last match in the
  league or the Champions League, and a flag for a Champions League game in the
  previous seven days. Seasons without Champions League data are left missing.
- **Rolling xG:** each team's mean xG and xGA over its previous five league
  matches, from the shift-by-one rolling window used for every other form
  feature.
- **FIFA ratings:** attack, midfield and defence from the latest weekly
  snapshot within 60 days before the match.
- **Testing:** each group is added to the feature matrix and the model is
  retrained with the served configuration. The change is compared with a
  paired bootstrap on rows where the source has data. FIFA ratings end in 2022,
  so they are tested on 2020/21–2021/22, trained up to 2018/19 and validated on
  2019/20.

## Decision

Keep the served model as it is (ADR 007 promotion rule). The alias table and
the experiment script are committed so the test can be repeated if a live xG or
ratings source becomes available. That is the only way either could be served.

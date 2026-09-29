# Goals Model: Rolling-Origin Evaluation

**Date:** 2026-09-28
**Model:** time-weighted Dixon-Coles per league ([ADR 009](../adr/009-dixon-coles-goals-model.md), `ai/goals/`)
**Data:** `match_results_live_v20260928_172253.csv` (top five leagues, 2000/01 to 2026/27 so far)
**Reproduce:** `uv run python -m evaluation.goals_evaluation_cli` from `ai/`
(writes `models/evaluation/goals/goals_evaluation.json` and `goals_forecasts.csv`)

## Summary

- **Scorelines.** The most likely score is right 12–14% of the time, and the
  actual score is in the top three about a third of the time. That is in the
  range the plan expected.
- **Goal markets are well calibrated.** Forecast totals match the seasons'
  actual goals (2.81 forecast against 2.80 actual per match on 2024/25–2025/26).
  Over 2.5 forecasts track outcomes within a few points in every well-populated
  bin. Bookmakers remain slightly better, as expected (Brier 0.2432 against
  0.2399 on the holdout).
- **Against a plain Poisson model the gain is small.** The Dixon-Coles
  correction and time decay improve scoreline log loss by 0.009 on 2023/24,
  which is borderline (the 95% interval just includes zero). There is no
  change on 2024/25–2025/26. The tuned model is kept because it is never worse,
  but the plan's "beats independent Poisson" gate is only met on the point
  estimate.
- **XGBoost keeps the headline pick.** The goals model's home/draw/away
  probabilities are worse than XGBoost's on 2023/24 and 2026/27 so far, and
  equal on the holdout. This confirms decision 2 in the plan.
- **No help with draws.** Its draw probabilities are as flat as XGBoost's
  (never above 0.36), so the draw tag (ADR 011) stays on XGBoost.

## Method

- **Rolling origin.** Before every matchweek (Monday to Sunday) each league
  is refitted on all matches strictly before that Monday, and that week's
  matches are forecast. This mirrors serving, where the model is refitted on
  every data refresh. A test asserts that no fit sees the match it forecasts.
- **Fit.** Four-year window, match weights `exp(-xi * age in days)`, L2
  shrinkage of team strengths toward the league average, with an unpenalised
  league intercept. Teams with little recent data (promoted sides) are shrunk
  toward the three weakest established teams.
- **Tuning.** `xi` and `l2` were chosen on 2022/23 only, by scoreline log
  loss, from a 6 × 4 grid. The best was `xi = 0.003` per day (a weight halves
  in about 7½ months) and `l2 = 8`, inside the grid.
- **Baseline.** Independent Poisson with the same shrinkage, no time decay and
  `rho = 0`, also refitted weekly.
- **Blocks.** Test 2023/24 (1,752 matches), holdout 2024/25–2025/26 (3,504),
  and 2026/27 so far (250).

## Results

### Scorelines

| Block | Log loss, model | Log loss, Poisson baseline | Change (95% interval) | Top-1 hit | Top-3 hit |
|---|---|---|---|---|---|
| 2023/24 | 2.9324 | 2.9417 | −0.0093 (−0.0193 to +0.0011) | 14.1% | 33.5% |
| 2024/25–2025/26 | 2.9078 | 2.9077 | +0.0001 (−0.0064 to +0.0063) | 12.4% | 32.1% |
| 2026/27 so far | 3.0260 | 3.0356 | −0.0096 (−0.0324 to +0.0141) | 13.2% | 30.4% |

### Goal markets

| Block | Over 2.5 Brier, model | Over 2.5 Brier, bookmakers | BTTS Brier, model |
|---|---|---|---|
| 2023/24 | 0.2375 | 0.2348 | 0.2431 |
| 2024/25–2025/26 | 0.2432 | 0.2399 | 0.2469 |
| 2026/27 so far | 0.2338 | 0.2262 | 0.2414 |

Bookmaker probabilities are the market-average over/under 2.5 odds with the
margin removed. Every evaluated match has them.

Over 2.5 reliability on 2024/25–2025/26 (forecast → observed):

| Forecast bin | Matches | Forecast | Observed |
|---|---|---|---|
| 0.3–0.4 | 342 | 0.37 | 0.42 |
| 0.4–0.5 | 1,039 | 0.45 | 0.47 |
| 0.5–0.6 | 1,271 | 0.55 | 0.55 |
| 0.6–0.7 | 726 | 0.64 | 0.61 |
| 0.7+ | 112 | 0.75 | 0.74 |

2026/27 so far has more goals than the model expects (3.04 per match against
2.80). With 250 matches this is not yet a reliable trend, but it is worth
re-checking after more matchweeks.

### Home/draw/away, against the served XGBoost model

| Block | Log loss, goals model | Log loss, XGBoost | Change (95% interval) |
|---|---|---|---|
| 2023/24 | 0.9838 | 0.9762 | +0.0076 (+0.0006 to +0.0144) |
| 2024/25–2025/26 | 0.9952 | 0.9960 | −0.0009 (−0.0061 to +0.0044) |
| 2026/27 so far | 0.9948 | 0.9749 | +0.0198 (+0.0025 to +0.0372) |

## What ships

The tuned Dixon-Coles model feeds the scoreline extras only: the most likely
scores, expected goals, both teams to score, over/under lines and clean
sheets. The next step is the `/insights` API (plan PR 3), then the app sections
(plan PR 4). A first-run bug worth recording: without an unpenalised
intercept, shrinkage pulled the league's scoring level down and every goals
market was under-forecast. A test now guards against it.

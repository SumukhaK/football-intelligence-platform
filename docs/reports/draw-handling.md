# Draw Handling: What the Model Can and Cannot Do

**Date:** 2026-09-28
**Model:** `20260928_123224` (XGBoost, 42 features)
**Plan:** [next-phase plan, W4](../plans/next-phase-plan.md)
**Reproduce:** `uv run python -m evaluation.draw_analysis --in-season models/backtests/2627_20260928_model123224/predictions.csv`
and `uv run python -m scripts.draw_feature_experiment` (both from `ai/`)

## Summary

- The model's draw probabilities are **well calibrated**. When it gives a
  draw about 28%, about 28% of those matches end level.
- They are also **flat**. The draw probability never goes above 0.36 in any
  season, so a draw is never the most likely outcome, and no match stands
  out as a clear draw.
- **The agreed target is out of reach.** Catching a third of draws costs
  about 4 to 5 points of accuracy, not 1. Within a 1-point budget, the rule
  catches about 10% of draws.
- **Draw features don't help.** Six draw-oriented features change log loss by
  −0.0002 on 2023/24 and −0.0001 on 2024/25–2025/26. Both 95% intervals
  include zero, so the features were not adopted (ADR 007 promotion rule).

## 1. Calibration of the draw probability

Predicted draw probability against the share of matches that ended level.

| Draw probability | 2022/23 (n, predicted → observed) | 2023/24 | 2024/25–2025/26 |
|---|---|---|---|
| up to 0.20 | 250, 0.16 → 0.16 | 235, 0.16 → 0.17 | 482, 0.16 → 0.17 |
| 0.20–0.24 | 315, 0.22 → 0.20 | 307, 0.22 → 0.22 | 570, 0.22 → 0.23 |
| 0.24–0.27 | 484, 0.26 → 0.27 | 460, 0.26 → 0.27 | 952, 0.26 → 0.26 |
| 0.27–0.30 | 686, 0.28 → 0.25 | 664, 0.28 → 0.31 | 1,273, 0.28 → 0.28 |
| 0.30–0.33 | 91, 0.31 → 0.40 | 84, 0.31 → 0.32 | 216, 0.31 → 0.29 |
| above 0.33 | — | 2, 0.34 → 0.50 | 11, 0.34 → 0.27 |

The bins track the observed rate to within a few points wherever the sample
is large. The problem is range, not bias: almost every match sits between
0.20 and 0.33, where a draw is plausible but never likely.

## 2. Draw rule trade-off

The rule picks a draw when its probability is within a margin of the
favourite's. The margin was read off 2022/23 only; the later seasons test it.

| Margin | 2022/23 accuracy, draws caught | 2023/24 | 2024/25–2025/26 | 2026/27 so far (250) |
|---|---|---|---|---|
| 0 (today) | 52.9%, 0% | 52.5%, 0% | 51.6%, 0% | 52.4%, 0% |
| 0.09 | 52.4%, 11% | 52.1%, 8% | 50.8%, 8% | 50.0%, 11% |
| 0.10 | 51.6%, 14% | 51.6%, 11% | 50.6%, 13% | 50.0%, 15% |
| 0.15 | 48.5%, 32% | 50.0%, 31% | 48.1%, 32% | 54.0%, 56% |
| 0.20 | 45.1%, 51% | 47.7%, 48% | 45.6%, 49% | 50.4%, 81% |

- Every draw pick is right only 27–30% of the time, barely above the 25% base
  rate. Each extra draw caught costs about two correct home or away picks.
- The 2026/27 row is only 250 matches, and 62 of them draws. Its jump at the
  0.15 margin is noise, not a sign that the rule works better this season.

## 3. Draw-oriented features

Candidates, each computed only from matches before the one being predicted:

- each team's draw rate over its last 10 matches (home and away side);
- average total goals in each team's last 10 matches;
- absolute Elo rating gap;
- the league's draw rate over roughly its last two seasons.

With all six added and the model retrained with the served configuration:

| Block | Log loss change (new − current) | 95% interval |
|---|---|---|
| 2023/24 | −0.0002 | −0.0021 to +0.0016 |
| 2024/25–2025/26 | −0.0001 | −0.0014 to +0.0013 |

The maximum draw probability rises only from about 0.34 to 0.36–0.37, and the
draw rule's trade-off is unchanged. The existing features (Elo ratings, form,
head-to-head draws) already carry what these add.

## 4. What this means

Draws are hard to call from pre-match information. Bookmakers' favourites
were right 51.6% of the time in 2026/27 so far, and they never make a draw
the favourite either. The options, which need a product decision:

1. **Tag only:** keep today's picks and show a "draw possible" tag for the
   tightest games. There is no accuracy cost.
2. **Small rule (margin 0.09):** about 10% of draws caught, about 1 point of
   accuracy lost.
3. **Catch a third (margin 0.15):** about 4 to 5 points of accuracy lost.

The Dixon-Coles goals model (ADR 009) is the remaining route to a sharper
draw signal. It models the low scores that produce most draws directly. Its
evaluation should repeat section 2 on the blended probabilities.

## 5. Decision: tag only

Chosen on 2026-09-28 (ADR 011). The API flags `draw_possible` when the draw
probability is at least 0.28, and the pick is unchanged. The threshold was
read off 2022/23 as the lowest that flags under a third of matches.

| Block | Matches flagged | Draw rate, flagged | Draw rate, others |
|---|---|---|---|
| 2022/23 | 30% | 27% | 23% |
| 2023/24 | 29% | 31% | 25% |
| 2024/25–2025/26 | 29% | 28% | 24% |
| 2026/27 so far | 41% | 35% | 18% |

# 2026/27 So Far: Live Check of the Five-League Model

**Date:** 2026-09-28
**Model:** `20260928_120015` (served at the time, now replaced by `20260928_123224`, see Rerun; trained on 2000/01–2021/22, never retrained on later data)
**Matches:** every played league match of 2026/27 in the five leagues, up to 2026-09-20 (250 matches)
**Method:** each match is predicted from features built only from matches before it, using the training feature pipeline (`python -m evaluation.in_season_cli`).
**Benchmark:** the bookmaker is Bet365's pre-match odds (football-data.co.uk `B365H`, `B365D`, `B365A`) with the margin removed by normalising the implied probabilities to sum to 1. It is a benchmark only and never a model input.

## Rerun with the current model

After ADR 008 changed the Elo season rules, the served model became
`20260928_123224`. Rerun on the same 250 matches, overall accuracy is
unchanged at 131/250 (52.4%), with log loss 0.975 against the bookmakers'
0.981. Two matches flip: Serie A becomes 31/50 (62.0%) and Ligue 1 becomes
25/45 (55.6%). The root README shows these numbers. The tables below are
from the first run, with model `20260928_120015`.

## Confidence ranges and an Elo-only baseline

Rescored on 2026-10-07 from the same saved features (model `20260928_123224`,
250 matches up to 2026-09-20). Ranges are 95% bootstrap intervals over 2,000
resamples of the 250 matches. The Elo-only baseline is a multinomial logistic
regression on the pre-match Elo gap (home minus away), fitted on every
completed season before 2026/27, so it shows what the model adds over ratings
alone.

| Forecast | Accuracy | Log loss | RPS | Brier |
|---|---|---|---|---|
| Our model | 52.4% (46.4% to 58.8%) | 0.975 (0.930 to 1.020) | 0.199 (0.185 to 0.213) | 0.578 (0.546 to 0.610) |
| Elo only | 48.8% (42.8% to 55.2%) | 1.005 (0.956 to 1.056) | 0.207 (0.192 to 0.223) | 0.598 (0.563 to 0.634) |
| Bet365 | 51.6% (45.6% to 57.6%) | 0.981 (0.925 to 1.037) | 0.201 (0.185 to 0.218) | 0.584 (0.544 to 0.623) |

Paired bootstrap of our model minus each benchmark on the same resampled
matches. Negative is better for log loss, RPS and Brier; positive is better
for accuracy (in percentage points).

| Model minus | Accuracy | Log loss | RPS | Brier |
|---|---|---|---|---|
| Bet365 | +0.8 (−2.4 to +4.0) | −0.006 (−0.027 to +0.015) | −0.003 (−0.009 to +0.004) | −0.006 (−0.021 to +0.009) |
| Elo only | +3.7 (+0.8 to +6.8) | −0.030 (−0.051 to −0.010) | −0.009 (−0.015 to −0.003) | −0.021 (−0.034 to −0.008) |

- **Level with Bet365.** Every interval for model minus Bet365 includes zero.
- **Clearly better than Elo alone.** Every interval for model minus Elo only
  excludes zero, so the other features add real information on these matches.
- **The ranges are wide.** With 250 matches, accuracy alone is only known to
  about ±6 points, so the per-league tables below say little on their own.

## Results

Played matches up to 2026-09-20, scored 2026-09-28.
Accuracy is the share of matches where the most likely outcome happened.
Log loss rewards confident correct forecasts; lower is better.

| League | Matches | Our accuracy | Bookmaker accuracy | Our log loss | Bookmaker log loss | Priors log loss |
|---|---|---|---|---|---|---|
| overall | 250 | 52.4% | 51.6% | 0.973 | 0.981 | 1.076 |
| Bundesliga | 36 | 50.0% | 52.8% | 0.975 | 0.953 | 1.026 |
| La Liga | 69 | 49.3% | 55.1% | 0.958 | 0.947 | 1.068 |
| Ligue 1 | 45 | 53.3% | 48.9% | 1.019 | 1.044 | 1.095 |
| Premier League | 50 | 46.0% | 44.0% | 1.023 | 1.052 | 1.117 |
| Serie A | 50 | 64.0% | 56.0% | 0.902 | 0.921 | 1.066 |

## What this says

- **Level with the bookmakers.** Overall log loss is 0.973 against the bookmakers' 0.981, and accuracy is 52.4% against 51.6%. The paired bootstrap interval for our log loss minus theirs is −0.029 to +0.014, so the edge is within noise.
- **Much better than guessing from past frequencies**, which scores 1.076.
- **Confident picks hold up.** When the model gave one outcome more than 60%, it was right in 39 of 45 matches (87%).
- **Draws are never the pick.** 25% of these matches were draws, but a draw is never the single most likely outcome. This is typical for outcome models and costs accuracy, not log loss.
- **Small samples per league.** Between 36 and 69 matches each, so per-league differences, such as Serie A at 64% or the Premier League at 46%, are not reliable yet.

The same check on the completed 2024/25 and 2025/26 holdout seasons (3,504 matches) gave 51.8% accuracy and log loss 0.995, against the bookmakers' 53.4% and 0.972. See [the comparison report](multi-league-retraining-comparison.md).

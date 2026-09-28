# 2026/27 So Far: Live Check of the Five-League Model

**Date:** 2026-09-28
**Model:** `20260928_120015` (served; trained on 2000/01–2021/22, never retrained on later data)
**Matches:** every played league match of 2026/27 in the five leagues, up to 2026-09-20 (250 matches)
**Method:** each match is predicted from features built only from matches before it, using the training feature pipeline (`python -m evaluation.in_season_cli`). Bookmaker probabilities are a benchmark only.

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

# Refit on All Seasons: Backtest on 2026/27 So Far

**Date:** 2026-10-07
**Reporting model (frozen split):** `20260928_123224`, trained on 2000/01–2021/22 (served until 2026-10-07; still the source of test and holdout results)
**Serving refit:** `20261007_154105`, trained on 2000/01–2025/26 (46,709 matches), served since 2026-10-07
**Matches:** the same 250 played league matches of 2026/27, up to 2026-09-20, as the [in-season check](in-season-2026-27.md)
**Decision record:** [ADR 017](../adr/017-refit-on-all-seasons-for-serving.md)

## What was trained

The refit copies the reporting run's recipe: the 42 pinned features, depth 3,
learning rate 0.03, subsample and column sample 0.8, seed 42, and a median
imputer. The reporting run's best iteration was 167 (XGBoost counts from
zero), so it predicts with 168 trees; the refit grows exactly 168 trees with
no early stopping. Nothing is held out.

**No leakage.** The refit's last training match is 2026-05-24 (2025/26); the
first backtest match is 2026-08-15, and no 2026/27 match is in its training
rows. The backtest reuses the features saved by the in-season run on
2026-09-28, where each match was built only from matches before it. The
frozen model reproduces that run exactly (131/250, log loss 0.975).

## Results

Bookmaker probabilities are Bet365 odds normalised for the overround; they are
a benchmark only. Lower is better for log loss, RPS and Brier.

| | Accuracy | Log loss | RPS | Brier |
|---|---|---|---|---|
| Frozen `20260928_123224` | 52.4% (131/250) | 0.975 | 0.1987 | 0.578 |
| Refit `20261007_154105` | 52.0% (130/250) | 0.976 | 0.1987 | 0.578 |
| Bookmaker (Bet365) | 51.6% (129/250) | 0.981 | 0.2013 | 0.584 |

Paired bootstrap on the same 250 matches (2,000 resamples, 95% intervals):

| Difference | Log loss | RPS | Accuracy |
|---|---|---|---|
| Refit − frozen | +0.001 (−0.005 to +0.007) | +0.000 (−0.001 to +0.001) | −0.4 pts (−2.0 to +0.8) |
| Refit − bookmaker | −0.005 (−0.026 to +0.016) | −0.003 (−0.009 to +0.004) | +0.4 pts (−2.8 to +3.6) |
| Frozen − bookmaker | −0.006 (−0.027 to +0.016) | −0.003 (−0.009 to +0.004) | +0.8 pts (−2.4 to +4.0) |

Per league (accuracy / log loss):

| League | Matches | Frozen | Refit | Bookmaker |
|---|---|---|---|---|
| Bundesliga | 36 | 50.0% / 0.967 | 50.0% / 0.967 | 52.8% / 0.953 |
| La Liga | 69 | 49.3% / 0.958 | 49.3% / 0.954 | 55.1% / 0.947 |
| Ligue 1 | 45 | 55.6% / 1.023 | 55.6% / 1.018 | 48.9% / 1.044 |
| Premier League | 50 | 46.0% / 1.027 | 44.0% / 1.041 | 44.0% / 1.052 |
| Serie A | 50 | 62.0% / 0.908 | 62.0% / 0.910 | 56.0% / 0.921 |

## What this says

- **The refit is level with the frozen model.** Every interval for refit minus
  frozen straddles zero and is narrow: log loss within ±0.007, RPS within
  ±0.001. Only 3 of 250 picks change (one Premier League and two La Liga
  matches), netting one fewer correct pick. Probabilities move by 0.009 on
  average and at most 0.075.
- **Both are level with the bookmaker.** Each model's log loss and RPS are
  slightly better than Bet365's on these matches, but the intervals include
  zero, so neither edge is real evidence yet.
- **Four more seasons did not change much.** The 7,000 extra matches mostly
  repeat patterns the model had already learned. The case for serving the
  refit is that it has seen the most recent seasons, not that it scores
  better on this sample.
- **Small sample.** 250 matches cannot separate two models this close; the
  per-league differences are noise.

## Draw-tag check (ADR 011)

`evaluation.draw_analysis` was re-run for both models. The 2022/23 to 2025/26
blocks are training data for the refit, so only 2026/27 is out of sample for
it.

| Model | Block | Flagged at 0.28 | Draw rate, flagged | Draw rate, others | Lowest threshold flagging under a third |
|---|---|---|---|---|---|
| Frozen | 2022/23 | 30% | 27% | 23% | 0.28 |
| Refit | 2022/23 (in sample) | 30% | 31% | 21% | 0.28 |
| Frozen | 2026/27 so far | 41% | 35% | 18% | 0.29 |
| Refit | 2026/27 so far | 40% | 34% | 19% | 0.29 |

The ADR 011 rule still gives 0.28 for the refit, and on 2026/27 the tagged
matches draw far more often than the rest, as with the frozen model. The
threshold can stay at 0.28 if the refit is served. Its highest draw
probability on 2026/27 is 0.315, the same as the frozen model's, so a draw is
still never the pick.

## Status

Served since 2026-10-07, on the owner's approval (ADR 017 accepted). It met
the swap rule: the log loss interval against the frozen model is within
±0.02, the draw tag holds at 0.28, and SHAP values generate (42 features × 3
classes, all finite). `20260928_123224` stays in `models/runs/` as the
reporting model and the rollback.

## Reproduce

From `ai/`:

```bash
uv run python -m training.refit --source-run models/runs/20260928_123224 --last-season 2025/26
uv run python -m evaluation.refit_backtest --rows models/backtests/2627_20260928_model123224/features/feature_matrix.parquet --frozen-run models/runs/20260928_123224 --refit-run models/runs/20261007_154105
uv run python -m evaluation.draw_analysis --model models/runs/20261007_154105/model.joblib --in-season models/backtests/refit_20261007_154105/predictions_refit.csv --output models/backtests/refit_20261007_154105/draw_analysis_refit.json
uv run python -m training.promote_refit --run models/runs/20261007_154105 --backtest models/backtests/refit_20261007_154105/report.json
```

Model runs and backtest outputs are local artefacts under `ai/models/` and are
not committed.

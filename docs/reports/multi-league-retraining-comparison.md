# Multi-League Retraining: Model Comparison

## Update: tuned model promoted (2026-09-28)

Hyperparameters were chosen by season walk-forward CV on training seasons only
(`python -m training.tuning`, 27 settings, folds validating on 2017/18 to
2021/22). Best: max depth 3, learning rate 0.03, 400 trees (CV log loss 0.9897;
the top ten settings are within 0.0006 of each other). With early stopping on
2022/23 it stopped at iteration 212.

| Log loss | Current (1 season) | Untuned | Tuned | Bookmaker |
|---|---|---|---|---|
| Current model's 57 test matches | 0.9493 | 0.8381 | **0.8076** | 0.7677 |
| 2023/24 test, all leagues (1,752) | — | 0.9837 | **0.9748** | 0.9548 |
| 2024/25–2025/26 holdout (3,504) | — | 1.0002 | **0.9949** | 0.9719 |

Tuned minus current on the 57 matches: log loss −0.143 (95% interval −0.221 to
−0.065), RPS −0.048 (−0.072 to −0.023). The promotion rule passes.

The tuned settings were retrained with promotion as run `20260928_120015`
(identical metrics to the unpromoted run `20260928_115926`). It is now in
`models/latest` and the registry; `/model`, `/predict` and `/explain` serve it.
The previous model remains at `models/runs/20260630_132617` for rollback.

---

## Untuned candidate (first comparison)

**Date:** 2026-09-28
**Candidate run:** `20260928_085217` (not promoted)
**Data:** Top five leagues, 2000/01 to 2025/26, 46,709 matches (ADR 005)
**Split:** train 2000/01–2021/22 (39,627 matches), validation 2022/23, test 2023/24, holdout 2024/25 and 2025/26 (ADR 007)
**Model:** XGBoost, default hyperparameters (learning rate 0.1, depth 6), 42 features, best iteration 21
**SHAP:** explanations generated for all 46,709 matches

## Summary

- On the current model's own 57 test matches, the candidate's log loss is 0.838 against 0.949. The paired bootstrap interval for the difference is −0.19 to −0.04, so the improvement is not noise.
- It beats training-set outcome frequencies in every league, in the 2023/24 test season and in the two holdout seasons.
- Bookmaker probabilities remain better by about 0.03 log loss overall, which is the realistic ceiling for results-only features.
- The promotion rule in ADR 007 passes. The candidate has not been promoted; that is a separate decision.
- Hyperparameters were not tuned. Early stopping at iteration 21 of 300 with depth 6 suggests shallower trees and a lower learning rate are worth testing, chosen by season cross-validation on training seasons only.


Lower is better for log loss, RPS and Brier. Rows without odds are
excluded so every forecast is scored on the same matches. Bookmaker
probabilities are a benchmark only; odds are never model inputs.

## Current model's own test matches (Premier League 2023/24)

**overall** (57 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.8381 | 0.1805 | 0.4842 | 0.667 |
| current | 0.9493 | 0.2160 | 0.5617 | 0.561 |
| bookmaker | 0.7677 | 0.1555 | 0.4339 | 0.754 |

Candidate minus current, paired bootstrap (negative favours candidate):

- log_loss: -0.1114 (95% interval -0.1885 to -0.0352, 2000 resamples)
- rps: -0.0356 (95% interval -0.0587 to -0.0116, 2000 resamples)

## Test seasons, all leagues

**overall** (1752 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9837 | 0.1965 | 0.5855 | 0.521 |
| priors | 1.0786 | 0.2293 | 0.6530 | 0.431 |
| bookmaker | 0.9548 | 0.1877 | 0.5669 | 0.550 |

**Bundesliga** (306 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9681 | 0.1916 | 0.5744 | 0.542 |
| priors | 1.0752 | 0.2279 | 0.6505 | 0.438 |
| bookmaker | 0.9464 | 0.1846 | 0.5597 | 0.542 |

**La Liga** (380 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9739 | 0.1900 | 0.5789 | 0.513 |
| priors | 1.0757 | 0.2239 | 0.6507 | 0.439 |
| bookmaker | 0.9473 | 0.1822 | 0.5630 | 0.553 |

**Ligue 1** (306 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 1.0456 | 0.2162 | 0.6298 | 0.467 |
| priors | 1.0979 | 0.2362 | 0.6670 | 0.392 |
| bookmaker | 1.0144 | 0.2062 | 0.6096 | 0.503 |

**Premier League** (380 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9369 | 0.1929 | 0.5512 | 0.566 |
| priors | 1.0603 | 0.2346 | 0.6404 | 0.461 |
| bookmaker | 0.9092 | 0.1839 | 0.5331 | 0.589 |

**Serie A** (380 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 1.0033 | 0.1946 | 0.5998 | 0.508 |
| priors | 1.0871 | 0.2248 | 0.6588 | 0.418 |
| bookmaker | 0.9668 | 0.1845 | 0.5760 | 0.550 |


## Holdout seasons, all leagues

**overall** (3504 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 1.0002 | 0.2049 | 0.5969 | 0.513 |
| priors | 1.0781 | 0.2321 | 0.6528 | 0.430 |
| bookmaker | 0.9719 | 0.1962 | 0.5781 | 0.534 |

**Bundesliga** (612 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9985 | 0.2052 | 0.5954 | 0.508 |
| priors | 1.0869 | 0.2362 | 0.6593 | 0.412 |
| bookmaker | 0.9698 | 0.1962 | 0.5762 | 0.534 |

**La Liga** (760 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9783 | 0.1989 | 0.5814 | 0.533 |
| priors | 1.0596 | 0.2259 | 0.6394 | 0.467 |
| bookmaker | 0.9585 | 0.1928 | 0.5675 | 0.545 |

**Ligue 1** (612 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 0.9948 | 0.2091 | 0.5926 | 0.529 |
| priors | 1.0592 | 0.2322 | 0.6395 | 0.464 |
| bookmaker | 0.9665 | 0.2011 | 0.5738 | 0.541 |

**Premier League** (760 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 1.0277 | 0.2113 | 0.6157 | 0.493 |
| priors | 1.0851 | 0.2329 | 0.6578 | 0.417 |
| bookmaker | 0.9947 | 0.2015 | 0.5951 | 0.516 |

**Serie A** (760 matches)

| Forecast | Log loss | RPS | Brier | Accuracy |
|---|---|---|---|---|
| candidate | 1.0001 | 0.2009 | 0.5982 | 0.501 |
| priors | 1.0978 | 0.2343 | 0.6669 | 0.393 |
| bookmaker | 0.9684 | 0.1904 | 0.5764 | 0.534 |


## Promotion verdict (ADR 007)

**Promote**

- pass: beats current on its test matches
- pass: beats priors on test seasons
- pass: beats priors on holdout seasons

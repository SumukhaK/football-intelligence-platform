# ADR 007 — Season-Based Split and Evaluation Protocol

**Status:** Accepted

**Supersedes:** [003](003-chronological-train-val-test-split.md) (split mechanism only)
**Superseded by:** —
**Amended by:** [017](017-refit-on-all-seasons-for-serving.md) (item 6: a serving refit may replace the served model; proposed)

## Context

ADR 003 split one season by row order: first 70% train, next 15% validation, last 15% test. It
rejected a season-based split only because the dataset had one season. ADR 005 expands the data to
26 seasons across five leagues.

With multiple leagues, a row-ratio split cuts through seasons at different points per league and
changes every time data is added. The current test set is 57 matches, too small to tell a real
improvement from noise.

## Decision

Split by whole seasons, keep chronological order, and evaluate primarily on probability quality.

1. **Splits**, all five leagues together:

   | Set | Seasons | Purpose |
   |---|---|---|
   | Train | 2000/01 – 2021/22 | Model fitting |
   | Validation | 2022/23 | Early stopping only |
   | Test | 2023/24 | Final comparison; same season as the current model |
   | Out-of-time | 2024/25, 2025/26 | Opened once, after the model is chosen |

2. **Cross-validation** is walk-forward by season: train on seasons up to N, validate on N+1.
   `TimeSeriesSplit` over rows is no longer used.
3. **Metrics.** Log loss and ranked probability score are primary. Brier score, accuracy, weighted F1
   and a calibration curve are secondary. All are reported overall and per league.
4. **Baselines** on the same test rows: always home win, class priors, the current model, and
   bookmaker implied probabilities from closing odds (normalised for overround).
5. **Like-for-like comparison with the current model** on both the 57 end-of-season 2023/24 EPL
   matches it was tested on and the full 2023/24 EPL season, with bootstrap confidence intervals.
6. **Promotion rule.** A new model replaces the current one only if its log loss is better on the
   2023/24 test set and on the out-of-time seasons, the improvement holds under bootstrap, and SHAP
   explanations still generate.
7. **Imputation** statistics are fitted on the training seasons only.

## Consequences

- ADR 003's principle stands: no random splits and no future data in training. Only the row-ratio
  mechanism is replaced. ADR 003 is marked Deprecated with a pointer here.
- `ChronologicalSplitter` and `TrainingConfig` change from ratios to season lists.
- Split boundaries are stable when new data arrives; adding 2026/27 later only adds a new
  out-of-time season.
- Evaluation reports grow: per-league tables, baselines and confidence intervals.
- Odds appear in evaluation code but must never appear in the feature list; a test enforces this.

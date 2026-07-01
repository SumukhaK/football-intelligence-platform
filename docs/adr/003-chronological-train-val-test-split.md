# ADR 003 — Chronological Train/Val/Test Split

**Status:** Accepted

## Context

Football match data has a strong temporal dependency: a team's form on match day N is influenced by all matches played before N. A random split would allow the model to "see the future" — training on matches from August while predicting January, then being validated on September matches. This is data leakage.

Options considered:

| Strategy | Description | Verdict |
|---|---|---|
| Random split | Shuffle and split 70/15/15 | Rejected — temporal leakage |
| **Chronological split** | Sort by date, take first 70% as train | Accepted |
| Walk-forward validation | Rolling window training | Correct but complex; save for Stage 8 |
| Season-based split | By season boundary | Only one season in dataset; inapplicable |

## Decision

Use a **chronological (time-ordered) split**: sort all matches by `match_date`, then take the first 70% as training, the next 15% as validation (used for early stopping), and the final 15% as test (held-out for final evaluation).

Split sizes on the 2023/24 EPL season (380 matches):
- Train: 266 rows (Aug 2023 – approx Feb 2024)
- Validation: 57 rows
- Test: 57 rows

## Consequences

- The test set represents the end-of-season matches, where teams' true form is well-established. This is a realistic evaluation scenario.
- Validation set is used only for XGBoost early stopping — not for hyperparameter search.
- Cross-validation uses `sklearn.model_selection.TimeSeriesSplit` on the train+val set to avoid leakage within the CV loop.
- Random splitting must never be used without documenting the justification in an ADR.

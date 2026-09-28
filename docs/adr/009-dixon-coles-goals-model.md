# ADR 009 — Add a Dixon-Coles Goals Model for Scoreline Predictions

**Status:** Proposed

**Supersedes:** —
**Superseded by:** —

## Context

The app shows only home/draw/away probabilities from the XGBoost classifier
(ADR 001). Users want likely scores, expected goals and goal markets such as
both teams to score or over 2.5 goals. The classifier cannot produce these
because it never models goals. The classifier also never picks a draw as the
most likely result, and draws are 25% of 2026/27 results so far.

Every match in the dataset already has full-time goals (ADR 005), and the raw
football-data.co.uk files carry over/under 2.5 goal odds that can serve as a
benchmark.

## Decision

Add a time-weighted Dixon-Coles goals model per league, alongside the
XGBoost classifier.

1. **Model.** Poisson goals for each side with team attack and defence
   strengths, a home advantage, the Dixon-Coles low-score correction ρ, and
   exponential time decay ξ. Fitted by maximum likelihood with
   `scipy.optimize`, with light L2 shrinkage toward the league mean.
2. **Role.** XGBoost keeps the headline H/D/A prediction. The goals model
   supplies scorelines, expected goals and goal markets. A blend replaces the
   headline only if it beats XGBoost on log loss for the test and holdout
   seasons (ADR 007 promotion rule).
3. **Freshness.** The goals model is refit whenever results are refreshed.
   It is evaluated with a rolling-origin backtest (refit before each
   matchweek) so evaluation matches serving.
4. **Schema.** `ProcessedMatch` gains optional `over_2_5_odds` and
   `under_2_5_odds`, used only as an evaluation benchmark, never as inputs.
5. **API.** A new `POST /insights` endpoint serves goals-model outputs. The
   `/predict` and `/explain` contracts are unchanged.
6. **Dependency.** `scipy`, already installed through scikit-learn, becomes
   an explicit dependency.

## Consequences

- Scoreline, expected goals and market outputs become available at negligible
  serving cost: a small parameter file and an 11×11 score grid per fixture.
- A second model artifact is versioned, registered and refreshed.
- Evaluation needs scoreline and market metrics and a rolling-origin harness.
- The app's result screen grows new sections, which need strings resources
  and previews (CLAUDE.md §7).
- Exact-score hit rates are inherently low, about 10–12% for the top pick.
  Copy and docs must present probabilities, not tips.

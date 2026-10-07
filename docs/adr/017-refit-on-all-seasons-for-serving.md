# ADR 017 — Refit on All Seasons for Serving

**Status:** Proposed

**Supersedes:** —
**Superseded by:** —
**Amends:** [007](007-season-based-split-and-evaluation.md) (item 6, promotion rule)

## Context

The served model, `20260928_123224`, was trained on 2000/01–2021/22 under the
ADR 007 season split. 2022/23 was used for early stopping, 2023/24 for the
test, and 2024/25–2025/26 were held out. That split is what makes its quoted
results honest, but it also means the model in production has never seen the
four most recent seasons, about 7,000 matches.

The usual practice is to choose a model on a frozen split, then refit the same
recipe on all the data before serving it. An external review raised this, and
on 2026-10-07 the decision was to try it: pin the features (done in PR 1),
refit on every season through 2025/26, and backtest the refit on 2026/27 so
far before deciding whether to serve it.

## Decision

1. **Two roles, two models.** The frozen-split run stays the *reporting*
   model: test, holdout and README figures are quoted from it. A *serving
   refit* copies its recipe and trains on every completed season.
2. **The recipe is copied, not re-tuned.** Same pinned features
   (`MODEL_FEATURES`), hyperparameters, seed and median imputer. The tree count
   is fixed at the reporting run's best iteration plus one (XGBoost counts
   from zero), and there is no early stopping, because nothing is held out.
   `python -m training.refit` does this and writes `runs/<version>/refit.json`
   with the purpose `serving refit`, the seasons used and the tree count.
3. **The refit never promotes itself.** It is written to `runs/` only;
   `latest/` and the registry, which the backend serves from, are unchanged.
   It is not added to the registry until it is served, because the backend
   reports the newest registry entry as the served version.
4. **Promotion rule (amends ADR 007 item 6).** Model choice still follows
   ADR 007 on the frozen split. A serving refit replaces the served model only
   if, on the played matches of the current season (each predicted from
   earlier matches only), the paired bootstrap interval for its log loss minus
   the reporting model's lies within ±0.02, the ADR 011 draw-tag check still
   holds, SHAP explanations still generate, and the owner approves the swap.
5. **No leakage.** The refit trains on completed seasons only. The backtest
   (`python -m evaluation.refit_backtest`) fails if the refit's last training
   match is on or after the first backtest match, or if the backtest season is
   one it trained on.

## Consequences

- The served model can use the latest completed seasons without losing an
  honest test set.
- There is no held-out score for the refit itself. Its only out-of-sample
  evidence is the current season so far, which is small, so the rule asks for
  "no worse", not "better".
- Every new completed season means another refit and backtest.
- The first refit, `20261007_154105`, is in
  [the refit report](../reports/refit-all-seasons.md). On 250 matches of
  2026/27 it is level with the reporting model.

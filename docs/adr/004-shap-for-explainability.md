# ADR 004 — Use SHAP TreeExplainer for Model Explainability

**Status:** Accepted

## Context

The Football Intelligence Platform requires per-prediction explanations for every match outcome prediction produced by the Stage 7 XGBoost model. The explanation layer must:

- Attribute each prediction to its contributing input features (local explanation).
- Summarise which features matter most across all predictions (global explanation).
- Produce structured, serialisable output consumable by the Stage 9 backend API and Stage 10 assistant.
- Run offline without external services.
- Be consistent: the same input must produce the same explanation.

Candidate approaches considered:

| Approach | Pros | Cons |
|---|---|---|
| XGBoost native feature importance | Zero extra dependencies; fast | Not prediction-specific; only weight/gain/cover, no per-sample attribution |
| LIME | Model-agnostic; local explanations | Stochastic (random perturbation); slow; not additive |
| **SHAP TreeExplainer** | Exact, fast, additive; integrates directly with XGBoost; industry standard | Requires `shap` library; multi-class shape requires care |
| Permutation importance | Easy to compute | Not per-prediction; can be slow |

## Decision

Use **SHAP** (`shap>=0.46.0`) with `shap.TreeExplainer` applied to the XGBoost classifier.

Rationale:
1. TreeExplainer exploits the XGBoost tree structure for exact (not approximate) Shapley value computation — fast enough for batch offline use.
2. Additive property guarantees: the sum of all SHAP values plus the base value equals the model output log-odds for each sample, giving a mathematically grounded explanation.
3. Both global (mean |SHAP| across all samples) and local (per-sample attribution) explanations come from the same computation.
4. The existing Stage 7 model artifact (`models/latest/model.joblib`) is compatible with `shap.TreeExplainer(model.booster)` without retraining.
5. SHAP plots (summary, waterfall, force, dependence) are well-established for communicating feature importance to non-technical stakeholders.

## Implementation

- `shap.TreeExplainer(model.booster)` — initialised once per model version, cached in memory.
- Imputer must be applied before SHAP: `X_imp = model.imputer.transform(X)`.
- Multi-class output shape: `(n_samples, n_features, n_classes)` using the `Explanation` object API.
- Per-prediction explanations select the SHAP slice for the predicted class.
- Global summary: mean absolute SHAP averaged over all samples and all classes.
- Matplotlib `Agg` backend for all plots (headless-safe, matches Stage 7 `evaluation/plots.py`).

## Consequences

- `shap>=0.46.0` and `numba>=0.60.0` added to `pyproject.toml`. `numpy` pinned to `<2.3.0` to satisfy numba 0.65.x constraints.
- `explainability/` package added under `ai/`. Contains: configuration, explainer, cache, serializers, plots, service, pipeline.
- Explainer is cached by model version to avoid redundant initialisation across service calls.
- All explanation artifacts (JSON + PNG) are written to `explanations/` directory.
- The explanation service is FastAPI-agnostic; it takes a `pd.DataFrame` of features and returns a Pydantic model.
- If the dataset grows beyond ~10 000 samples, batching the SHAP computation may be necessary.

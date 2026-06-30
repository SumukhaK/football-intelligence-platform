# Stage 8 — SHAP Explainability Pipeline

**Status:** Complete  
**Date:** 2026-06-30

## What was built

A SHAP-based explainability pipeline that consumes the Stage 7 XGBoost model and
produces structured per-prediction explanations alongside visualisation plots.

### Packages added

| Package | Purpose |
|---|---|
| `explainability/` | Core explainability pipeline |
| `explainability/plots/` | Matplotlib/SHAP plot generation |
| `explainability/services/` | FastAPI-agnostic ExplanationService |

### Key components

- **`SHAPExplainer`** — wraps `shap.TreeExplainer(model.booster)`, handles multi-class
  output normalisation to `(n_samples, n_features, n_classes)`.
- **`ExplainerCache`** — class-level dict keyed by model version string; avoids
  rebuilding the TreeExplainer on every request.
- **`ExplainabilityPipeline`** — CLI-runnable pipeline; loads model and feature matrix,
  computes SHAP, persists JSON and plots.
- **`ExplanationService`** — single-sample explanation entry point for the backend API.
- **`LocalExplanation` / `GlobalSummary`** — frozen Pydantic models carrying predictions,
  probabilities, confidence, per-feature SHAP contributions, and version metadata.

### Generated artifacts (on 380 Premier League matches)

| Artifact | Description |
|---|---|
| `global_summary.json` | Mean \|SHAP\| per feature; top features by outcome class |
| `local_explanations.json` | 10 per-sample explanations with full contributions |
| `summary_plot.png` | Beeswarm plot — feature impact distribution |
| `feature_importance.png` | Mean \|SHAP\| bar chart |
| `waterfall/` | 30 PNGs (10 samples × 3 classes) |
| `force/` | 30 PNGs (10 samples × 3 classes) |
| `dependence/` | 5 PNGs for the top 5 most impactful features |

## Test coverage

54 tests across 8 test modules:

| Module | Tests |
|---|---|
| `test_configuration.py` | 6 |
| `test_explainer.py` | 7 |
| `test_serializers.py` | 8 |
| `test_cache.py` | 6 |
| `test_service.py` | 9 |
| `test_plots.py` | 5 |
| `test_validation.py` | 4 |
| `test_pipeline.py` | 9 |

Total across all stages: **320 tests passing**.

## Dependencies added

| Package | Reason |
|---|---|
| `shap>=0.46.0` | SHAP TreeExplainer |
| `numba>=0.60.0` | Required by SHAP on Python 3.12 |
| `numpy>=1.26.0,<2.3.0` | numba 0.65.1 requires numpy < 2.3 |

## ADR

[ADR 004 — SHAP for Explainability](../adr/004-shap-for-explainability.md)

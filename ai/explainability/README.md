# explainability

SHAP-based explainability pipeline for the XGBoost match outcome model.

## Overview

This package computes SHAP values for every match prediction and persists structured
explanations alongside visualisation plots. It is designed to be consumed directly by
the FastAPI backend (Stage 4) via `ExplanationService`.

## Directory structure

```
explainability/
  __init__.py
  configuration.py       # ExplainabilityConfig (Pydantic, frozen)
  explainer.py           # SHAPExplainer wrapping shap.TreeExplainer
  cache.py               # ExplainerCache — in-process, keyed by model version
  serializers.py         # FeatureContribution, LocalExplanation, GlobalSummary
  pipeline.py            # ExplainabilityPipeline + CLI entry point
  plots/
    __init__.py
    shap_plots.py        # summary, feature importance, waterfall, force, dependence
  services/
    __init__.py
    explanation_service.py  # FastAPI-agnostic ExplanationService
```

## Usage

### CLI

Run from the `ai/` directory:

```bash
uv run python -m explainability.pipeline
```

Optional arguments:

| Flag | Default | Description |
|---|---|---|
| `--model-path` | `models/latest/model.joblib` | Path to trained model |
| `--feature-matrix` | `datasets/features/feature_matrix.parquet` | Feature matrix |
| `--explanations-dir` | `explanations` | Output directory |
| `--n-top-features` | `10` | Top features per explanation |
| `--n-local-samples` | `10` | Number of per-sample local explanations |
| `--n-dependence-plots` | `5` | Number of dependence plots |

### Python API

```python
from pathlib import Path
from explainability.services.explanation_service import ExplanationService

service = ExplanationService(Path("models/latest/model.joblib"))
explanation = service.explain(
    features=df,
    home_team="Arsenal",
    away_team="Chelsea",
)
print(explanation.predicted_result)   # "H" | "D" | "A"
print(explanation.confidence)         # max probability
print(explanation.top_positive_features[:3])
```

## Generated artifacts

After running the pipeline, `explanations/` contains:

```
explanations/
  global_summary.json        # Mean |SHAP| per feature, top features by class
  local_explanations.json    # Per-sample predictions with SHAP contributions
  summary_plot.png           # Beeswarm plot across all samples
  feature_importance.png     # Mean |SHAP| bar chart
  waterfall/
    sample_0000_H.png        # Waterfall plot for sample 0, home-win class
    ...
  force/
    sample_0000_H.png        # Force plot for sample 0, home-win class
    ...
  dependence/
    home_league_position.png # Dependence plot for top feature
    ...
```

## Design decisions

See [ADR 004](../../docs/adr/004-shap-for-explainability.md) for the rationale behind
choosing SHAP TreeExplainer over LIME or permutation importance.

Key choices:

- `shap.TreeExplainer(model.booster)` — operates on the raw XGBoost booster for speed.
- Imputer is applied before SHAP (`model.imputer.transform(X)`).
- Multi-class output is normalised to `(n_samples, n_features, n_classes)`.
- Matplotlib Agg backend is set at import time to avoid display errors in headless environments.
- `ExplainerCache` avoids rebuilding the TreeExplainer for repeated calls with the same model.

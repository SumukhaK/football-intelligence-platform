# Stage 8 Demo — SHAP Explainability Pipeline

## Prerequisites

- Stage 7 training pipeline has been run (`uv run python -m training.pipeline`).
- Working directory: `ai/`.

## Run the pipeline

```bash
uv run python -m explainability.pipeline
```

Expected output:

```
Model:          .../ai/models/latest/model.joblib
Feature matrix: .../ai/datasets/features/feature_matrix.parquet
Output:         .../ai/explanations

Samples:        380
Features:       42
Local explanations: 10
Artifacts:      .../ai/explanations
```

## Inspect a local explanation

```python
import json
from pathlib import Path

data = json.loads(Path("explanations/local_explanations.json").read_text())
ex = data[0]

print(f"Match: {ex['home_team']} vs {ex['away_team']}")
print(f"Predicted: {ex['predicted_result']} (confidence: {ex['confidence']:.2%})")
print(f"Home: {ex['probability_home']:.2%}  Draw: {ex['probability_draw']:.2%}  Away: {ex['probability_away']:.2%}")

print("\nTop positive features:")
for f in ex["top_positive_features"][:3]:
    print(f"  {f['feature_name']:35s} SHAP={f['shap_value']:+.4f}  value={f['feature_value']:.2f}")

print("\nTop negative features:")
for f in ex["top_negative_features"][:3]:
    print(f"  {f['feature_name']:35s} SHAP={f['shap_value']:+.4f}  value={f['feature_value']:.2f}")
```

## Inspect the global summary

```python
import json
from pathlib import Path

summary = json.loads(Path("explanations/global_summary.json").read_text())
print(f"Samples: {summary['n_samples']}, Features: {summary['n_features']}")

ranked = sorted(summary["mean_abs_shap_per_feature"].items(), key=lambda x: x[1], reverse=True)
print("\nTop 10 features by mean |SHAP|:")
for name, val in ranked[:10]:
    print(f"  {name:40s} {val:.4f}")
```

## Use ExplanationService directly

```python
from pathlib import Path
import pandas as pd
from explainability.services.explanation_service import ExplanationService

service = ExplanationService(Path("models/latest/model.joblib"))
features = pd.read_parquet("datasets/features/feature_matrix.parquet")
row = features.iloc[[0]]

result = service.explain(row, home_team="Arsenal", away_team="Chelsea")
print(result.predicted_result, result.confidence)
```

## Plots

Open the generated PNGs:

| File | What it shows |
|---|---|
| `explanations/summary_plot.png` | Beeswarm: each dot is one sample × one feature. Red = high feature value, blue = low. |
| `explanations/feature_importance.png` | Mean \|SHAP\| bar chart — global ranking. |
| `explanations/waterfall/sample_0000_H.png` | How feature contributions add up to the home-win prediction for match 0. |
| `explanations/force/sample_0000_H.png` | Force plot: features pushing prediction above/below baseline. |
| `explanations/dependence/home_league_position.png` | How home league position correlates with its SHAP contribution. |

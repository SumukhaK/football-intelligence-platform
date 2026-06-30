# evaluation

Metrics, cross-validation, plots, and structured report models for the XGBoost pipeline.

## Modules

| Module | Responsibility |
|---|---|
| `metrics.py` | `compute_metrics`, `compute_confusion_matrix` — sklearn wrappers |
| `cross_validation.py` | `run_cross_validation` — TimeSeriesSplit CV, returns `CVSummary` |
| `plots.py` | Headless Matplotlib plots (confusion matrix, feature importance) |
| `reports.py` | Frozen Pydantic models: `SplitMetrics`, `CVReport`, `EvaluationReport` |

## Matplotlib backend

`plots.py` calls `matplotlib.use("Agg")` at import time so plots render without a
display. This is safe on Windows, macOS, and headless CI environments.

## Report structure

`EvaluationReport` captures:
- Per-split metrics (train, val, test): accuracy, precision/recall/F1 weighted,
  log loss, ROC AUC OvR, confusion matrix.
- Cross-validation summary: mean and std of accuracy, F1, log loss across folds.
- Dataset metadata: class labels, feature count, split sizes.

The report is serialised to JSON alongside every model run.

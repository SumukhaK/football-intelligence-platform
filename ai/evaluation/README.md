# evaluation

Metrics, cross-validation, plots, and structured report models for the XGBoost pipeline.

## Modules

| Module | Responsibility |
|---|---|
| `metrics.py` | `compute_metrics`, `compute_confusion_matrix` — sklearn wrappers |
| `cross_validation.py` | `run_cross_validation` — TimeSeriesSplit CV, returns `CVSummary` |
| `plots.py` | Headless Matplotlib plots (confusion matrix, feature importance) |
| `draw_analysis.py` | Draw calibration, draw-rule trade-off and the ADR 011 draw-tag check per season block (CLI; see `docs/reports/draw-handling.md`) |
| `refit_backtest.py` | Scores a serving refit against the frozen-split model and the bookmaker on a season so far (CLI; ADR 017) |
| `goals_backtest.py` | Rolling-origin backtest for the goals model: refit before each matchweek, forecast that week |
| `goals_metrics.py` | Scoreline, goal-market and outcome metrics for goals-model forecasts |
| `goals_evaluation_cli.py` | Tunes and scores the goals model against a Poisson baseline, bookmakers and XGBoost |
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

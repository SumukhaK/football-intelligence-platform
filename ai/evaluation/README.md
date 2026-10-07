# evaluation

Metrics, cross-validation, plots, and structured report models for the XGBoost pipeline.

## Modules

| Module | Responsibility |
|---|---|
| `metrics.py` | `compute_metrics`, `compute_confusion_matrix` — sklearn wrappers |
| `cross_validation.py` | `run_cross_validation` (TimeSeriesSplit over rows) and `run_season_cross_validation` (walk-forward by season, ADR 007); both return `CVSummary` |
| `comparison.py` | Log loss, RPS, Brier, accuracy; bookmaker implied probabilities (normalised); class-prior baseline; paired bootstrap deltas |
| `compare_models.py` | Compares a candidate run with the served model, priors and bookmakers per league, and applies the ADR 007 promotion rule (CLI) |
| `comparison_report.py` | Markdown rendering for `compare_models` reports |
| `in_season.py` | Scores a model on a season in progress, each match from features built only on earlier matches, against an Elo-only baseline, priors and Bet365 (benchmark only), with bootstrap ranges |
| `in_season_cli.py` | Downloads the current season's played matches, or rescores a saved feature matrix with `--features`, and runs `in_season` (CLI; see `docs/reports/in-season-2026-27.md`) |
| `plots.py` | Headless Matplotlib plots (confusion matrix, feature importance) |
| `draw_analysis.py` | Draw calibration, draw-rule trade-off and the ADR 011 draw-tag check per season block (CLI; see `docs/reports/draw-handling.md`) |
| `refit_backtest.py` | Scores a serving refit against the frozen-split model and the bookmaker on a season so far (CLI; ADR 017) |
| `goals_backtest.py` | Rolling-origin backtest for the goals model: refit before each matchweek, forecast that week |
| `goals_metrics.py` | Scoreline, goal-market and outcome metrics for goals-model forecasts |
| `goals_evaluation_cli.py` | Tunes and scores the goals model against a Poisson baseline, bookmakers and XGBoost |
| `assistant_grounding.py` | Asks the assistant for upcoming fixtures' predictions and checks it quotes `/v2/predict` without inventing numbers (CLI; ADR 018) |
| `assistant_abstention.py` | Checks the assistant answers questions its knowledge base covers and says "I don't know" to ones it doesn't (CLI) |
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

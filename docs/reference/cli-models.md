# Model Training and Evaluation Commands

Run from `ai/` unless a section says otherwise. [CLI index](cli.md). Shell examples use POSIX syntax; on Windows set environment variables with `$env:NAME="value"` before running the command.

## Model Training

### `python -m training.tuning`

Searches XGBoost hyperparameters by season walk-forward CV on training seasons only, so validation, test and holdout seasons stay unseen (ADR 007).

**Usage:**
```sh
uv run python -m training.tuning --feature-matrix ../datasets/features/top5/feature_matrix.parquet   --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26
```

| Flag | Default | Description |
|---|---|---|
| `--max-depths N ...` | `2 3 4` | Tree depths to try. |
| `--learning-rates LR ...` | `0.03 0.05 0.1` | Learning rates to try. |
| `--n-estimators N ...` | `100 200 400` | Tree counts to try. |
| `--cv-folds N` | `5` | Number of final training seasons used as validation folds. |
| `--output PATH` | `models/tuning/tuning_results.json` | Where to write ranked results. |

Prints every setting ranked by mean CV log loss.

---

### `python -m evaluation.in_season_cli`

Scores the served model on every played match of a season in progress. Each match is predicted from features built only from earlier matches; the model is not retrained. Dry run unless `--confirm` is given.

```sh
uv run python -m evaluation.in_season_cli --season 2627 --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--season CODE` | `2627` | Season in progress. |
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Leagues to score. |
| `--history PATH` | newest `match_results_top5_v*.csv` | Completed-season history. |
| `--model PATH` | `models/latest/model.joblib` | Model to score. |
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--output-dir DIR` | `models/backtests/<season>_<date>` | Where outputs go. |
| `--features PATH` | none | Rescore a saved run's `features/feature_matrix.parquet` instead of downloading. |
| `--through DATE` | none | Score only matches up to this date (`YYYY-MM-DD`). |
| `--confirm` | off | Download and score. |

The report scores the model against an Elo-only baseline (logistic regression on the pre-match Elo gap, fitted on earlier seasons), outcome-frequency priors and Bet365 (pre-match odds with the margin removed; a benchmark only). It adds overall 95% bootstrap ranges for accuracy, log loss, RPS and Brier, and paired bootstraps of the model minus Bet365 and minus Elo only.

Raw snapshots are stored once per division per day under `raw/football_data/match_results_in_progress/`. Outputs: `report.md`, `report.json` and `predictions.csv` (one line per match with probabilities, pick and result).

---

### `python -m evaluation.compare_models`

Scores a candidate run against the current model, bookmaker probabilities and training-set outcome frequencies (ADR 007), then applies the promotion rule. Nothing is promoted.

**Usage:**
```sh
uv run python -m evaluation.compare_models --candidate-run models/runs/<version>   [--feature-matrix PATH] [--current-model PATH] [--current-feature-matrix PATH]
```

| Flag | Default | Description |
|---|---|---|
| `--candidate-run DIR` | required | Run directory with `model.joblib` and `config.json` from a season-split run. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | Feature matrix the candidate was trained on. |
| `--current-model PATH` | `models/latest/model.joblib` | The model currently served. |
| `--current-feature-matrix PATH` | `../datasets/features/feature_matrix.parquet` | Feature matrix the current model was trained on. |

**Outputs:** `comparison.json` and `comparison.md` in the candidate run directory: log loss, RPS, Brier and accuracy per league for the test and holdout seasons, a paired bootstrap of candidate minus current on the current model's own test matches, and the promotion verdict.

---

### `python -m evaluation.goals_evaluation_cli`

Tunes and backtests the goals model (ADR 009) with a rolling-origin backtest: tunes on the validation season, then forecasts the test season, the holdout seasons and the season in progress, refitting before every matchweek. Compares against a plain Poisson baseline, bookmakers' over 2.5 odds and the served XGBoost model.

```sh
uv run python -m evaluation.goals_evaluation_cli
```

| Flag | Default | Description |
|---|---|---|
| `--matches CSV` | newest live dataset in `../datasets/processed/football_data` | Match history. |
| `--model PATH` | `models/latest/model.joblib` | Served XGBoost model to compare with. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | That model's feature matrix. |
| `--in-season-xgb CSV` | `models/backtests/2627_20260928_model123224/predictions.csv` | In-season XGBoost predictions from `evaluation.in_season_cli`. |
| `--in-season SEASON` | `2026/27` | Season in progress. |
| `--output-dir DIR` | `models/evaluation/goals` | Where outputs go. |

**Outputs:** `goals_evaluation.json` and `goals_forecasts.csv`.

---

### `python -m evaluation.draw_analysis`

Checks how well the model's draw probabilities are calibrated, and what a "pick a draw when it is close to the favourite" rule would cost in accuracy, per season block. Writes JSON and prints `Wrote <path>`.

| Flag | Default | Description |
|---|---|---|
| `--model PATH` | `models/latest/model.joblib` | Model to analyse. |
| `--feature-matrix PATH` | `../datasets/features/top5/feature_matrix.parquet` | That model's feature matrix. |
| `--in-season CSV` | none | `predictions.csv` from `evaluation.in_season_cli`. |
| `--output PATH` | `models/evaluation/draw_analysis.json` | Report path. |

---

### Experiments

Two one-off experiments that retrain with the served model's configuration and compare log loss with a paired bootstrap. Neither takes any options, and neither changes the served model. Both read `../datasets/features/top5/feature_matrix.parquet` and `models/latest/config.json`.

```sh
# Do draw-oriented features help? (docs/reports/draw-handling.md)
uv run python -m scripts.draw_feature_experiment

# Do Champions League rest days, rolling xG or FIFA ratings help? (docs/reports/kaggle-extras.md)
uv run python -m scripts.kaggle_extras_experiment
```

`scripts.kaggle_extras_experiment` also needs the Kaggle source files in `../datasets/raw/kaggle/`. Both print their results to the console.

---

### `python -m training.pipeline`

Loads the feature matrix, splits it, trains an XGBoost classifier with early stopping, runs cross-validation, evaluates on all splits, generates a model card, and registers the run.

The default split is chronological (70/15/15). The frozen reporting recipe uses `--split-strategy season`, which assigns whole seasons to each split (ADR 007). The served refit later trains that recipe on all completed seasons (ADR 017). See the first example below.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--feature-matrix PATH` | `datasets/features/feature_matrix.parquet` | Path to the feature matrix Parquet file. |
| `--models-dir DIR` | `models` | Root directory for model artifacts. |
| `--n-estimators N` | `300` | Maximum number of XGBoost trees. |
| `--learning-rate LR` | `0.1` | XGBoost learning rate (eta). |
| `--max-depth DEPTH` | `6` | Maximum tree depth. |
| `--seed SEED` | `42` | Random seed for reproducibility. |
| `--split-strategy {chronological,season}` | `chronological` | `season` assigns whole seasons (ADR 007) and uses season walk-forward CV. The served model uses `season`. |
| `--val-seasons S ...` | — | Validation seasons for `season`, e.g. `2022/23`. Training uses every earlier season. |
| `--test-seasons S ...` | — | Test seasons for `season`. |
| `--holdout-seasons S ...` | — | Seasons never used in training or model selection. |
| `--no-promote` | off | Write only `models/runs/<version>/`; leave `models/latest/`, the global report and the registry untouched. |

**Examples:**
```sh
# Frozen reporting configuration used as the serving refit recipe
uv run python -m training.pipeline \
  --feature-matrix ../datasets/features/top5/feature_matrix.parquet \
  --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 \
  --holdout-seasons 2024/25 2025/26 \
  --max-depth 3 --learning-rate 0.03 --n-estimators 400

# Candidate variant, without replacing the served model
uv run python -m training.pipeline   --feature-matrix ../datasets/features/top5/feature_matrix.parquet   --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24   --holdout-seasons 2024/25 2025/26 --no-promote

# Default configuration (chronological split)
uv run python -m training.pipeline

```

**Inputs:** A feature matrix produced by the feature engineering pipeline. The default path, `datasets/features/feature_matrix.parquet`, is relative to `ai/`; the served model uses `../datasets/features/top5/feature_matrix.parquet`.

**Outputs:**

| File | Location | Description |
|---|---|---|
| Model bundle | `models/runs/<ts>/model.joblib` | XGBClassifier + imputer + label encoder |
| Config | `models/runs/<ts>/config.json` | Training hyperparameters |
| Metrics | `models/runs/<ts>/metrics.json` | Per-split metrics (accuracy, F1, log loss, ROC AUC) |
| Evaluation report | `models/runs/<ts>/evaluation_report.json` | Full report including CV results |
| Model card | `models/runs/<ts>/model_card.md` | Human-readable model documentation |
| Feature importance | `models/runs/<ts>/plots/feature_importance.png` | Top-N feature importance bar chart |
| Confusion matrix | `models/runs/<ts>/plots/confusion_matrix.png` | Test set confusion matrix |
| Latest | `models/latest/` | Copy of all artifacts from the most recent promoted run |
| Global eval report | `models/evaluation/evaluation_report.json` | Updated on every promoted run |
| Registry | `models/registry.json` | Appended with a new `ModelEntry` on every promoted run |

With `--no-promote`, only `models/runs/<ts>/` is written.

**Exit codes:** `0` on success, `1` on any failure (printed as `ERROR: <reason>`).

**Output:** the feature matrix path, models directory and hyperparameters, then:

```
Version:        <timestamp>
Best iteration: <N>
Features used:  42
Test accuracy:  <value>
Test F1:        <value>
Test log-loss:  <value>
Run dir:        <path>/models/runs/<timestamp>
Promoted:       yes
```

`Promoted:` reads `no` when `--no-promote` is given. For reference, the season-split run `20260928_123224` has test accuracy 0.5245, test log loss 0.9762 and best iteration 167 (`models/runs/20260928_123224/model_card.md`). The served model, `20261007_154105`, is a refit of that run (ADR 017; see below).

---

### Serving refit (ADR 017)

Three steps retrain a season-split run on every completed season and serve it. Each prints `ERROR: <reason>` and exits with code 1 on failure.

```sh
# 1. Retrain on all seasons up to --last-season (default 2025/26) with the
#    source run's settings and best tree count. Writes models/runs/<v>/ only.
uv run python -m training.refit --source-run models/runs/20260928_123224

# 2. Score the refit and the source run on the season so far, using the
#    features saved by evaluation.in_season_cli
uv run python -m evaluation.refit_backtest   --rows models/backtests/<in-season run>/features/feature_matrix.parquet   --frozen-run models/runs/20260928_123224 --refit-run models/runs/<v>

# 3. Copy the refit to models/latest/ and register it with its backtest scores
uv run python -m training.promote_refit --run models/runs/<v>   --backtest models/backtests/refit_<v>/report.json
```

`evaluation.refit_backtest` also takes `--season` (default `2026/27`), `--through` (default `2026-09-20`) and `--output-dir`. `training.promote_refit` takes `--models-dir` (default `models`). The refit has no test season, so the registry holds its current-season scores (`accuracy_2026_27`, ...), and test and holdout results stay quoted from the source run.

---

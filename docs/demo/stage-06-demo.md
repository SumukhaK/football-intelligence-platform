# Demo: Stage 6 — Feature Engineering Pipeline

Demonstrate the composable feature engineering pipeline producing a validated 42-column feature matrix from raw match data.

**Approximate demo time:** 3 minutes

---

## Objective

Show that the platform can:
- Execute 9 independent, composable feature generators in dependency order.
- Produce 42 pre-match engineered features with no data leakage.
- Validate the feature matrix before persisting it.
- Generate reproducible output in under 2 seconds.

---

## Prerequisites

- `ai/` workspace set up: `uv sync --extra dev`
- Stage 5 complete: `datasets/processed/football_data/` must contain at least one `ProcessedMatch` CSV.
  - If running Stage 5 live is not convenient, the processed CSV included in `datasets/processed/` (if present) may be used directly.

---

## Commands

All commands run from the `ai/` directory.

### 1. Show the feature generators

```sh
# macOS/Linux
ls feature_engineering/features/

# Windows PowerShell
Get-ChildItem feature_engineering\features\
```

You should see 9 feature generator files.

### 2. Show the tests pass

```sh
uv run pytest tests/feature_engineering/ -v
```

Expected: 142 tests pass.

### 3. Run the feature engineering pipeline

```sh
uv run python -m feature_engineering.pipeline
```

### 4. Inspect the feature matrix

```sh
uv run python -c "
import pandas as pd
df = pd.read_parquet('../datasets/features/feature_matrix.parquet')
print('Shape:', df.shape)
print('Feature columns:', [c for c in df.columns if c not in ['match_date','season','competition','home_team','away_team','result','full_time_home_goals','full_time_away_goals']])
"
```

### 5. Show the feature metadata

```sh
# macOS/Linux
cat ../datasets/features/feature_metadata.json

# Windows PowerShell
Get-Content ..\datasets\features\feature_metadata.json
```

---

## Expected Output

```
Input:      datasets/processed/football_data/match_results_v<timestamp>.csv
Output dir: datasets/features

Pipeline complete in 1.8s
Rows: 380 in -> 380 out
Feature columns: 67
Validation: PASSED

Outputs written to: datasets/features
```

---

## Verification

After running, confirm:

- [ ] `datasets/features/feature_matrix.parquet` exists
- [ ] `datasets/features/feature_metadata.json` exists
- [ ] The feature matrix has 380 rows and 67 columns (42 feature columns + identity columns)
- [ ] Validation prints `PASSED`
- [ ] Exit code is 0

---

## What to Highlight

**Architecture points:**
- `BaseFeature` ABC enforces a single `compute(df) → df` contract. Each generator is independently testable.
- `FeatureRegistry` uses Kahn's topological sort to determine execution order from declared `dependencies`. `StrengthOfScheduleFeature` depends on `EloRatingFeature` — this is declared, not hardcoded.
- Cycles or missing dependencies raise a `RegistryError` at registration time, not at runtime.
- `build_team_match_view()` doubles the DataFrame to one row per `(match, team)`, enabling vectorised `groupby + transform` for rolling stats — no row-by-row iteration.

**AI engineering points:**
- All rolling and expanding features apply `.shift(1)` before computing. Row 0 per team always yields NaN — the correct behaviour for a team's first match with no prior history.
- The pipeline filters the feature matrix to 42 pre-match columns before training. Post-match statistics (`full_time_home_goals`, `result`, etc.) are excluded at training time to prevent data leakage.
- NaN imputation (training-set median) happens in the training pipeline, not here — preserving the integrity of the feature matrix.

**Feature summary (42 pre-match features):**

| Category | Count | Examples |
|---|---|---|
| Rolling form | 8 | `home_points_last5`, `away_wins_last10` |
| Goal statistics | 6 | `home_goals_scored_last5`, `away_goals_conceded_last10` |
| Home/away advantage | 4 | `home_win_rate`, `away_draw_rate` |
| Rest days | 2 | `home_rest_days`, `away_rest_days` |
| Head-to-head | 5 | `h2h_home_wins`, `h2h_draw_rate` |
| League position | 6 | `home_league_position`, `away_points` |
| Elo ratings | 2 | `home_elo`, `away_elo` |
| Strength of schedule | 9 | `home_sos_5`, `away_sos_10` |

---

## Troubleshooting

**`FileNotFoundError: No processed CSV found`:** Run Stage 5 first: `uv run python -m scripts.ingest_football_data`

**`Validation: FAILED`:** Review the warning messages. Small numbers of NaN values in first-match rows are expected. Widespread NaN values indicate a feature generator bug.

**Feature column count differs from 42:** Run `uv run pytest tests/feature_engineering/` — a failing test will identify the problem.

---

## Approximate Demo Time

| Step | Time |
|---|---|
| Show feature generators | 30 seconds |
| Run tests | 90 seconds |
| Run pipeline | 5 seconds |
| Inspect feature matrix | 30 seconds |
| Explain architecture | 90 seconds |
| **Total** | **~3 minutes** |

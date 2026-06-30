# Stage 06 — Feature Engineering Pipeline: Summary

**Date:** 2026-06-30
**Branch:** `feature/ai-stage6-feature-engineering`
**Commit:** `feat(ai): implement feature engineering pipeline`
**PR target:** `develop`

---

## Executive Summary

Stage 06 delivers a production-quality feature engineering pipeline. It loads the canonical `ProcessedMatch` dataset (380 rows), executes 9 feature modules in dependency order, merges the results into a 67-column feature matrix, validates the output, and persists three artefacts to `datasets/features/`. The pipeline runs in under 2 seconds on the 2023/24 EPL season. All 217 unit tests pass. Ruff, Black, and MyPy all report clean.

---

## Architecture Decisions

### 1. BaseFeature ABC with a single compute() contract

Each feature is a self-contained class implementing `BaseFeature`. The pipeline passes the full accumulated DataFrame to every `compute()` call, which means later features can read columns produced by earlier ones without any special coupling mechanism. The contract is: receive all current columns, return only new columns.

**Consequence:** Features with dependencies (e.g. `StrengthOfScheduleFeature` needing Elo columns) work transparently as long as the registry orders them correctly.

### 2. FeatureRegistry with Kahn's topological sort

`FeatureRegistry.get_ordered()` uses Kahn's algorithm to produce a dependency-respecting execution order. Features declare `dependencies` as a list of feature names. The registry raises `RegistryError` on cycles or missing dependencies at registration time.

**Consequence:** Adding a new feature with dependencies requires only declaring them in the class — no manual ordering in the pipeline.

### 3. build_team_match_view() for per-team rolling statistics

Rather than iterating row-by-row for rolling stats, the pipeline uses a "team match view" DataFrame that doubles the row count to one row per `(match, team)`. This allows `groupby('team').transform(...)` for O(n) rolling computations. The `_original_idx` column maps back to the original index for joining.

**Consequence:** Rolling features are vectorised and fast. The helper is shared across all rolling feature classes.

### 4. Data leakage prevention via shift(1)

All rolling and expanding features apply `.shift(1)` before `.rolling()` or `.expanding()`. Row 0 for any team always yields `NaN` for rolling features, which is the correct behaviour: no prior data exists.

**Consequence:** The feature matrix is safe to use for model training without additional leakage checks.

### 5. Parquet output with pyarrow

The feature matrix is written as Parquet using `pyarrow`. This was added as a dependency in `pyproject.toml`. Parquet preserves column dtypes and compresses well, making it suitable for training and analysis.

---

## Files Created

| File | Purpose |
|---|---|
| `ai/feature_engineering/base.py` | `BaseFeature` ABC; `build_team_match_view()` helper |
| `ai/feature_engineering/registry.py` | `FeatureRegistry` with topological sort; `RegistryError` |
| `ai/feature_engineering/validators.py` | `validate_canonical_input()`, `validate_feature_matrix()` |
| `ai/feature_engineering/metadata.py` | `FeatureMetadata`, `FeatureReport`, `FeatureExecutionRecord` |
| `ai/feature_engineering/pipeline.py` | `FeaturePipeline`, `build_default_registry()`, CLI `main()` |
| `ai/feature_engineering/features/rolling_form.py` | `RollingFormFeature` |
| `ai/feature_engineering/features/goal_statistics.py` | `GoalStatisticsFeature` |
| `ai/feature_engineering/features/home_advantage.py` | `HomeAdvantageFeature` |
| `ai/feature_engineering/features/away_form.py` | `AwayFormFeature` |
| `ai/feature_engineering/features/rest_days.py` | `RestDaysFeature` |
| `ai/feature_engineering/features/head_to_head.py` | `HeadToHeadFeature` |
| `ai/feature_engineering/features/league_position.py` | `LeaguePositionFeature` |
| `ai/feature_engineering/features/elo_rating.py` | `EloRatingFeature` |
| `ai/feature_engineering/features/strength_of_schedule.py` | `StrengthOfScheduleFeature` |
| `ai/feature_engineering/features/__init__.py` | Re-exports all 9 feature classes |
| `ai/feature_engineering/README.md` | Module documentation |
| `ai/tests/feature_engineering/conftest.py` | Shared fixtures: `sample_matches`, `elo_enriched_matches` |
| `ai/tests/feature_engineering/test_registry.py` | 8 registry tests |
| `ai/tests/feature_engineering/test_validation.py` | 8 validator tests |
| `ai/tests/feature_engineering/test_metadata.py` | 4 metadata model tests |
| `ai/tests/feature_engineering/test_rolling_form.py` | 9 rolling form tests |
| `ai/tests/feature_engineering/test_goal_statistics.py` | 5 goal statistics tests |
| `ai/tests/feature_engineering/test_home_advantage.py` | 4 home advantage tests |
| `ai/tests/feature_engineering/test_rest_days.py` | 4 rest days tests |
| `ai/tests/feature_engineering/test_head_to_head.py` | 5 head-to-head tests |
| `ai/tests/feature_engineering/test_elo_rating.py` | 5 Elo rating tests |
| `ai/tests/feature_engineering/test_league_position.py` | 6 league position tests |
| `ai/tests/feature_engineering/test_strength_of_schedule.py` | 7 strength-of-schedule tests |
| `ai/tests/feature_engineering/test_pipeline.py` | 9 pipeline integration tests |
| `docs/reports/stage-06-summary.md` | This document |

### Updated Files

| File | Change |
|---|---|
| `ai/pyproject.toml` | Added `pyarrow>=24.0.0` dependency |
| `ai/README.md` | Added Feature Engineering Pipeline section |

---

## Tests Added

| File | Tests | Coverage |
|---|---|---|
| `test_registry.py` | 8 | Register, duplicate detection, get, missing feature, topological sort |
| `test_validation.py` | 8 | Canonical input validation, feature matrix validation, warnings |
| `test_metadata.py` | 4 | FeatureMetadata, FeatureReport construction and frozen behaviour |
| `test_rolling_form.py` | 9 | Rolling win/point counts, leakage, first-match NaN |
| `test_goal_statistics.py` | 5 | Rolling goal means, first-match NaN |
| `test_home_advantage.py` | 4 | Expanding home stats, first-match NaN |
| `test_rest_days.py` | 4 | Rest day calculation, first-match NaN |
| `test_head_to_head.py` | 5 | H2H counts, venue-neutral, first-match zero |
| `test_elo_rating.py` | 5 | Elo update after win/loss/draw, index alignment |
| `test_league_position.py` | 6 | Position, points, matches played, pre-match recording |
| `test_strength_of_schedule.py` | 7 | Opponent Elo rolling mean, dependency on elo_rating |
| `test_pipeline.py` | 9 | Output files, column completeness, metadata/report validity, empty input |
| **New total** | **75** | |

**Grand total: 217 passed, 1 integration test deselected.**

---

## Feature Matrix

| Metric | Value |
|---|---|
| Input rows | 380 |
| Output rows | 380 |
| Output columns | 67 (25 canonical + 32 feature + 10 optional match stats) |
| Pipeline duration | ~1.5s |
| Validation | PASSED |
| NaN total % | ~5.5% (first-match rows and missing rest-day data) |

---

## Build Verification

```
uv run black --check .                → 75 files unchanged
uv run ruff check .                   → All checks passed
uv run mypy .                         → Success: no issues found in 75 source files
uv run pytest -m "not integration"    → 217 passed in 3.83s
uv run python -m feature_engineering.pipeline
  → 380 rows in -> 380 out, 67 feature columns, Validation: PASSED (1.55s)
```

---

## CLI Output

```
Input:      .../datasets/processed/football_data/match_results_v20260630_090657.csv
Output dir: .../datasets/features

Pipeline complete in 1.55s
Rows: 380 in -> 380 out
Feature columns: 67
Validation: PASSED

Outputs written to: .../datasets/features
```

---

## Known Limitations

1. **Single season only.** The pipeline operates on one canonical CSV. Multi-season feature computation (e.g. Elo carry-over between seasons) is not implemented.

2. **First-match NaN.** Rolling features yield `NaN` for a team's first match. The model training step must handle these (imputation or filtering).

3. **League position uses full-season table.** The league position feature computes position from all matches in the dataset, not per-competition. If the dataset contains multiple competitions, positions would be mixed.

4. **Elo resets each pipeline run.** Elo ratings start at 1500 for every team on every pipeline run. There is no persistence across seasons.

---

## Next Stage Recommendation

**Stage 7 — XGBoost Model Training:** train a match outcome classifier on the feature matrix. Target: `result` (H/D/A). Attach SHAP explanations to every prediction. Write the trained model to `models/`. Evaluation script must track accuracy, log-loss, and per-class F1 before any model is merged.

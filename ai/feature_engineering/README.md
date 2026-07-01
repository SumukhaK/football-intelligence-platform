# feature_engineering

Transforms the canonical `ProcessedMatch` dataset into a model-ready feature matrix.

---

## Entry Point

```sh
# Auto-detects the latest canonical CSV in datasets/processed/football_data/
python -m feature_engineering.pipeline

# Explicit paths
python -m feature_engineering.pipeline \
  --input datasets/processed/football_data/match_results_v<version>.csv \
  --output-dir datasets/features
```

---

## Output

All outputs are written to `datasets/features/`:

| File | Description |
|---|---|
| `feature_matrix.parquet` | Feature matrix: canonical columns + 32 engineered feature columns |
| `feature_metadata.json` | `FeatureMetadata`: pipeline version, feature names/versions, row and column counts |
| `feature_generation_report.json` | `FeatureReport`: per-feature timing, validation result, dataset statistics |

---

## Module Structure

```
feature_engineering/
  base.py           # BaseFeature ABC and build_team_match_view() helper
  registry.py       # FeatureRegistry with Kahn's topological sort
  validators.py     # validate_canonical_input(), validate_feature_matrix()
  metadata.py       # FeatureMetadata, FeatureReport, FeatureExecutionRecord
  pipeline.py       # FeaturePipeline, build_default_registry(), CLI main()
  features/
    __init__.py             # Re-exports all 9 feature classes
    rolling_form.py         # RollingFormFeature
    goal_statistics.py      # GoalStatisticsFeature
    home_advantage.py       # HomeAdvantageFeature
    away_form.py            # AwayFormFeature
    rest_days.py            # RestDaysFeature
    head_to_head.py         # HeadToHeadFeature
    league_position.py      # LeaguePositionFeature
    elo_rating.py           # EloRatingFeature
    strength_of_schedule.py # StrengthOfScheduleFeature (depends on elo_rating)
```

---

## Feature Reference

| Feature | Class | Columns Produced |
|---|---|---|
| `rolling_form` | `RollingFormFeature` | 8: home/away win and points counts over last 5/10 matches |
| `goal_statistics` | `GoalStatisticsFeature` | 12: home/away rolling mean goals scored/conceded/diff |
| `home_advantage` | `HomeAdvantageFeature` | `home_win_pct`, `home_ppg` |
| `away_form` | `AwayFormFeature` | `away_win_pct`, `away_ppg` |
| `rest_days` | `RestDaysFeature` | `home_rest_days`, `away_rest_days` |
| `head_to_head` | `HeadToHeadFeature` | `h2h_meetings`, `h2h_home_wins`, `h2h_away_wins`, `h2h_draws` |
| `league_position` | `LeaguePositionFeature` | 6: home/away position, points, matches played at kick-off |
| `elo_rating` | `EloRatingFeature` | `home_elo_before`, `away_elo_before` |
| `strength_of_schedule` | `StrengthOfScheduleFeature` | 4: home/away rolling avg opponent Elo over last 5/10 matches |

---

## Architecture Notes

### BaseFeature

Every feature implements `BaseFeature`:

```python
class BaseFeature(ABC):
    @property @abstractmethod def name(self) -> str: ...
    @property @abstractmethod def version(self) -> str: ...
    @property def dependencies(self) -> list[str]: return []
    @property @abstractmethod def output_columns(self) -> list[str]: ...
    @abstractmethod def compute(self, df: pd.DataFrame) -> pd.DataFrame: ...
```

`compute()` receives the full accumulated DataFrame (including columns produced by prior features) and returns a DataFrame of new columns aligned to the input index.

### FeatureRegistry

`FeatureRegistry.get_ordered()` uses Kahn's topological sort to order features respecting `dependencies`. `StrengthOfScheduleFeature` declares `dependencies = ["elo_rating"]`, so `EloRatingFeature` always runs first.

### Data Leakage Prevention

All rolling statistics use `.shift(1)` before `.rolling(n)` so each row only observes data from prior matches. First-match rows yield `NaN` for rolling features.

### build_team_match_view()

Expands the match DataFrame to one row per `(match, team)` — doubling the row count — so per-team rolling stats can be computed with simple `groupby('team').transform(...)` calls. The `_original_idx` column maps back to the original DataFrame index.

---

## Adding a New Feature

1. Create `features/my_feature.py` implementing `BaseFeature`.
2. Declare `dependencies` if the feature needs columns from another feature.
3. Export the class from `features/__init__.py`.
4. Register it in `build_default_registry()` in `pipeline.py`.
5. Write tests in `tests/feature_engineering/test_my_feature.py`.
6. Write an ADR in `docs/adr/` if the feature introduces new data assumptions.

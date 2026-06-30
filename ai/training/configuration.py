"""Training configuration for the XGBoost match outcome model."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Columns present after Stage 6 that must never be used as features.
# They are either post-match statistics (leakage) or metadata identifiers.
_POST_MATCH_COLUMNS: list[str] = [
    "full_time_home_goals",
    "full_time_away_goals",
    "half_time_home_goals",
    "half_time_away_goals",
    "home_shots",
    "away_shots",
    "home_shots_on_target",
    "away_shots_on_target",
    "home_fouls",
    "away_fouls",
    "home_corners",
    "away_corners",
    "home_yellow_cards",
    "away_yellow_cards",
    "home_red_cards",
    "away_red_cards",
    "home_odds",
    "draw_odds",
    "away_odds",
]

_METADATA_COLUMNS: list[str] = [
    "match_date",
    "season",
    "competition",
    "home_team",
    "away_team",
]


def _default_exclude() -> list[str]:
    """Return the default list of columns to exclude from feature training."""
    return _METADATA_COLUMNS + _POST_MATCH_COLUMNS


class TrainingConfig(BaseModel):
    """Frozen configuration for a single XGBoost training run."""

    model_config = {"frozen": True}

    # XGBoost hyperparameters
    learning_rate: float = Field(default=0.1, gt=0.0)
    max_depth: int = Field(default=6, ge=1)
    n_estimators: int = Field(default=300, ge=1)
    subsample: float = Field(default=0.8, gt=0.0, le=1.0)
    colsample_bytree: float = Field(default=0.8, gt=0.0, le=1.0)
    random_seed: int = 42
    early_stopping_rounds: int = Field(default=50, ge=1)

    # Data split ratios
    train_ratio: float = Field(default=0.70, gt=0.0, lt=1.0)
    val_ratio: float = Field(default=0.15, gt=0.0, lt=1.0)

    # Cross-validation
    cv_folds: int = Field(default=5, ge=2)

    # Paths (relative to the ai/ workspace root)
    feature_matrix_path: str = "datasets/features/feature_matrix.parquet"
    models_dir: str = "models"

    # Schema
    target_column: str = "result"
    date_column: str = "match_date"
    exclude_columns: list[str] = Field(default_factory=_default_exclude)

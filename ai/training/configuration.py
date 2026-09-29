"""Training configuration for the XGBoost match outcome model."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

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
    "over_2_5_odds",
    "under_2_5_odds",
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

    # Data split: "chronological" uses the ratios below (ADR 003); "season"
    # assigns whole seasons (ADR 007). Training takes every season before the
    # first validation season; holdout seasons are never used in training.
    split_strategy: Literal["chronological", "season"] = "chronological"
    train_ratio: float = Field(default=0.70, gt=0.0, lt=1.0)
    val_ratio: float = Field(default=0.15, gt=0.0, lt=1.0)
    val_seasons: list[str] = Field(default_factory=list)
    test_seasons: list[str] = Field(default_factory=list)
    holdout_seasons: list[str] = Field(default_factory=list)

    # Cross-validation
    cv_folds: int = Field(default=5, ge=2)

    # Paths (relative to the ai/ workspace root)
    feature_matrix_path: str = "datasets/features/feature_matrix.parquet"
    models_dir: str = "models"

    # Schema
    target_column: str = "result"
    date_column: str = "match_date"
    season_column: str = "season"
    exclude_columns: list[str] = Field(default_factory=_default_exclude)

    @model_validator(mode="after")
    def _check_season_lists(self) -> Self:
        """Require disjoint validation and test seasons for the season split."""
        if self.split_strategy != "season":
            return self
        if not self.val_seasons or not self.test_seasons:
            raise ValueError("Season split needs val_seasons and test_seasons")
        lists = [self.val_seasons, self.test_seasons, self.holdout_seasons]
        flat = [season for group in lists for season in group]
        if len(flat) != len(set(flat)):
            raise ValueError(f"Season lists overlap: {flat}")
        return self

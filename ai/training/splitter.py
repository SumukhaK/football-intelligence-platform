"""Train/validation/test splits for football data.

``ChronologicalSplitter`` splits by row ratios (ADR 003); ``SeasonSplitter``
assigns whole seasons (ADR 007). Neither ever shuffles.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from training.configuration import TrainingConfig


@dataclass(frozen=True)
class DataSplit:
    """Chronologically ordered feature and label arrays for all three sets."""

    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series
    train_size: int
    val_size: int
    test_size: int
    date_range_train: tuple[str, str]
    date_range_val: tuple[str, str]
    date_range_test: tuple[str, str]


def get_feature_columns(df: pd.DataFrame, config: TrainingConfig) -> list[str]:
    """Return the pinned ``config.feature_columns``, checked against ``df``.

    Raises:
        ValueError: If a pinned feature is missing or not numeric, or if a
            numeric column is neither a feature nor explicitly excluded.
    """
    features = list(config.feature_columns)
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise ValueError(f"Feature matrix is missing pinned features: {missing}")
    not_numeric = [c for c in features if df[c].dtype.kind not in "fiub"]
    if not_numeric:
        raise ValueError(f"Pinned features are not numeric: {not_numeric}")
    known = set(features) | set(config.exclude_columns) | {config.target_column}
    unknown = [c for c in df.columns if c not in known and df[c].dtype.kind in "fiub"]
    if unknown:
        raise ValueError(
            f"Unknown numeric columns {unknown}: add them to feature_columns "
            "or exclude_columns before training."
        )
    return features


class ChronologicalSplitter:
    """Splits a feature matrix in chronological order — no shuffling."""

    def split(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        config: TrainingConfig,
    ) -> DataSplit:
        """Return a DataSplit with no temporal leakage between sets."""
        df_sorted = df.sort_values(config.date_column).reset_index(drop=True)
        n = len(df_sorted)
        train_end = int(n * config.train_ratio)
        val_end = train_end + int(n * config.val_ratio)

        train_df = df_sorted.iloc[:train_end]
        val_df = df_sorted.iloc[train_end:val_end]
        test_df = df_sorted.iloc[val_end:]

        return _build_split(train_df, val_df, test_df, feature_cols, config)


class SeasonSplitter:
    """Splits a feature matrix by whole seasons, in date order."""

    def split(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        config: TrainingConfig,
    ) -> DataSplit:
        """Return train (seasons before validation), validation and test sets.

        Holdout seasons, and any season after the first validation season that
        is not listed, are left out entirely.
        """
        season = df[config.season_column]
        known = set(season)
        listed = config.val_seasons + config.test_seasons + config.holdout_seasons
        missing = [s for s in listed if s not in known]
        if missing:
            raise ValueError(f"Seasons not in feature matrix: {missing}")

        starts = df.groupby(config.season_column)[config.date_column].min()
        cutoff = min(starts[s] for s in config.val_seasons)
        train_seasons = [
            s for s in starts.index if starts[s] < cutoff and s not in listed
        ]

        df_sorted = df.sort_values(config.date_column, kind="stable")
        in_season = df_sorted[config.season_column].isin
        return _build_split(
            df_sorted[in_season(train_seasons)],
            df_sorted[in_season(config.val_seasons)],
            df_sorted[in_season(config.test_seasons)],
            feature_cols,
            config,
        )


def make_splitter(config: TrainingConfig) -> ChronologicalSplitter | SeasonSplitter:
    """Return the splitter selected by ``config.split_strategy``."""
    if config.split_strategy == "season":
        return SeasonSplitter()
    return ChronologicalSplitter()


def _build_split(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    config: TrainingConfig,
) -> DataSplit:
    """Assemble a DataSplit from three already-ordered frames."""

    def _date_range(sub: pd.DataFrame) -> tuple[str, str]:
        dates = sub[config.date_column].astype(str)
        return str(dates.iloc[0]), str(dates.iloc[-1])

    target = config.target_column
    return DataSplit(
        X_train=train_df[feature_cols].copy(),
        X_val=val_df[feature_cols].copy(),
        X_test=test_df[feature_cols].copy(),
        y_train=train_df[target].copy(),
        y_val=val_df[target].copy(),
        y_test=test_df[target].copy(),
        train_size=len(train_df),
        val_size=len(val_df),
        test_size=len(test_df),
        date_range_train=_date_range(train_df),
        date_range_val=_date_range(val_df),
        date_range_test=_date_range(test_df),
    )

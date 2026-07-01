"""Chronological train/validation/test split for football data."""

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
    """Return numeric columns that are safe to use as training features."""
    excluded = set(config.exclude_columns) | {config.target_column}
    return [c for c in df.columns if c not in excluded and df[c].dtype.kind in "fiu"]


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

        def _date_range(sub: pd.DataFrame) -> tuple[str, str]:
            dates = sub[config.date_column].astype(str)
            return str(dates.iloc[0]), str(dates.iloc[-1])

        return DataSplit(
            X_train=train_df[feature_cols].copy(),
            X_val=val_df[feature_cols].copy(),
            X_test=test_df[feature_cols].copy(),
            y_train=train_df[config.target_column].copy(),
            y_val=val_df[config.target_column].copy(),
            y_test=test_df[config.target_column].copy(),
            train_size=len(train_df),
            val_size=len(val_df),
            test_size=len(test_df),
            date_range_train=_date_range(train_df),
            date_range_val=_date_range(val_df),
            date_range_test=_date_range(test_df),
        )

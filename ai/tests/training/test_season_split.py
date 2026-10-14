"""Tests for the season-based split (ADR 007)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from training.configuration import TrainingConfig
from training.splitter import (
    ChronologicalSplitter,
    SeasonSplitter,
    get_feature_columns,
    make_splitter,
)

_SEASONS = ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24", "2024/25"]


def _multi_season(rows_per_season: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    frames = []
    for i, season in enumerate(_SEASONS):
        start = pd.Timestamp(f"{2019 + i}-08-10")
        frames.append(
            pd.DataFrame(
                {
                    "match_date": pd.date_range(start, periods=rows_per_season),
                    "season": season,
                    "competition": rng.choice(["Premier League", "Serie A"], 20),
                    "home_team": "A",
                    "away_team": "B",
                    "result": rng.choice(["H", "D", "A"], rows_per_season),
                    "home_elo_before": rng.uniform(1300, 1700, rows_per_season),
                    "home_odds": rng.uniform(1.2, 6.0, rows_per_season),
                    "draw_odds": rng.uniform(2.5, 5.0, rows_per_season),
                    "away_odds": rng.uniform(1.2, 9.0, rows_per_season),
                }
            )
        )
    return pd.concat(frames, ignore_index=True).sample(frac=1, random_state=1)


@pytest.fixture()
def season_config() -> TrainingConfig:
    return TrainingConfig(
        feature_columns=["home_elo_before"],
        split_strategy="season",
        val_seasons=["2022/23"],
        test_seasons=["2023/24"],
        holdout_seasons=["2024/25"],
    )


def test_season_split_assigns_whole_seasons(season_config: TrainingConfig) -> None:
    df = _multi_season()
    cols = get_feature_columns(df, season_config)
    split = SeasonSplitter().split(df, cols, season_config)
    assert split.train_size == 60
    assert split.val_size == 20
    assert split.test_size == 20
    assert split.date_range_train[1] < split.date_range_val[0]
    assert split.date_range_val[1] < split.date_range_test[0]


def test_holdout_seasons_are_never_used(season_config: TrainingConfig) -> None:
    df = _multi_season()
    split = SeasonSplitter().split(df, ["home_elo_before"], season_config)
    total = split.train_size + split.val_size + split.test_size
    assert total == len(df) - 20


def test_train_only_uses_seasons_before_validation() -> None:
    df = _multi_season()
    config = TrainingConfig(
        split_strategy="season", val_seasons=["2021/22"], test_seasons=["2023/24"]
    )
    split = SeasonSplitter().split(df, ["home_elo_before"], config)
    assert split.train_size == 40
    assert split.date_range_train[1] < "2021-08-01"


def test_train_rows_are_in_date_order(season_config: TrainingConfig) -> None:
    df = _multi_season()
    split = SeasonSplitter().split(df, ["home_elo_before"], season_config)
    dates = df.loc[split.X_train.index, "match_date"]
    assert dates.is_monotonic_increasing


def test_unknown_season_raises(season_config: TrainingConfig) -> None:
    df = _multi_season()
    config = season_config.model_copy(update={"test_seasons": ["1999/00"]})
    with pytest.raises(ValueError, match="1999/00"):
        SeasonSplitter().split(df, ["home_elo_before"], config)


def test_season_strategy_requires_val_and_test_seasons() -> None:
    with pytest.raises(ValidationError):
        TrainingConfig(split_strategy="season", test_seasons=["2023/24"])


def test_overlapping_season_lists_are_rejected() -> None:
    with pytest.raises(ValidationError):
        TrainingConfig(
            split_strategy="season",
            val_seasons=["2022/23"],
            test_seasons=["2022/23"],
        )


def test_make_splitter_picks_strategy(season_config: TrainingConfig) -> None:
    assert isinstance(make_splitter(season_config), SeasonSplitter)
    assert isinstance(make_splitter(TrainingConfig()), ChronologicalSplitter)


def test_odds_are_never_feature_columns(season_config: TrainingConfig) -> None:
    cols = get_feature_columns(_multi_season(), season_config)
    assert not {"home_odds", "draw_odds", "away_odds"} & set(cols)

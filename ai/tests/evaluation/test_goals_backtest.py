"""Tests for the goals-model rolling-origin backtest."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from evaluation.goals_backtest import rolling_origin_forecasts, week_start
from goals.dixon_coles import GoalsModelConfig, fit_dixon_coles
from tests.goals.test_dixon_coles import synthetic_league


def league_with_seasons() -> pd.DataFrame:
    matches = synthetic_league(seasons=3)
    matches["competition"] = "Test League"
    matches["result"] = "D"
    split = matches["match_date"].iloc[len(matches) * 2 // 3]
    matches["season"] = [
        "2022/23" if d < split else "2023/24" for d in matches["match_date"]
    ]
    return matches


def test_week_start_is_the_monday() -> None:
    dates = pd.Series(pd.to_datetime(["2026-09-20", "2026-09-21", "2026-09-27"]))
    assert week_start(dates).dt.strftime("%Y-%m-%d").tolist() == [
        "2026-09-14",
        "2026-09-21",
        "2026-09-21",
    ]


def test_forecasts_only_the_requested_seasons() -> None:
    matches = league_with_seasons()
    out = rolling_origin_forecasts(matches, ["2023/24"], GoalsModelConfig())
    assert len(out) == (matches["season"] == "2023/24").sum()
    assert set(out["season"]) == {"2023/24"}


def test_never_fits_on_the_match_being_forecast_or_later() -> None:
    matches = league_with_seasons()
    seen: list[tuple[pd.Timestamp, pd.Timestamp]] = []

    def spy(data: pd.DataFrame, before: pd.Timestamp, *args: object) -> object:
        used = pd.to_datetime(data["match_date"])
        in_window = used[used < before]
        seen.append((before, in_window.max()))
        return fit_dixon_coles(data, before, *args)  # type: ignore[arg-type]

    with patch("evaluation.goals_backtest.fit_dixon_coles", side_effect=spy):
        out = rolling_origin_forecasts(matches, ["2023/24"], GoalsModelConfig())
    fitted = pd.to_datetime(out["fitted_before"])
    assert (fitted <= pd.to_datetime(out["match_date"])).all()
    assert all(latest < before for before, latest in seen)


def test_probabilities_are_consistent() -> None:
    out = rolling_origin_forecasts(
        league_with_seasons(), ["2023/24"], GoalsModelConfig()
    )
    total = out["p_H"] + out["p_D"] + out["p_A"]
    assert total.to_numpy() == pytest.approx(1.0)
    assert ((out["p_score"] > 0) & (out["p_score"] < 1)).all()
    assert (out["top3_hit"] | ~out["top1_hit"]).all()

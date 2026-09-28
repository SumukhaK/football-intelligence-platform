"""Tests for FixtureFeatureBuilder: serving features must equal training features."""

from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from feature_engineering.pipeline import FeaturePipeline
from inference.fixture_features import (
    Fixture,
    FixtureFeatureBuilder,
    UnknownTeamError,
    find_latest_dataset,
    season_for_date,
)

_COMP = "Premier League"


def _rounds(teams: list[str]) -> list[list[tuple[str, str]]]:
    """Circle-method double round robin: every team plays once per round."""
    order, n, first_half = list(teams), len(teams), []
    for _ in range(n - 1):
        first_half.append([(order[i], order[n - 1 - i]) for i in range(n // 2)])
        order = [order[0], order[-1], *order[1:-1]]
    return first_half + [[(a, h) for h, a in rnd] for rnd in first_half]


def _league(teams: list[str], season: str, start: date, seed: int) -> list[dict]:
    """A double round robin, one round per week, random scores."""
    rng = np.random.default_rng(seed)
    rows = []
    for week, fixtures in enumerate(_rounds(teams)):
        for home, away in fixtures:
            hg, ag = (int(x) for x in rng.integers(0, 4, 2))
            result = "H" if hg > ag else "A" if ag > hg else "D"
            rows.append(
                {
                    "match_date": (start + timedelta(days=7 * week)).isoformat(),
                    "season": season,
                    "competition": _COMP,
                    "home_team": home,
                    "away_team": away,
                    "full_time_home_goals": hg,
                    "full_time_away_goals": ag,
                    "result": result,
                }
            )
    return rows


@pytest.fixture()
def matches() -> pd.DataFrame:
    season_one = _league(["A", "B", "C", "D"], "2024/25", date(2024, 8, 10), 1)
    season_two = _league(["A", "B", "C", "E"], "2025/26", date(2025, 8, 9), 2)
    return pd.DataFrame(season_one + season_two)


def test_serving_features_equal_training_features(matches: pd.DataFrame) -> None:
    trained, _ = FeaturePipeline().compute(matches)
    builder = FixtureFeatureBuilder(matches)
    for _, row in trained[trained["season"] == "2025/26"].iterrows():
        fixture = Fixture(
            row["home_team"],
            row["away_team"],
            _COMP,
            date.fromisoformat(row["match_date"]),
        )
        served = builder.build(fixture)
        for name, value in served.items():
            expected = float(row[name])
            if math.isnan(expected):
                assert math.isnan(value), name
            else:
                assert value == pytest.approx(expected), (name, fixture)


def test_teams_are_from_the_latest_season(matches: pd.DataFrame) -> None:
    season, teams = FixtureFeatureBuilder(matches).teams(_COMP)
    assert season == "2025/26"
    assert teams == ["A", "B", "C", "E"]


def test_relegated_team_is_rejected(matches: pd.DataFrame) -> None:
    builder = FixtureFeatureBuilder(matches)
    with pytest.raises(UnknownTeamError, match="'D'"):
        builder.build(Fixture("A", "D", _COMP, date(2026, 8, 15)))


def test_future_fixture_uses_all_history(matches: pd.DataFrame) -> None:
    features = FixtureFeatureBuilder(matches).build(
        Fixture("A", "E", _COMP, date(2026, 8, 15))
    )
    assert features["h2h_meetings"] == 2
    assert features["home_league_points"] == 0
    assert math.isnan(features["home_rest_days"])
    assert len(features) == 42


def test_repeat_requests_are_cached(matches: pd.DataFrame) -> None:
    builder = FixtureFeatureBuilder(matches)
    fixture = Fixture("A", "B", _COMP, date(2026, 8, 15))
    assert builder.build(fixture) is builder.build(fixture)


@pytest.mark.parametrize(
    ("day", "season"),
    [
        (date(2026, 9, 28), "2026/27"),
        (date(2027, 5, 1), "2026/27"),
        (date(2026, 7, 1), "2026/27"),
        (date(2026, 6, 30), "2025/26"),
    ],
)
def test_season_for_date(day: date, season: str) -> None:
    assert season_for_date(day) == season


def test_find_latest_dataset_prefers_live_snapshot(tmp_path: Path) -> None:
    for name in (
        "match_results_top5_v20260928_071043.csv",
        "match_results_live_v20260901_000000.csv",
        "match_results_live_v20260928_000000.csv",
    ):
        (tmp_path / name).write_text("x")
    assert find_latest_dataset(tmp_path).name == (
        "match_results_live_v20260928_000000.csv"
    )


def test_find_latest_dataset_falls_back_to_history(tmp_path: Path) -> None:
    (tmp_path / "match_results_top5_v20260928_071043.csv").write_text("x")
    assert "top5" in find_latest_dataset(tmp_path).name
    with pytest.raises(FileNotFoundError):
        find_latest_dataset(tmp_path / "missing")


def test_past_fixture_accepts_that_seasons_teams(matches: pd.DataFrame) -> None:
    builder = FixtureFeatureBuilder(matches)
    features = builder.build(Fixture("A", "D", _COMP, date(2025, 3, 1)))
    assert len(features) == 42


def test_cache_is_bounded(matches: pd.DataFrame) -> None:
    builder = FixtureFeatureBuilder(matches, max_cached=2)
    for day in (15, 16, 17):
        builder.build(Fixture("A", "B", _COMP, date(2026, 8, day)))
    assert builder.cached_fixtures <= 2

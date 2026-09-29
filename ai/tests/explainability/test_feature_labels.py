"""Tests for fan-friendly feature labels and values."""

from __future__ import annotations

import math

import pytest

from explainability.feature_labels import describe_feature
from feature_engineering.pipeline import build_default_registry

_ALL_FEATURES = [
    c for f in build_default_registry().get_ordered() for c in f.output_columns
]


@pytest.mark.parametrize("name", _ALL_FEATURES)
def test_every_model_feature_has_a_fan_label(name: str) -> None:
    label, value = describe_feature(name, 1.0, "Arsenal", "Chelsea")
    assert "_" not in label
    assert label[0].isupper()
    assert value


@pytest.mark.parametrize(
    ("name", "raw", "label", "value"),
    [
        ("home_elo_before", 1617.748, "Arsenal team strength rating", "1618"),
        ("away_elo_before", 1467.035, "Chelsea team strength rating", "1467"),
        ("home_win_pct", 0.681, "Arsenal win rate at home", "68%"),
        ("away_ppg", 1.1, "Chelsea points per away game", "1.1"),
        ("home_form_wins_last10", 9.0, "Arsenal wins in last 10 games", "9 of 10"),
        ("away_form_points_last5", 7.0, "Chelsea points from last 5 games", "7 of 15"),
        (
            "home_goals_scored_last5",
            2.4,
            "Arsenal goals scored per game, last 5",
            "2.4",
        ),
        (
            "away_goal_diff_last10",
            -0.7,
            "Chelsea goal difference per game, last 10",
            "-0.7",
        ),
        (
            "home_goal_diff_last5",
            1.2,
            "Arsenal goal difference per game, last 5",
            "+1.2",
        ),
        ("home_rest_days", 7.0, "Arsenal days of rest before the match", "7 days"),
        ("home_rest_days", 1.0, "Arsenal days of rest before the match", "1 day"),
        ("away_league_position", 10.0, "Chelsea league position", "10th"),
        ("home_league_position", 1.0, "Arsenal league position", "1st"),
        ("home_league_position", 22.0, "Arsenal league position", "22nd"),
        ("home_league_position", 13.0, "Arsenal league position", "13th"),
        ("home_league_points", 16.0, "Arsenal league points this season", "16"),
        ("h2h_meetings", 58.0, "Previous meetings between the teams", "58"),
        ("h2h_home_wins", 19.0, "Arsenal wins in previous meetings", "19"),
        ("h2h_draws", 17.0, "Draws in previous meetings", "17"),
        (
            "home_avg_opp_elo_last5",
            1512.4,
            "Strength of Arsenal's last 5 opponents",
            "1512",
        ),
    ],
)
def test_labels_and_values(name: str, raw: float, label: str, value: str) -> None:
    assert describe_feature(name, raw, "Arsenal", "Chelsea") == (label, value)


def test_unknown_feature_falls_back_to_readable_name() -> None:
    assert describe_feature("some_new_feature", 0.12345, "A", "B") == (
        "Some new feature",
        "0.123",
    )


def test_missing_value_is_shown_as_not_available() -> None:
    _, value = describe_feature("home_rest_days", math.nan, "Arsenal", "Chelsea")
    assert value == "n/a"

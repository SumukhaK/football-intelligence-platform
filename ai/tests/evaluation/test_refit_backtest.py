"""Tests for the refit-versus-frozen backtest."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from evaluation.refit_backtest import check_no_leakage, compare, render, season_rows

_CLASSES = ["A", "D", "H"]


def _matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_date": pd.to_datetime(
                ["2026-05-20", "2026-08-16", "2026-08-15", "2026-09-20", "2026-09-27"]
            ),
            "season": ["2025/26", "2026/27", "2026/27", "2026/27", "2026/27"],
            "competition": ["Serie A", "La Liga", "Serie A", "La Liga", "La Liga"],
            "home_team": list("ABCDE"),
            "away_team": list("VWXYZ"),
            "result": ["H", "D", "H", "A", "H"],
            "home_odds": [2.0, 2.5, 1.8, 3.0, 2.0],
            "draw_odds": [3.4, 3.1, 3.6, 3.3, 3.4],
            "away_odds": [3.8, 2.9, 4.5, 2.3, 3.8],
        }
    )


def _rows() -> pd.DataFrame:
    return season_rows(_matrix(), "2026/27", "2026-09-20")


def _refit(last_date: str, last_season: str = "2025/26") -> dict[str, Any]:
    return {
        "first_season": "2000/01",
        "last_season": last_season,
        "date_range_train": ["2000-07-28", last_date],
    }


def test_season_rows_keep_the_season_up_to_the_cutoff_in_date_order() -> None:
    assert _rows()["home_team"].tolist() == ["C", "B", "D"]


def test_leakage_check_passes_when_training_ends_before_the_season() -> None:
    check = check_no_leakage(_refit("2026-05-24"), _rows())
    assert check["first_backtest_match"] == "2026-08-15"
    assert check["refit_last_training_match"] == "2026-05-24"


def test_leakage_check_fails_on_overlapping_dates() -> None:
    with pytest.raises(ValueError, match="overlaps"):
        check_no_leakage(_refit("2026-08-20"), _rows())


def test_leakage_check_fails_when_the_season_was_trained_on() -> None:
    with pytest.raises(ValueError, match="overlaps"):
        check_no_leakage(_refit("2026-05-24", last_season="2026/27"), _rows())


def test_compare_scores_both_models_and_the_bookmaker() -> None:
    rows = _rows()  # results H, D, A
    frozen = np.tile([0.3, 0.3, 0.4], (3, 1))
    refit = np.array([[0.2, 0.2, 0.6], [0.3, 0.4, 0.3], [0.5, 0.2, 0.3]])
    result = compare(rows, frozen, refit, _CLASSES)

    overall = result["scores"]["overall"]
    assert set(overall) == {"frozen", "refit", "bookmaker"}
    assert overall["refit"]["accuracy"] == 1.0
    assert "La Liga" in result["scores"]
    assert result["deltas"]["refit_minus_frozen_log_loss"]["mean"] < 0
    assert "frozen_minus_bookmaker_rps" in result["deltas"]
    report = {
        "season": "2026/27",
        "through": "2026-09-20",
        "frozen_model": "f",
        "refit_model": "r",
        "matches": 3,
        **result,
    }
    assert "| overall | 3 | refit | 100.0% |" in render(report)

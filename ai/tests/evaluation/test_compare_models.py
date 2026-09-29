"""Tests for the model comparison helpers and report rendering."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from evaluation.compare_models import align_matches, score_block, verdict
from evaluation.comparison_report import render_markdown

_CLASSES = ["A", "D", "H"]


def _rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_date": ["2024-05-19", "2024-05-19", "2024-05-12"],
            "home_team": ["Arsenal", "Chelsea", "Luton"],
            "away_team": ["Everton", "Bournemouth", "Fulham"],
            "competition": ["Premier League", "Premier League", "Serie A"],
            "result": ["H", "H", "A"],
            "home_odds": [1.2, 1.8, np.nan],
            "draw_odds": [6.0, 4.0, 3.6],
            "away_odds": [13.0, 4.0, 2.4],
        }
    )


def test_align_matches_returns_rows_in_key_order() -> None:
    df = _rows()
    keys = df.iloc[[1, 0]][["match_date", "home_team", "away_team"]]
    joined = align_matches(keys, df)
    assert joined["home_team"].tolist() == ["Chelsea", "Arsenal"]


def test_align_matches_raises_on_missing_match() -> None:
    keys = pd.DataFrame(
        {"match_date": ["2024-05-19"], "home_team": ["Spurs"], "away_team": ["X"]}
    )
    with pytest.raises(ValueError, match="Spurs"):
        align_matches(keys, _rows())


def test_score_block_skips_rows_without_odds_and_groups() -> None:
    rows = _rows()
    probs = np.array([[0.1, 0.2, 0.7]] * 3)
    block = score_block(rows, {"candidate": probs}, _CLASSES)
    assert block["overall"]["candidate"]["n"] == 2
    assert set(block["overall"]) == {"candidate", "bookmaker"}
    assert "Serie A" not in block


def _report(delta_upper: float, candidate_ll: float) -> dict[str, Any]:
    scores = {
        "overall": {
            "candidate": {
                "n": 10,
                "log_loss": candidate_ll,
                "rps": 0.2,
                "brier": 0.6,
                "accuracy": 0.5,
            },
            "priors": {
                "n": 10,
                "log_loss": 1.08,
                "rps": 0.23,
                "brier": 0.65,
                "accuracy": 0.43,
            },
        }
    }
    delta = {
        "metric": "log_loss",
        "mean": -0.1,
        "lower": -0.2,
        "upper": delta_upper,
        "n_resamples": 10,
    }
    return {
        "candidate_run": "runs/x",
        "test": scores,
        "holdout": scores,
        "like_for_like": {
            **scores,
            "delta_log_loss": delta,
            "delta_rps": {**delta, "metric": "rps"},
        },
    }


def test_verdict_promotes_only_when_every_check_passes() -> None:
    assert verdict(_report(-0.01, 0.98))["promote"] is True
    failed = verdict(_report(0.02, 0.98))
    assert failed["promote"] is False
    assert failed["checks"]["beats_current_on_its_test_matches"] is False
    assert verdict(_report(-0.01, 1.2))["promote"] is False


def test_render_markdown_includes_tables_and_verdict() -> None:
    report = _report(-0.01, 0.98)
    report["verdict"] = verdict(report)
    text = render_markdown(report)
    assert "| candidate | 0.9800 |" in text
    assert "95% interval -0.2000 to -0.0100" in text
    assert "**Promote**" in text

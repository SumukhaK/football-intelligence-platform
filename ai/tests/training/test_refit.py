"""Tests for the serving refit (ADR 017).

The ``refit_matrix`` and ``source_run`` fixtures live in ``conftest.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.persistence import load_model
from training.refit import PURPOSE, refit_config, refit_rows, run_refit

_FEATURES = ["home_elo_before", "away_elo_before"]


def test_refit_config_uses_the_source_best_tree_count(source_run: Path) -> None:
    best = load_model(source_run / "model.joblib").best_iteration
    config = refit_config(source_run)
    assert config.n_estimators == best + 1
    assert config.feature_columns == _FEATURES


def test_refit_rows_stop_at_the_last_season(refit_matrix: pd.DataFrame) -> None:
    config = TrainingConfig(feature_columns=_FEATURES)
    rows = refit_rows(refit_matrix, config, "2023/24")
    assert sorted(set(rows["season"]))[-1] == "2023/24"
    assert "2024/25" not in set(rows["season"])
    assert rows["match_date"].is_monotonic_increasing


def test_refit_rows_reject_an_unknown_season(refit_matrix: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="2030/31"):
        refit_rows(refit_matrix, TrainingConfig(feature_columns=_FEATURES), "2030/31")


def test_run_refit_writes_a_run_without_promoting(
    tmp_path: Path, source_run: Path
) -> None:
    summary = run_refit(source_run, "2023/24", tmp_path)
    run_dir = Path(summary["run_dir"])
    info = json.loads((run_dir / "refit.json").read_text(encoding="utf-8"))
    model = load_model(run_dir / "model.joblib")

    assert info["purpose"] == PURPOSE
    assert info["last_season"] == "2023/24"
    assert info["excluded_seasons"] == ["2024/25"]
    assert info["n_train"] == 200
    assert info["date_range_train"][1] < "2024-08-10"
    assert model.booster.get_booster().num_boosted_rounds() == info["n_estimators"]
    assert not (tmp_path / "models" / "latest").exists()
    assert not (tmp_path / "models" / "registry.json").exists()

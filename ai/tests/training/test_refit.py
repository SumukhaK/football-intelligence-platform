"""Tests for the serving refit (ADR 017)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.persistence import load_model
from training.pipeline import TrainingPipeline
from training.refit import PURPOSE, refit_config, refit_rows, run_refit

_SEASONS = ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24", "2024/25"]
_FEATURES = ["home_elo_before", "away_elo_before"]
_MATRIX = "features/feature_matrix.parquet"


def _write_matrix(cwd: Path) -> str:
    rng = np.random.default_rng(3)
    frames = [
        pd.DataFrame(
            {
                "match_date": pd.date_range(f"{2019 + i}-08-10", periods=40),
                "season": season,
                "competition": "Premier League",
                "home_team": "A",
                "away_team": "B",
                "result": rng.choice(["H", "D", "A"], 40),
                "home_elo_before": rng.uniform(1300, 1700, 40),
                "away_elo_before": rng.uniform(1300, 1700, 40),
            }
        )
        for i, season in enumerate(_SEASONS)
    ]
    path = cwd / _MATRIX
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_parquet(path)
    return _MATRIX


@pytest.fixture()
def source_run(tmp_path: Path) -> Path:
    """A season-split run that was not promoted, as the refit's source."""
    config = TrainingConfig(
        feature_columns=_FEATURES,
        n_estimators=30,
        early_stopping_rounds=3,
        cv_folds=2,
        split_strategy="season",
        val_seasons=["2021/22"],
        test_seasons=["2022/23"],
        holdout_seasons=["2023/24"],
        feature_matrix_path=_write_matrix(tmp_path),
    )
    return Path(TrainingPipeline(config).run(tmp_path, promote=False)["run_dir"])


def test_refit_config_uses_the_source_best_tree_count(source_run: Path) -> None:
    best = load_model(source_run / "model.joblib").best_iteration
    config = refit_config(source_run)
    assert config.n_estimators == best + 1
    assert config.feature_columns == _FEATURES


def test_refit_rows_stop_at_the_last_season(tmp_path: Path) -> None:
    df = pd.read_parquet(tmp_path / _write_matrix(tmp_path))
    rows = refit_rows(df, TrainingConfig(feature_columns=_FEATURES), "2023/24")
    assert sorted(set(rows["season"])) == _SEASONS[:5]
    assert rows["match_date"].is_monotonic_increasing


def test_refit_rows_reject_an_unknown_season(tmp_path: Path) -> None:
    df = pd.read_parquet(tmp_path / _write_matrix(tmp_path))
    with pytest.raises(ValueError, match="2030/31"):
        refit_rows(df, TrainingConfig(feature_columns=_FEATURES), "2030/31")


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

"""Tests for TrainingPipeline promotion and the season split end to end."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from training.configuration import TrainingConfig
from training.pipeline import TrainingPipeline

_SEASONS = ["2019/20", "2020/21", "2021/22", "2022/23", "2023/24"]


def _write_matrix(cwd: Path) -> str:
    rng = np.random.default_rng(5)
    frames = []
    for i, season in enumerate(_SEASONS):
        n = 40
        frames.append(
            pd.DataFrame(
                {
                    "match_date": pd.date_range(f"{2019 + i}-08-10", periods=n),
                    "season": season,
                    "competition": "Premier League",
                    "home_team": "A",
                    "away_team": "B",
                    "result": rng.choice(["H", "D", "A"], n),
                    "home_elo_before": rng.uniform(1300, 1700, n),
                    "away_elo_before": rng.uniform(1300, 1700, n),
                }
            )
        )
    path = cwd / "features" / "feature_matrix.parquet"
    path.parent.mkdir(parents=True)
    pd.concat(frames, ignore_index=True).to_parquet(path)
    return "features/feature_matrix.parquet"


@pytest.fixture()
def config(tmp_path: Path) -> TrainingConfig:
    return TrainingConfig(
        n_estimators=10,
        early_stopping_rounds=3,
        cv_folds=2,
        split_strategy="season",
        val_seasons=["2022/23"],
        test_seasons=["2023/24"],
        feature_matrix_path=_write_matrix(tmp_path),
    )


def test_unpromoted_run_leaves_latest_and_registry_untouched(
    tmp_path: Path, config: TrainingConfig
) -> None:
    result = TrainingPipeline(config).run(tmp_path, promote=False)
    run_dir = Path(result["run_dir"])
    assert (run_dir / "model.joblib").exists()
    assert (run_dir / "model_card.md").exists()
    assert not (tmp_path / "models" / "latest").exists()
    assert not (tmp_path / "models" / "registry.json").exists()
    assert result["promoted"] is False


def test_promoted_run_updates_latest_and_registry(
    tmp_path: Path, config: TrainingConfig
) -> None:
    TrainingPipeline(config).run(tmp_path)
    assert (tmp_path / "models" / "latest" / "model_card.md").exists()
    assert (tmp_path / "models" / "registry.json").exists()


def test_model_card_describes_seasons_and_split(
    tmp_path: Path, config: TrainingConfig
) -> None:
    result = TrainingPipeline(config).run(tmp_path, promote=False)
    card = (Path(result["run_dir"]) / "model_card.md").read_text(encoding="utf-8")
    assert "Premier League; 2019/20 to 2023/24 (200 matches)" in card
    assert "Season split (ADR 007)" in card
    assert "season walk-forward, 2 folds" in card

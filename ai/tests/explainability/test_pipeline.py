"""Tests for explainability.pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from explainability.configuration import ExplainabilityConfig
from explainability.pipeline import ExplainabilityPipeline
from training.persistence import save_model
from training.trainer import TrainedModel


def _make_feature_matrix(
    trained_model: TrainedModel, n: int = 20, seed: int = 3
) -> pd.DataFrame:
    """Return a minimal feature matrix matching the trained model."""
    import numpy as np

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-08-01", periods=n, freq="7D")
    rows: list[dict[str, object]] = []
    for i in range(n):
        row: dict[str, object] = {
            "match_date": dates[i],
            "season": "2023/24",
            "competition": "Premier League",
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "result": rng.choice(["H", "D", "A"]),
        }
        for col in trained_model.feature_names:
            row[col] = float(rng.random())
        rows.append(row)
    return pd.DataFrame(rows)


@pytest.fixture()
def _pipeline(
    trained_model: TrainedModel, tmp_path: Path
) -> tuple[ExplainabilityPipeline, Path, Path]:
    """A configured pipeline with model and feature matrix saved to tmp_path."""
    model_path = tmp_path / "model.joblib"
    save_model(trained_model, model_path)

    fm = _make_feature_matrix(trained_model)
    fm_path = tmp_path / "feature_matrix.parquet"
    fm.to_parquet(fm_path, index=False)

    config = ExplainabilityConfig(
        model_path=str(model_path),
        feature_matrix_path=str(fm_path),
        explanations_dir=str(tmp_path / "explanations"),
        n_top_features=3,
        n_local_samples=3,
        n_dependence_plots=2,
    )
    return ExplainabilityPipeline(config), tmp_path, tmp_path / "explanations"


def test_pipeline_run_succeeds(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """pipeline.run() completes without raising."""
    pipeline, _, _ = _pipeline
    result = pipeline.run(use_absolute_paths=True)
    assert result["status"] == "ok"


def test_pipeline_generates_global_json(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """global_summary.json is written to the explanations directory."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    json_path = exp_dir / "global_summary.json"
    assert json_path.exists()
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert "n_samples" in parsed


def test_pipeline_generates_local_json(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """local_explanations.json is written to the explanations directory."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    json_path = exp_dir / "local_explanations.json"
    assert json_path.exists()
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(parsed, list)
    assert len(parsed) > 0


def test_pipeline_generates_summary_plot(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """summary_plot.png is written to the explanations directory."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    assert (exp_dir / "summary_plot.png").exists()


def test_pipeline_generates_feature_importance_plot(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """feature_importance.png is written to the explanations directory."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    assert (exp_dir / "feature_importance.png").exists()


def test_pipeline_generates_waterfall_plots(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """At least one waterfall plot PNG is generated."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    waterfall_dir = exp_dir / "waterfall"
    pngs = list(waterfall_dir.glob("*.png"))
    assert len(pngs) > 0


def test_pipeline_generates_force_plots(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """At least one force plot PNG is generated."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    force_dir = exp_dir / "force"
    pngs = list(force_dir.glob("*.png"))
    assert len(pngs) > 0


def test_pipeline_generates_dependence_plots(
    _pipeline: tuple[ExplainabilityPipeline, Path, Path],
) -> None:
    """At least one dependence plot PNG is generated."""
    pipeline, _, exp_dir = _pipeline
    pipeline.run(use_absolute_paths=True)
    dep_dir = exp_dir / "dependence"
    pngs = list(dep_dir.glob("*.png"))
    assert len(pngs) > 0


def test_pipeline_missing_model_raises(tmp_path: Path) -> None:
    """Pipeline raises an error when the model file does not exist."""
    config = ExplainabilityConfig(
        model_path=str(tmp_path / "missing.joblib"),
        feature_matrix_path=str(tmp_path / "fm.parquet"),
        explanations_dir=str(tmp_path / "explanations"),
    )
    pipeline = ExplainabilityPipeline(config)
    with pytest.raises(Exception):  # noqa: B017
        pipeline.run(use_absolute_paths=True)

"""Tests for promoting a backtested serving refit (ADR 017)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_registry.registry import ModelRegistry
from training.persistence import save_json
from training.promote_refit import backtest_metrics, promote
from training.refit import run_refit


def _report(version: str) -> dict[str, object]:
    scores = {"accuracy": 0.52, "log_loss": 0.976, "rps": 0.199, "brier": 0.578}
    return {
        "season": "2026/27",
        "refit_model": version,
        "scores": {"overall": {"refit": {"n": 250.0, **scores}}},
    }


def test_backtest_metrics_are_named_by_season() -> None:
    metrics = backtest_metrics(_report("v1"), "v1")
    assert metrics == {
        "accuracy_2026_27": 0.52,
        "log_loss_2026_27": 0.976,
        "rps_2026_27": 0.199,
        "brier_2026_27": 0.578,
    }


def test_backtest_for_another_refit_is_rejected() -> None:
    with pytest.raises(ValueError, match="not v2"):
        backtest_metrics(_report("v1"), "v2")


def test_promote_serves_the_refit_and_registers_it(
    tmp_path: Path, source_run: Path
) -> None:
    run_dir = Path(run_refit(source_run, "2023/24", tmp_path)["run_dir"])
    version = run_dir.name
    backtest = tmp_path / "report.json"
    save_json(_report(version), backtest)

    promote(run_dir, backtest, tmp_path / "models")

    latest = tmp_path / "models" / "latest"
    assert (latest / "model.joblib").exists()
    assert "serving refit" in (latest / "model_card.md").read_text("utf-8")
    metrics = json.loads((latest / "metrics.json").read_text("utf-8"))
    assert metrics["accuracy_2026_27"] == 0.52
    entry = ModelRegistry(tmp_path / "models" / "registry.json").latest()
    assert entry is not None and entry.version == version
    assert entry.metrics["log_loss_2026_27"] == 0.976

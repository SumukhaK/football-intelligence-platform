"""Serialisation helpers for model artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from training.configuration import TrainingConfig
from training.trainer import TrainedModel


def save_model(model: TrainedModel, path: Path) -> None:
    """Persist a TrainedModel to a joblib file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: Path) -> TrainedModel:
    """Load a TrainedModel from a joblib file."""
    model: TrainedModel = joblib.load(path)
    return model


def save_json(data: dict[str, Any], path: Path) -> None:
    """Write a dict to a UTF-8 JSON file with two-space indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    """Read and deserialise a JSON file into a dict."""
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return raw


def save_config(config: TrainingConfig, path: Path) -> None:
    """Persist a TrainingConfig as a JSON file."""
    save_json(config.model_dump(), path)

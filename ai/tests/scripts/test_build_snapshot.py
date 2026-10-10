"""Tests for scripts.build_snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.config import Settings
from scripts.build_snapshot import build, main

_MATCHES = "datasets/processed/football_data"


def _repo(tmp_path: Path) -> Settings:
    """A tiny repository with every file the API serves from."""
    files = {
        "ai/models/latest/model.joblib": "latest",
        "ai/models/runs/v1/model.joblib": "v1",
        "ai/models/registry.json": "[]",
        f"{_MATCHES}/match_results_live_v20261001_000000.csv": "old",
        f"{_MATCHES}/match_results_live_v20261009_000000.csv": "new",
        "datasets/processed/openfootball/fixtures_v20261009_000000.csv": "fixtures",
        "ai/assistant/vector_store/embeddings.npy": "vectors",
        "ai/assistant/vector_store/documents.json": "[]",
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")
    return Settings(
        model_path=tmp_path / "ai/models/latest/model.joblib",
        v1_model_path=tmp_path / "ai/models/runs/v1/model.joblib",
        registry_path=tmp_path / "ai/models/registry.json",
        matches_dir=tmp_path / "datasets/processed/football_data",
        fixtures_dir=tmp_path / "datasets/processed/openfootball",
        assistant_vector_store_path=tmp_path / "ai/assistant/vector_store",
    )


def _paths(out: Path) -> list[str]:
    manifest = json.loads((out / "manifest.json").read_text("utf-8"))
    return [f["path"] for f in manifest["files"]]


def test_build_takes_the_newest_datasets_and_the_index(tmp_path: Path) -> None:
    out = tmp_path / "snap"
    build(out, _repo(tmp_path), tmp_path, with_index=True)
    assert _paths(out) == [
        "ai/assistant/vector_store/documents.json",
        "ai/assistant/vector_store/embeddings.npy",
        "ai/models/latest/model.joblib",
        "ai/models/registry.json",
        "ai/models/runs/v1/model.joblib",
        f"{_MATCHES}/match_results_live_v20261009_000000.csv",
        "datasets/processed/openfootball/fixtures_v20261009_000000.csv",
    ]
    assert main(["--verify", str(out)]) == 0


def test_build_can_leave_the_index_out(tmp_path: Path) -> None:
    out = tmp_path / "snap"
    build(out, _repo(tmp_path), tmp_path, with_index=False)
    assert not any(p.startswith("ai/assistant") for p in _paths(out))


def test_a_snapshot_is_never_overwritten(tmp_path: Path) -> None:
    out = tmp_path / "snap"
    settings = _repo(tmp_path)
    build(out, settings, tmp_path, with_index=False)
    with pytest.raises(FileExistsError):
        build(out, settings, tmp_path, with_index=False)


def test_verify_fails_on_a_tampered_snapshot(tmp_path: Path) -> None:
    out = tmp_path / "snap"
    build(out, _repo(tmp_path), tmp_path, with_index=False)
    (out / "ai/models/latest/model.joblib").write_text("tampered", "utf-8")
    assert main(["--verify", str(out)]) == 1

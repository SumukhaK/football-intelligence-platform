"""Tests for shared.snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.snapshot import MANIFEST, copy_into, snapshot_id, verify, write_manifest


def _sources(tmp_path: Path) -> dict[str, Path]:
    (tmp_path / "src").mkdir(parents=True)
    model = tmp_path / "src" / "model.joblib"
    model.write_bytes(b"model-bytes")
    data = tmp_path / "src" / "matches.csv"
    data.write_text("a,b\n1,2\n", "utf-8")
    return {"ai/models/latest/model.joblib": model, "datasets/m.csv": data}


def _built(tmp_path: Path) -> Path:
    root = tmp_path / "snap"
    write_manifest(root, copy_into(root, _sources(tmp_path)), {"git_commit": "abc"})
    return root


def test_copy_keeps_the_repository_layout(tmp_path: Path) -> None:
    root = _built(tmp_path)
    assert (root / "ai/models/latest/model.joblib").read_bytes() == b"model-bytes"
    manifest = json.loads((root / MANIFEST).read_text("utf-8"))
    assert manifest["git_commit"] == "abc"
    assert [f["path"] for f in manifest["files"]] == [
        "ai/models/latest/model.joblib",
        "datasets/m.csv",
    ]
    assert manifest["files"][0]["bytes"] == len(b"model-bytes")


def test_a_fresh_snapshot_verifies(tmp_path: Path) -> None:
    assert verify(_built(tmp_path)) == []


def test_a_changed_file_fails_verification(tmp_path: Path) -> None:
    root = _built(tmp_path)
    (root / "datasets/m.csv").write_text("a,b\n9,9\n", "utf-8")
    assert verify(root) == ["Changed: datasets/m.csv"]


def test_a_missing_file_fails_verification(tmp_path: Path) -> None:
    root = _built(tmp_path)
    (root / "datasets/m.csv").unlink()
    assert verify(root) == ["Missing: datasets/m.csv"]


def test_an_edited_manifest_fails_verification(tmp_path: Path) -> None:
    root = _built(tmp_path)
    manifest = json.loads((root / MANIFEST).read_text("utf-8"))
    manifest["files"].pop()
    (root / MANIFEST).write_text(json.dumps(manifest), "utf-8")
    assert verify(root) == ["snapshot_id does not match the listed files"]


def test_no_manifest_fails_verification(tmp_path: Path) -> None:
    assert verify(tmp_path) == [f"No {MANIFEST} in {tmp_path}"]


def test_a_missing_source_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        copy_into(tmp_path / "snap", {"x": tmp_path / "absent"})


def test_the_id_depends_only_on_content(tmp_path: Path) -> None:
    first = _built(tmp_path)
    again = tmp_path / "again"
    files = copy_into(again, _sources(tmp_path / "second"))
    write_manifest(again, files, {"git_commit": "other"})
    ids = [
        json.loads((root / MANIFEST).read_text("utf-8"))["snapshot_id"]
        for root in (first, again)
    ]
    assert ids[0] == ids[1] == snapshot_id(files)

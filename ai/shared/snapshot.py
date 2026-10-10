"""Immutable serving snapshots: the files the API serves from, and their manifest.

A snapshot is a directory laid out like the repository (``ai/models/...``,
``datasets/processed/...``) plus ``manifest.json`` listing every file's path,
size and SHA-256 (ADR 025). Its ID is derived from those hashes, so the same
files always give the same ID and any changed byte gives a new one.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MANIFEST = "manifest.json"
MANIFEST_VERSION = 1
_CHUNK = 1 << 20


@dataclass(frozen=True)
class SnapshotFile:
    """One file in a snapshot, by its path relative to the snapshot root."""

    path: str
    bytes: int
    sha256: str


def sha256_of(path: Path) -> str:
    """Hex SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_id(files: Iterable[SnapshotFile]) -> str:
    """Short content ID: the same files always give the same ID."""
    lines = sorted(f"{f.path}:{f.sha256}" for f in files)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]


def copy_into(root: Path, sources: dict[str, Path]) -> list[SnapshotFile]:
    """Copy each source file to ``root/<relative path>`` and describe it."""
    described = []
    for relative, source in sorted(sources.items()):
        if not source.is_file():
            raise FileNotFoundError(f"Snapshot source missing: {source}")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        described.append(
            SnapshotFile(relative, target.stat().st_size, sha256_of(target))
        )
    return described


def write_manifest(
    root: Path, files: list[SnapshotFile], details: dict[str, Any]
) -> dict[str, Any]:
    """Write ``manifest.json`` for ``files`` with extra ``details``; return it."""
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "snapshot_id": snapshot_id(files),
        **details,
        "files": [asdict(f) for f in files],
    }
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    return manifest


def verify(root: Path) -> list[str]:
    """Problems with the snapshot at ``root``; empty when every file matches."""
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        return [f"No {MANIFEST} in {root}"]
    manifest = json.loads(manifest_path.read_text("utf-8"))
    files = [SnapshotFile(**entry) for entry in manifest.get("files", [])]
    problems = [problem for f in files if (problem := _check(root, f))]
    if manifest.get("snapshot_id") != snapshot_id(files):
        problems.append("snapshot_id does not match the listed files")
    return problems


def _check(root: Path, expected: SnapshotFile) -> str | None:
    path = root / expected.path
    if not path.is_file():
        return f"Missing: {expected.path}"
    if path.stat().st_size != expected.bytes or sha256_of(path) != expected.sha256:
        return f"Changed: {expected.path}"
    return None

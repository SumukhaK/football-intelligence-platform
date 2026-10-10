"""CLI: build or verify an immutable serving snapshot (ADR 025).

Usage:
    uv run python -m scripts.build_snapshot --out ../snapshot
    uv run python -m scripts.build_snapshot --out ../snapshot --no-index
    uv run python -m scripts.build_snapshot --verify ../snapshot

``--out`` copies the files the API serves from (both models, the registry,
the newest match and fixtures datasets and, unless ``--no-index``, the
assistant index) into a new directory laid out like the repository, and
writes ``manifest.json`` with each file's size and SHA-256. Source paths come
from the backend settings, so set the same ``.env`` values the server uses.
``--verify`` checks a snapshot against its manifest and exits 1 on any
difference.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import Settings, get_settings
from backend.app.services.fixtures_service import find_latest_fixtures
from inference.fixture_features import find_latest_dataset
from model_registry.registry import ModelRegistry
from shared.snapshot import copy_into, verify, write_manifest

# Names the index's embedding model, when the pipeline that built it wrote one.
INDEX_INFO = "index.json"
_INDEX_FILES = ("embeddings.npy", "documents.json", INDEX_INFO)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build_snapshot")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--out", type=Path, help="New directory to build into")
    action.add_argument("--verify", type=Path, help="Snapshot directory to check")
    parser.add_argument(
        "--no-index", action="store_true", help="Leave the assistant index out"
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path(".."), help="Repository root"
    )
    return parser


def serving_files(
    settings: Settings, repo_root: Path, with_index: bool
) -> dict[str, Path]:
    """Snapshot-relative path to source file for everything the API loads."""
    sources = [
        settings.model_path,
        settings.v1_model_path,
        settings.registry_path,
        find_latest_dataset(settings.matches_dir),
        find_latest_fixtures(settings.fixtures_dir),
    ]
    if with_index:
        store = settings.assistant_vector_store_path
        sources += [store / name for name in _INDEX_FILES if (store / name).exists()]
    root = repo_root.resolve()
    return {source.resolve().relative_to(root).as_posix(): source for source in sources}


def snapshot_details(settings: Settings, with_index: bool) -> dict[str, Any]:
    """What the manifest says about the snapshot besides its files."""
    latest = ModelRegistry(settings.registry_path).latest()
    info = settings.assistant_vector_store_path / INDEX_INFO
    index = json.loads(info.read_text("utf-8")) if with_index and info.exists() else {}
    return {
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "model_version": latest.version if latest else None,
        "v1_model_version": settings.v1_model_version,
        "index_embed_model": index.get("embed_model"),
    }


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def build(out: Path, settings: Settings, repo_root: Path, with_index: bool) -> str:
    """Build a snapshot in the new directory ``out``; return its ID."""
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} is not empty; snapshots are never changed")
    sources = serving_files(settings, repo_root, with_index)
    files = copy_into(out, sources)
    manifest = write_manifest(out, files, snapshot_details(settings, with_index))
    return str(manifest["snapshot_id"])


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns 0 on success, 1 on failure."""
    args = _build_arg_parser().parse_args(argv)
    if args.verify is not None:
        problems = verify(args.verify)
        for problem in problems:
            print(problem, file=sys.stderr)
        print("Snapshot OK" if not problems else "Snapshot FAILED")
        return 1 if problems else 0
    try:
        snapshot = build(args.out, get_settings(), args.repo_root, not args.no_index)
    except Exception as exc:  # noqa: BLE001 — surface any failure as exit code 1
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Snapshot {snapshot} written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

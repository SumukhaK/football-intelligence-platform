"""Tests for assistant.ingestion.loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assistant.ingestion.loader import DocumentLoader


@pytest.fixture()
def knowledge_root(tmp_path: Path) -> Path:
    """Create a minimal knowledge-base directory tree."""
    models_dir = tmp_path / "models" / "latest"
    models_dir.mkdir(parents=True)
    (models_dir / "model_card.md").write_text(
        "# Model Card\n\nTest accuracy: 56%.", encoding="utf-8"
    )
    (models_dir / "evaluation_report.json").write_text(
        json.dumps({"accuracy": 0.56}), encoding="utf-8"
    )

    adr_dir = tmp_path.parent / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / "001-xgboost.md").write_text(
        "# ADR 001\n\nUse XGBoost.", encoding="utf-8"
    )
    return tmp_path


def test_loader_finds_markdown(knowledge_root: Path) -> None:
    """DocumentLoader loads model card markdown files."""
    loader = DocumentLoader(knowledge_root)
    docs = loader.load_all()
    sources = [d.source for d in docs]
    assert any("model_card.md" in s for s in sources)


def test_loader_finds_json(knowledge_root: Path) -> None:
    """DocumentLoader loads JSON evaluation reports."""
    loader = DocumentLoader(knowledge_root)
    docs = loader.load_all()
    sources = [d.source for d in docs]
    assert any("evaluation_report.json" in s for s in sources)


def test_loader_assigns_doc_type(knowledge_root: Path) -> None:
    """DocumentLoader assigns doc_type to each document."""
    loader = DocumentLoader(knowledge_root)
    docs = loader.load_all()
    doc_types = {d.doc_type for d in docs}
    assert "model_card" in doc_types or "evaluation_report" in doc_types


def test_loader_skips_missing_paths(tmp_path: Path) -> None:
    """DocumentLoader returns empty list when knowledge root is empty."""
    loader = DocumentLoader(tmp_path)
    docs = loader.load_all()
    assert isinstance(docs, list)


def test_loader_text_is_nonempty(knowledge_root: Path) -> None:
    """All loaded documents have non-empty text."""
    loader = DocumentLoader(knowledge_root)
    docs = loader.load_all()
    for doc in docs:
        assert doc.text.strip(), f"Empty text in {doc.source}"

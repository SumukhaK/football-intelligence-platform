"""Tests for assistant.retrieval.vector_store."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import VectorStore


def _make_docs(n: int) -> list[Document]:
    return [
        Document(id=f"d{i}", text=f"text {i}", source=f"src{i}.md") for i in range(n)
    ]


def _make_embeddings(n: int, dim: int = 4) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.standard_normal((n, dim)).astype(np.float32)


def test_store_initially_empty() -> None:
    """A new VectorStore is empty."""
    store = VectorStore()
    assert store.is_empty()
    assert store.size() == 0


def test_store_add_increases_size() -> None:
    """Adding documents increases the store size."""
    store = VectorStore()
    docs = _make_docs(3)
    embs = _make_embeddings(3)
    store.add(docs, embs)
    assert store.size() == 3


def test_store_add_multiple_batches() -> None:
    """Documents can be added in multiple batches."""
    store = VectorStore()
    store.add(_make_docs(2), _make_embeddings(2))
    store.add(_make_docs(3), _make_embeddings(3))
    assert store.size() == 5


def test_store_clear_resets_to_empty() -> None:
    """clear() removes all documents."""
    store = VectorStore()
    store.add(_make_docs(2), _make_embeddings(2))
    store.clear()
    assert store.is_empty()


def test_store_get_all_documents() -> None:
    """get_all_documents returns the list of added documents."""
    docs = _make_docs(3)
    store = VectorStore()
    store.add(docs, _make_embeddings(3))
    returned = store.get_all_documents()
    assert len(returned) == 3
    assert returned[0].id == "d0"


def test_store_get_all_embeddings_shape() -> None:
    """get_all_embeddings returns (n, dim) array."""
    store = VectorStore()
    store.add(_make_docs(4), _make_embeddings(4, dim=8))
    matrix = store.get_all_embeddings()
    assert matrix.shape == (4, 8)


def test_store_mismatched_lengths_raises() -> None:
    """add() raises ValueError when docs and embeddings lengths differ."""
    store = VectorStore()
    with pytest.raises(ValueError, match="same length"):
        store.add(_make_docs(3), _make_embeddings(2))


def test_store_save_and_load(tmp_path: Path) -> None:
    """Saved store can be loaded and produces identical results."""
    docs = _make_docs(5)
    embs = _make_embeddings(5, dim=4)
    store = VectorStore()
    store.add(docs, embs)
    store.save(tmp_path)

    loaded = VectorStore.load(tmp_path)
    assert loaded.size() == 5
    assert loaded.get_all_documents()[0].id == docs[0].id
    np.testing.assert_allclose(loaded.get_all_embeddings(), embs, rtol=1e-5)


def test_store_load_missing_path_raises(tmp_path: Path) -> None:
    """Loading from a missing path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        VectorStore.load(tmp_path / "nonexistent")

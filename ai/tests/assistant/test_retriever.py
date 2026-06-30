"""Tests for assistant.retrieval.retriever."""

from __future__ import annotations

import numpy as np
import pytest

from assistant.ingestion.document import Document
from assistant.retrieval.retriever import retrieve
from assistant.retrieval.vector_store import VectorStore


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)  # type: ignore[no-any-return]


def _store_with(docs: list[Document], embeddings: np.ndarray) -> VectorStore:
    store = VectorStore()
    store.add(docs, embeddings)
    return store


def test_retrieve_returns_top_k() -> None:
    """retrieve returns at most top_k results."""
    rng = np.random.default_rng(0)
    docs = [Document(id=f"d{i}", text=f"t{i}", source="s") for i in range(10)]
    embs = rng.standard_normal((10, 4)).astype(np.float32)
    store = _store_with(docs, embs)

    query = rng.standard_normal(4).astype(np.float32)
    results = retrieve(query, store, top_k=3)
    assert len(results) == 3


def test_retrieve_sorted_descending() -> None:
    """Results are ordered from most to least relevant."""
    rng = np.random.default_rng(1)
    docs = [Document(id=f"d{i}", text=f"t{i}", source="s") for i in range(5)]
    embs = rng.standard_normal((5, 4)).astype(np.float32)
    store = _store_with(docs, embs)

    query = rng.standard_normal(4).astype(np.float32)
    results = retrieve(query, store, top_k=5)
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_identical_vector_scores_high() -> None:
    """A query identical to a stored vector scores close to 1."""
    doc = Document(id="d0", text="match", source="s")
    vec = _unit(np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32))
    store = _store_with([doc], vec.reshape(1, -1))
    results = retrieve(vec, store, top_k=1)
    _, score = results[0]
    assert score > 0.99


def test_retrieve_scores_in_unit_range() -> None:
    """All retrieval scores are in [0, 1]."""
    rng = np.random.default_rng(7)
    docs = [Document(id=f"d{i}", text=f"t{i}", source="s") for i in range(6)]
    embs = rng.standard_normal((6, 8)).astype(np.float32)
    store = _store_with(docs, embs)
    query = rng.standard_normal(8).astype(np.float32)
    results = retrieve(query, store, top_k=6)
    for _, score in results:
        assert 0.0 <= score <= 1.0


def test_retrieve_empty_store_raises() -> None:
    """retrieve raises ValueError when the store is empty."""
    store = VectorStore()
    query = np.ones(4, dtype=np.float32)
    with pytest.raises(ValueError, match="empty"):
        retrieve(query, store)


def test_retrieve_top_k_capped_at_store_size() -> None:
    """Requesting more results than the store has is handled gracefully."""
    docs = [Document(id="d0", text="t", source="s")]
    embs = np.ones((1, 4), dtype=np.float32)
    store = _store_with(docs, embs)
    results = retrieve(np.ones(4, dtype=np.float32), store, top_k=100)
    assert len(results) == 1

"""Shared fixtures for the assistant test suite."""

from __future__ import annotations

import numpy as np
import pytest

from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import VectorStore

# ---------------------------------------------------------------------------
# Fake Embedder and Generator
# ---------------------------------------------------------------------------


class FakeEmbedder:
    """Deterministic embedder that returns the same unit vector for any text."""

    def __init__(self, dim: int = 8) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return (n, dim) array with identical unit rows."""
        vec = np.ones(self._dim, dtype=np.float32) / np.sqrt(self._dim)
        return np.tile(vec, (len(texts), 1))


class VariedEmbedder:
    """Embedder that returns distinct vectors based on text hash."""

    def __init__(self, dim: int = 8) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        out = []
        for text in texts:
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            vec = rng.standard_normal(self._dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            out.append(vec / norm if norm > 0 else vec)
        return np.array(out, dtype=np.float32)


class FakeGenerator:
    """Generator that returns a canned answer."""

    def __init__(self, answer: str = "Test answer.") -> None:
        self._answer = answer

    def generate(self, messages: list[dict[str, str]]) -> str:
        return self._answer


# ---------------------------------------------------------------------------
# Document fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_docs() -> list[Document]:
    """Three minimal Document objects for testing."""
    return [
        Document(
            id="doc1",
            text="The XGBoost model achieved 56% test accuracy on Premier League data.",
            source="model_card.md",
            doc_type="model_card",
            metadata={"filename": "model_card.md"},
        ),
        Document(
            id="doc2",
            text=(
                "SHAP values show that home_goals_scored_last10 is the most "
                "important feature for predicting home wins."
            ),
            source="global_summary.json",
            doc_type="shap_global_summary",
            metadata={"filename": "global_summary.json"},
        ),
        Document(
            id="doc3",
            text=(
                "ADR 001: XGBoost was chosen for its native NaN handling and "
                "excellent SHAP integration."
            ),
            source="001-use-xgboost-for-predictions.md",
            doc_type="adr",
            metadata={"filename": "001-use-xgboost-for-predictions.md"},
        ),
    ]


@pytest.fixture()
def populated_store(sample_docs: list[Document]) -> VectorStore:
    """A VectorStore pre-populated with sample documents."""
    embedder = VariedEmbedder(dim=8)
    texts = [d.text for d in sample_docs]
    embeddings = embedder.embed(texts)
    store = VectorStore()
    store.add(sample_docs, embeddings)
    return store


@pytest.fixture()
def fake_embedder() -> FakeEmbedder:
    """Return a FakeEmbedder instance."""
    return FakeEmbedder(dim=8)


@pytest.fixture()
def fake_generator() -> FakeGenerator:
    """Return a FakeGenerator instance."""
    return FakeGenerator()

"""Tests for evaluation.relevance_cutoff, with no provider calls."""

from __future__ import annotations

import numpy as np

from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import VectorStore
from evaluation.relevance_cutoff import Separation, separation, top_scores


class OneHotEmbedder:
    """Embeds "in" questions along x and everything else along y."""

    def embed(self, texts: list[str]) -> np.ndarray:
        rows = [[1.0, 0.0] if t.startswith("in") else [0.0, 1.0] for t in texts]
        return np.array(rows, dtype=np.float32)


def test_top_scores_read_the_best_match() -> None:
    store = VectorStore()
    store.add(
        [Document(id="d", text="t", source="s")], np.array([[1.0, 0.0]], np.float32)
    )
    scores = top_scores(("in a", "out b"), OneHotEmbedder(), store)
    assert scores["in a"] > scores["out b"]


def test_separable_groups_get_a_cut_off_between_them() -> None:
    result = separation({"a": 0.80, "b": 0.85}, {"c": 0.70, "d": 0.74})
    assert result.separable
    assert result.cut_off == 0.77


def test_overlapping_groups_are_not_separable() -> None:
    assert not Separation(lowest_in_scope=0.75, highest_out_of_scope=0.78).separable

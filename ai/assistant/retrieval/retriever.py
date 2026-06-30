"""Retriever — cosine similarity search over the vector store."""

from __future__ import annotations

import numpy as np

from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import VectorStore

RetrievedDoc = tuple[Document, float]


def retrieve(
    query_embedding: np.ndarray,
    store: VectorStore,
    top_k: int = 5,
) -> list[RetrievedDoc]:
    """Return the *top_k* most relevant documents from *store*.

    Similarity is computed as normalised cosine similarity in [0, 1]:
    ``(dot_product + 1) / 2`` so that antipodal vectors score 0 and
    identical vectors score 1.

    Args:
        query_embedding: 1-D float32 array of shape ``(embed_dim,)``.
        store: Populated :class:`VectorStore`.
        top_k: Maximum number of results to return.

    Returns:
        List of ``(Document, score)`` pairs, sorted descending by score.

    Raises:
        ValueError: When the store is empty.
    """
    if store.is_empty():
        raise ValueError("The vector store is empty. Build the index before querying.")

    matrix = store.get_all_embeddings()
    q = query_embedding.astype(np.float32).reshape(-1)

    q_norm = np.linalg.norm(q)
    if q_norm == 0.0:
        raise ValueError("Query embedding is a zero vector.")

    row_norms = np.linalg.norm(matrix, axis=1)
    row_norms = np.where(row_norms == 0.0, 1e-12, row_norms)

    cosines = (matrix @ q) / (row_norms * q_norm)
    scores = (cosines + 1.0) / 2.0

    k = min(top_k, len(store.get_all_documents()))
    top_indices = np.argsort(scores)[::-1][:k]

    documents = store.get_all_documents()
    return [(documents[int(i)], float(scores[i])) for i in top_indices]

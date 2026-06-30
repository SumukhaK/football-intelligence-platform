"""VectorStore — numpy-backed persistent store for document embeddings."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from assistant.ingestion.document import Document

logger = logging.getLogger(__name__)

_EMBEDDINGS_FILE = "embeddings.npy"
_DOCUMENTS_FILE = "documents.json"


class VectorStore:
    """In-memory vector store backed by numpy arrays with file persistence.

    Embeddings are stored as a 2-D float32 ndarray of shape
    ``(n_docs, embed_dim)``. Documents are stored in a parallel list.
    """

    def __init__(self) -> None:
        """Initialise an empty store."""
        self._documents: list[Document] = []
        self._embeddings: np.ndarray = np.empty((0, 0), dtype=np.float32)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, documents: list[Document], embeddings: np.ndarray) -> None:
        """Append *documents* and their corresponding *embeddings*.

        *embeddings* must have shape ``(len(documents), embed_dim)``.
        """
        if len(documents) != embeddings.shape[0]:
            raise ValueError(
                f"documents ({len(documents)}) and embeddings "
                f"({embeddings.shape[0]}) must have the same length"
            )
        if not documents:
            return
        if self._embeddings.shape[0] == 0:
            self._embeddings = embeddings.astype(np.float32)
        else:
            if embeddings.shape[1] != self._embeddings.shape[1]:
                raise ValueError("Embedding dimension mismatch")
            self._embeddings = np.vstack(
                [self._embeddings, embeddings.astype(np.float32)]
            )
        self._documents.extend(documents)

    def clear(self) -> None:
        """Remove all documents and embeddings from the store."""
        self._documents = []
        self._embeddings = np.empty((0, 0), dtype=np.float32)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def size(self) -> int:
        """Return the number of stored documents."""
        return len(self._documents)

    def is_empty(self) -> bool:
        """Return True when no documents have been added."""
        return len(self._documents) == 0

    def get_all_documents(self) -> list[Document]:
        """Return a copy of the document list."""
        return list(self._documents)

    def get_all_embeddings(self) -> np.ndarray:
        """Return the embedding matrix (n_docs, embed_dim)."""
        return self._embeddings

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Persist embeddings and document metadata to *path*."""
        path.mkdir(parents=True, exist_ok=True)
        np.save(path / _EMBEDDINGS_FILE, self._embeddings)
        doc_list = [d.to_dict() for d in self._documents]
        (path / _DOCUMENTS_FILE).write_text(
            json.dumps(doc_list, indent=2), encoding="utf-8"
        )
        logger.info("Saved vector store: %d documents → %s", len(self._documents), path)

    @classmethod
    def load(cls, path: Path) -> VectorStore:
        """Load a previously saved store from *path*."""
        emb_path = path / _EMBEDDINGS_FILE
        doc_path = path / _DOCUMENTS_FILE
        if not emb_path.exists() or not doc_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {path}. "
                "Run the assistant pipeline to build the index first."
            )
        store = cls()
        store._embeddings = np.load(emb_path).astype(np.float32)
        raw = json.loads(doc_path.read_text(encoding="utf-8"))
        store._documents = [Document.from_dict(d) for d in raw]
        logger.info("Loaded vector store: %d documents from %s", store.size(), path)
        return store

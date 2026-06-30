"""TextChunker — splits Document text into overlapping chunks."""

from __future__ import annotations

import hashlib

from assistant.ingestion.document import Document


class TextChunker:
    """Splits documents into fixed-size character chunks with overlap.

    Both *chunk_size* and *overlap* are measured in characters.
    """

    def __init__(self, chunk_size: int = 600, overlap: int = 80) -> None:
        """Initialise with chunk size and overlap in characters."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document: Document) -> list[Document]:
        """Return a list of chunk Documents derived from *document*."""
        text = document.text.strip()
        if not text:
            return []

        chunks = self._split_text(text)
        result: list[Document] = []
        for idx, chunk_text in enumerate(chunks):
            chunk_id = _chunk_id(document.id, idx)
            result.append(
                Document(
                    id=chunk_id,
                    text=chunk_text,
                    source=document.source,
                    doc_type=document.doc_type,
                    metadata={
                        **document.metadata,
                        "chunk_index": str(idx),
                        "chunk_count": str(len(chunks)),
                        "parent_id": document.id,
                    },
                )
            )
        return result

    def chunk_all(self, documents: list[Document]) -> list[Document]:
        """Chunk all documents and return the combined list."""
        result: list[Document] = []
        for doc in documents:
            result.extend(self.chunk(doc))
        return result

    def _split_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start += self._chunk_size - self._overlap
        return chunks


def _chunk_id(parent_id: str, index: int) -> str:
    """Generate a stable chunk ID from parent ID and index."""
    raw = f"{parent_id}:{index}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:8]
    return f"{parent_id}_chunk{index}_{digest}"

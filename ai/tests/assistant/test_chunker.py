"""Tests for assistant.chunking.chunker."""

from __future__ import annotations

import pytest

from assistant.chunking.chunker import TextChunker
from assistant.ingestion.document import Document


@pytest.fixture()
def base_doc() -> Document:
    """A document with 200-character text for chunking."""
    return Document(
        id="base",
        text="A" * 200,
        source="test.md",
        doc_type="report",
        metadata={"filename": "test.md"},
    )


def test_chunker_single_chunk_for_short_text() -> None:
    """Short text that fits in one chunk returns exactly one chunk."""
    chunker = TextChunker(chunk_size=500, overlap=50)
    doc = Document(id="d", text="short text", source="s")
    chunks = chunker.chunk(doc)
    assert len(chunks) == 1
    assert chunks[0].text == "short text"


def test_chunker_splits_long_text(base_doc: Document) -> None:
    """Text longer than chunk_size is split into multiple chunks."""
    chunker = TextChunker(chunk_size=80, overlap=10)
    chunks = chunker.chunk(base_doc)
    assert len(chunks) > 1


def test_chunker_overlap_present(base_doc: Document) -> None:
    """Consecutive chunks share overlapping characters."""
    chunker = TextChunker(chunk_size=80, overlap=20)
    chunks = chunker.chunk(base_doc)
    if len(chunks) > 1:
        end_of_first = chunks[0].text[-20:]
        start_of_second = chunks[1].text[:20]
        assert end_of_first == start_of_second


def test_chunker_preserves_source(base_doc: Document) -> None:
    """All chunks inherit the parent document's source."""
    chunker = TextChunker(chunk_size=80, overlap=10)
    chunks = chunker.chunk(base_doc)
    for chunk in chunks:
        assert chunk.source == base_doc.source


def test_chunker_sets_parent_id(base_doc: Document) -> None:
    """Each chunk records the parent document id in its metadata."""
    chunker = TextChunker(chunk_size=80, overlap=10)
    chunks = chunker.chunk(base_doc)
    for chunk in chunks:
        assert chunk.metadata.get("parent_id") == base_doc.id


def test_chunker_empty_document_returns_empty() -> None:
    """An empty document produces no chunks."""
    chunker = TextChunker(chunk_size=200, overlap=20)
    doc = Document(id="e", text="", source="empty.md")
    assert chunker.chunk(doc) == []


def test_chunker_invalid_params() -> None:
    """Invalid constructor params raise ValueError."""
    with pytest.raises(ValueError, match="chunk_size"):
        TextChunker(chunk_size=0, overlap=0)
    with pytest.raises(ValueError, match="overlap"):
        TextChunker(chunk_size=100, overlap=-1)
    with pytest.raises(ValueError, match="overlap"):
        TextChunker(chunk_size=100, overlap=100)


def test_chunk_all_processes_multiple_docs() -> None:
    """chunk_all returns chunks for all provided documents."""
    chunker = TextChunker(chunk_size=50, overlap=5)
    docs = [Document(id=f"d{i}", text="X" * 120, source=f"doc{i}.md") for i in range(3)]
    all_chunks = chunker.chunk_all(docs)
    assert len(all_chunks) > 3

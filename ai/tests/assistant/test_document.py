"""Tests for assistant.ingestion.document."""

from __future__ import annotations

from assistant.ingestion.document import Document


def test_document_round_trip() -> None:
    """Document serialises and deserialises to the same values."""
    doc = Document(
        id="d1",
        text="Some content",
        source="/path/to/file.md",
        doc_type="report",
        metadata={"filename": "file.md", "type": "report"},
    )
    restored = Document.from_dict(doc.to_dict())
    assert restored == doc


def test_document_defaults() -> None:
    """Document with minimal fields uses correct defaults."""
    doc = Document(id="x", text="hello", source="src.txt")
    assert doc.doc_type == ""
    assert doc.metadata == {}


def test_document_is_frozen() -> None:
    """Document instances are immutable."""
    doc = Document(id="x", text="hello", source="src.txt")
    try:
        doc.id = "y"  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except Exception:
        pass


def test_from_dict_handles_missing_optional_keys() -> None:
    """from_dict tolerates missing doc_type and metadata keys."""
    data: dict[str, object] = {"id": "a", "text": "t", "source": "s"}
    doc = Document.from_dict(data)
    assert doc.id == "a"
    assert doc.doc_type == ""
    assert doc.metadata == {}

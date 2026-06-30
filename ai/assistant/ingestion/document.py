"""Document — the atom of the RAG knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast


@dataclass(frozen=True)
class Document:
    """A single piece of text from the knowledge base with provenance."""

    id: str
    text: str
    source: str
    doc_type: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a JSON-compatible dict."""
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "doc_type": self.doc_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Document:
        """Deserialise from a dict produced by :meth:`to_dict`."""
        return cls(
            id=str(data["id"]),
            text=str(data["text"]),
            source=str(data["source"]),
            doc_type=str(data.get("doc_type", "")),
            metadata={
                str(k): str(v)
                for k, v in (
                    cast(dict[str, object], data["metadata"]).items()
                    if isinstance(data.get("metadata"), dict)
                    else []
                )
            },
        )

"""AssistantService — orchestrates the RAG pipeline end-to-end."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from assistant.embeddings.embedder import Embedder
from assistant.generation.generator import Generator
from assistant.prompting.templates import build_messages
from assistant.retrieval.retriever import RetrievedDoc, retrieve
from assistant.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceDocument:
    """A retrieved document with its relevance score and a short excerpt."""

    source: str
    excerpt: str
    relevance_score: float


@dataclass(frozen=True)
class AssistantResponse:
    """Full response from the assistant including answer and retrieved sources."""

    answer: str
    sources: list[SourceDocument]
    confidence: float
    model: str
    retrieved_count: int


_EXCERPT_LENGTH = 200
_NO_INFO_MARKER = "I don't have enough information"


class AssistantService:
    """Retrieval-augmented generation service for football questions.

    Composes: embed → retrieve → prompt → generate → structured response.
    """

    def __init__(
        self,
        embedder: Embedder,
        generator: Generator,
        store: VectorStore,
        model_name: str,
        top_k: int = 5,
    ) -> None:
        """Initialise with injected components."""
        self._embedder = embedder
        self._generator = generator
        self._store = store
        self._model_name = model_name
        self._top_k = top_k

    def chat(self, question: str) -> AssistantResponse:
        """Answer *question* using RAG over the local knowledge base.

        Raises:
            ValueError: When *question* is empty.
            :exc:`VectorStoreEmptyError`: When the index has not been built.
        """
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty.")

        if self._store.is_empty():
            raise VectorStoreEmptyError(
                "The knowledge base index is empty. "
                "Run the assistant pipeline to build the index first."
            )

        query_emb = self._embedder.embed([question])[0]
        retrieved: list[RetrievedDoc] = retrieve(query_emb, self._store, self._top_k)

        messages = build_messages(question, retrieved)
        answer = self._generator.generate(messages)

        sources = _build_sources(retrieved)
        confidence = _compute_confidence(retrieved, answer)

        logger.info(
            "Chat: retrieved=%d confidence=%.2f model=%s",
            len(retrieved),
            confidence,
            self._model_name,
        )
        return AssistantResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            model=self._model_name,
            retrieved_count=len(retrieved),
        )


class VectorStoreEmptyError(RuntimeError):
    """Raised when the vector store has not been populated."""


def _build_sources(retrieved: list[RetrievedDoc]) -> list[SourceDocument]:
    seen: set[str] = set()
    sources: list[SourceDocument] = []
    for doc, score in retrieved:
        if doc.source in seen:
            continue
        seen.add(doc.source)
        excerpt = doc.text.strip()[:_EXCERPT_LENGTH].replace("\n", " ")
        sources.append(
            SourceDocument(
                source=doc.metadata.get("filename", doc.source),
                excerpt=excerpt,
                relevance_score=round(score, 4),
            )
        )
    return sources


def _compute_confidence(retrieved: list[RetrievedDoc], answer: str) -> float:
    if not retrieved:
        return 0.0
    top_score = retrieved[0][1]
    if _NO_INFO_MARKER in answer:
        return round(top_score * 0.3, 4)
    return round(top_score, 4)

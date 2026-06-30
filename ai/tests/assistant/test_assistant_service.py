"""Tests for assistant.services.assistant_service."""

from __future__ import annotations

import pytest

from assistant.ingestion.document import Document
from assistant.services.assistant_service import (
    AssistantService,
    VectorStoreEmptyError,
)
from tests.assistant.conftest import FakeEmbedder, FakeGenerator, VariedEmbedder


def _make_service(
    sample_docs: list[Document],
    answer: str = "The model accuracy is 56%.",
) -> AssistantService:
    from assistant.retrieval.vector_store import VectorStore

    embedder = VariedEmbedder(dim=8)
    texts = [d.text for d in sample_docs]
    embeddings = embedder.embed(texts)
    store = VectorStore()
    store.add(sample_docs, embeddings)
    return AssistantService(
        embedder=embedder,
        generator=FakeGenerator(answer=answer),
        store=store,
        model_name="llama3.2",
        top_k=3,
    )


def test_service_returns_assistant_response(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """AssistantService.chat returns a valid AssistantResponse."""
    service = _make_service(sample_docs)
    resp = service.chat("What is the model accuracy?")
    assert resp.answer == "The model accuracy is 56%."
    assert resp.model == "llama3.2"
    assert resp.retrieved_count > 0


def test_service_returns_sources(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """AssistantResponse includes at least one source document."""
    service = _make_service(sample_docs)
    resp = service.chat("Explain the model.")
    assert len(resp.sources) > 0
    for src in resp.sources:
        assert src.source
        assert src.excerpt


def test_service_confidence_in_unit_range(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """Confidence score is between 0 and 1."""
    service = _make_service(sample_docs)
    resp = service.chat("Tell me about SHAP.")
    assert 0.0 <= resp.confidence <= 1.0


def test_service_empty_question_raises(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """chat() with an empty message raises ValueError."""
    service = _make_service(sample_docs)
    with pytest.raises(ValueError, match="empty"):
        service.chat("")


def test_service_whitespace_question_raises(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """chat() with whitespace-only message raises ValueError."""
    service = _make_service(sample_docs)
    with pytest.raises(ValueError, match="empty"):
        service.chat("   ")


def test_service_empty_store_raises() -> None:
    """chat() raises VectorStoreEmptyError when the index is not built."""
    from assistant.retrieval.vector_store import VectorStore

    store = VectorStore()
    service = AssistantService(
        embedder=FakeEmbedder(),
        generator=FakeGenerator(),
        store=store,
        model_name="m",
    )
    with pytest.raises(VectorStoreEmptyError):
        service.chat("Who wins?")


def test_service_low_confidence_on_no_info_answer(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """Confidence is lower when answer says 'I don't have enough information'."""
    no_info = "I don't have enough information in my knowledge base to answer that."
    service = _make_service(sample_docs, answer=no_info)
    resp = service.chat("Random question?")
    normal_service = _make_service(sample_docs, answer="Normal answer.")
    normal_resp = normal_service.chat("Random question?")
    assert resp.confidence < normal_resp.confidence

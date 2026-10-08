"""Tests for assistant.services.assistant_service."""

from __future__ import annotations

import json
from typing import Any

import pytest

from assistant.generation.generator import ChatTurn, ToolCall
from assistant.ingestion.document import Document
from assistant.services.assistant_service import (
    AssistantService,
    VectorStoreEmptyError,
)
from assistant.tools.routing import Route
from assistant.tools.tool import Tool
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


class ScriptedToolGenerator:
    """Tool-calling fake: plays back turns and records the messages it saw."""

    def __init__(self, turns: list[ChatTurn]) -> None:
        self._turns = list(turns)
        self.calls: list[tuple[list[dict[str, Any]], list[dict[str, Any]]]] = []

    def generate(self, messages: list[dict[str, str]]) -> str:
        raise AssertionError("A tool-calling generator should be used via chat().")

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ChatTurn:
        self.calls.append((list(messages), tools))
        return self._turns.pop(0)


_PREDICTION = {"predicted_result": "H", "probability_home": 0.4712}


def _predict_tool() -> Tool:
    return Tool(
        "predict_match",
        "Match prediction.",
        {"type": "object"},
        lambda args: {**_PREDICTION, "home_team": args["home_team"]},
    )


def _tool_service(sample_docs: list[Document], generator: Any) -> AssistantService:
    service = _make_service(sample_docs)
    return AssistantService(
        embedder=VariedEmbedder(dim=8),
        generator=generator,
        store=service._store,
        model_name="llama3.2",
        top_k=3,
        tools=[_predict_tool()],
    )


def test_service_runs_tool_and_feeds_result_back(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """The model's tool call is run and its JSON result reaches the next turn."""
    call = ToolCall("predict_match", {"home_team": "Arsenal", "away_team": "Leeds"})
    generator = ScriptedToolGenerator(
        [ChatTurn("", [call]), ChatTurn("Arsenal win at 47.1% [source: tool].")]
    )

    resp = _tool_service(sample_docs, generator).chat("Arsenal v Leeds?")

    assert resp.answer == "Arsenal win at 47.1% [source: tool]."
    offered = generator.calls[0][1]
    assert offered[0]["function"]["name"] == "predict_match"
    second_messages = generator.calls[1][0]
    assert second_messages[-2]["tool_calls"][0]["function"]["name"] == "predict_match"
    tool_message = second_messages[-1]
    assert tool_message["role"] == "tool"
    assert json.loads(tool_message["content"]) == {
        **_PREDICTION,
        "home_team": "Arsenal",
    }


def test_service_stops_calling_tools_after_the_cap(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """A model that keeps calling tools is asked for a final answer without them."""
    call = ToolCall("predict_match", {"home_team": "Arsenal"})
    generator = ScriptedToolGenerator(
        [ChatTurn("", [call])] * 3 + [ChatTurn("Final answer.")]
    )

    resp = _tool_service(sample_docs, generator).chat("Arsenal?")

    assert resp.answer == "Final answer."
    assert len(generator.calls) == 4
    assert generator.calls[-1][1] == []


def test_service_without_tools_uses_plain_generation(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """With no tools configured the service keeps calling generate()."""
    resp = _make_service(sample_docs, answer="Plain.").chat("Question?")
    assert resp.answer == "Plain."


class _FixedRouter:
    def __init__(self, route: Route | None) -> None:
        self._route = route

    def route(self, question: str) -> Route | None:
        return self._route


class _CountingEmbedder(VariedEmbedder):
    calls = 0

    def embed(self, texts: list[str]) -> Any:
        _CountingEmbedder.calls += 1
        return super().embed(texts)


def _routed_service(
    sample_docs: list[Document], generator: Any, route: Route | None
) -> AssistantService:
    base = _make_service(sample_docs)
    return AssistantService(
        embedder=_CountingEmbedder(dim=8),
        generator=generator,
        store=base._store,
        model_name="qwen2.5",
        tools=[_predict_tool()],
        router=_FixedRouter(route),
    )


def test_router_reply_skips_retrieval_and_the_model(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """A fixed reply is returned as is, with no embedding or generation."""
    generator = ScriptedToolGenerator([])
    _CountingEmbedder.calls = 0
    service = _routed_service(sample_docs, generator, Route(reply="No players."))

    resp = service.chat("Who is the top scorer?")

    assert (resp.answer, resp.model, resp.sources) == ("No players.", "router", [])
    assert generator.calls == []
    assert _CountingEmbedder.calls == 0


def test_routed_calls_run_before_the_model_answers(sample_docs) -> None:  # type: ignore[no-untyped-def]
    """Routed tool results are in the conversation the model first sees."""
    generator = ScriptedToolGenerator([ChatTurn("Arsenal at 47.1%.")])
    route = Route(calls=[ToolCall("predict_match", {"home_team": "Arsenal"})])

    resp = _routed_service(sample_docs, generator, route).chat("Arsenal next?")

    assert resp.answer == "Arsenal at 47.1%."
    assert resp.retrieved_count == 0
    first_messages = generator.calls[0][0]
    assert first_messages[-1]["role"] == "tool"
    assert json.loads(first_messages[-1]["content"])["home_team"] == "Arsenal"

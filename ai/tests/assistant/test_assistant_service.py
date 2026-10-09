"""Tests for assistant.services.assistant_service."""

from __future__ import annotations

import json
from collections.abc import Callable
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


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

Events = Callable[[str], list[tuple[str, dict[str, Any]]]]


class _StepClock:
    """Each call moves time on by a quarter of a second."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        self.now += 0.25
        return self.now


def _clocked(service: AssistantService) -> AssistantService:
    service._clock = _StepClock()
    return service


def _answer(events: Events) -> dict[str, Any]:
    ((severity, attributes),) = events("assistant.answer")
    assert severity == "INFO"
    return attributes


def test_answer_from_retrieval_is_logged(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    service = _clocked(_make_service(sample_docs, answer="Accuracy is 56%."))
    service.chat("What is the model accuracy?")
    attributes = _answer(events)
    assert attributes["path"] == "model"
    assert attributes["question_chars"] == len("What is the model accuracy?")
    assert attributes["retrieved_count"] == 3
    assert isinstance(attributes["top_score"], float)
    assert attributes["tool_rounds"] == 0
    assert attributes["model"] == "llama3.2"
    assert attributes["duration_ms"] == 250
    assert (attributes["prompt_tokens"], attributes["cost_usd"]) == (None, None)
    assert events("assistant.abstain") == []


def test_tool_calls_are_logged(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    call = ToolCall("predict_match", {"home_team": "Arsenal"})
    generator = ScriptedToolGenerator([ChatTurn("", [call]), ChatTurn("Done.")])
    _clocked(_tool_service(sample_docs, generator)).chat("Arsenal?")
    assert events("assistant.tool") == [
        (
            "INFO",
            {
                "tool": "predict_match",
                "status": "ok",
                "duration_ms": 250,
                "error": None,
            },
        )
    ]
    attributes = _answer(events)
    assert (attributes["path"], attributes["tool_rounds"]) == ("model_with_tools", 1)


def test_a_failed_tool_is_a_warning(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    call = ToolCall("made_up_tool", {})
    generator = ScriptedToolGenerator([ChatTurn("", [call]), ChatTurn("Sorry.")])
    _tool_service(sample_docs, generator).chat("Arsenal?")
    ((severity, attributes),) = events("assistant.tool")
    assert (severity, attributes["status"]) == ("WARNING", "error")
    assert attributes["error"] == "Unknown tool 'made_up_tool'."


def test_the_tool_round_limit_falls_back(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    call = ToolCall("predict_match", {"home_team": "Arsenal"})
    generator = ScriptedToolGenerator(
        [ChatTurn("", [call])] * 3 + [ChatTurn("Final answer.")]
    )
    _tool_service(sample_docs, generator).chat("Arsenal?")
    assert events("fallback") == [
        (
            "WARNING",
            {
                "from_path": "tool_calling",
                "to_path": "answer_without_tools",
                "cause": "tool_round_limit",
            },
        )
    ]
    assert _answer(events)["tool_rounds"] == 3


def test_router_reply_is_the_router_path(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    service = _routed_service(
        sample_docs, ScriptedToolGenerator([]), Route(reply="No.")
    )
    service.chat("Who is the top scorer?")
    attributes = _answer(events)
    assert (attributes["path"], attributes["model"]) == ("router", "router")
    assert (attributes["retrieved_count"], attributes["top_score"]) == (0, None)


def test_routed_tools_are_the_tools_path(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    generator = ScriptedToolGenerator([ChatTurn("Arsenal at 47.1%.")])
    route = Route(calls=[ToolCall("predict_match", {"home_team": "Arsenal"})])
    _routed_service(sample_docs, generator, route).chat("Arsenal next?")
    attributes = _answer(events)
    assert (attributes["path"], attributes["tool_rounds"]) == ("model_with_tools", 1)


def test_a_refusal_is_an_abstention(sample_docs, events: Events) -> None:  # type: ignore[no-untyped-def]
    answer = "I don't have enough information to answer that."
    _make_service(sample_docs, answer=answer).chat("Who won in 1888?")
    assert events("assistant.abstain") == [("INFO", {"reason": "model_declined"})]


def test_a_refusal_without_documents_is_no_retrieval(
    sample_docs: list[Document], events: Events, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("assistant.services.assistant_service.retrieve", lambda *_: [])
    answer = "I don't have enough information to answer that."
    _make_service(sample_docs, answer=answer).chat("Who won in 1888?")
    assert events("assistant.abstain") == [("INFO", {"reason": "no_retrieval"})]
    assert _answer(events)["retrieved_count"] == 0

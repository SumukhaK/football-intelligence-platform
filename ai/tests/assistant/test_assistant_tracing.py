"""Spans recorded while the assistant answers (telemetry contract section 4)."""

from __future__ import annotations

from typing import Any

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode

from assistant.generation.generator import ChatTurn, ToolCall
from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import VectorStore
from assistant.services.assistant_service import AssistantService
from assistant.tools.routing import Route
from assistant.tools.tool import Tool
from tests.assistant.conftest import VariedEmbedder

_CALL = ToolCall("predict_match", {"home_team": "Arsenal"})


class _Scripted:
    """Tool-calling fake that plays back turns, or fails when told to."""

    def __init__(self, turns: list[ChatTurn], error: Exception | None = None) -> None:
        self._turns = turns
        self._error = error

    def generate(self, messages: list[dict[str, str]]) -> str:
        raise AssertionError("Tool-calling generators are used through chat().")

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ChatTurn:
        if self._error is not None:
            raise self._error
        return self._turns.pop(0)


class _Router:
    def route(self, question: str) -> Route | None:
        return None


def _service(sample_docs: list[Document], generator: _Scripted) -> AssistantService:
    embedder = VariedEmbedder(dim=8)
    store = VectorStore()
    store.add(sample_docs, embedder.embed([d.text for d in sample_docs]))
    tool = Tool("predict_match", "Prediction.", {"type": "object"}, lambda a: {})
    return AssistantService(
        embedder=embedder,
        generator=generator,
        store=store,
        model_name="qwen2.5",
        top_k=2,
        tools=[tool],
        router=_Router(),
    )


def _by_name(spans: InMemorySpanExporter) -> dict[str, list[ReadableSpan]]:
    found: dict[str, list[ReadableSpan]] = {}
    for span in spans.get_finished_spans():
        found.setdefault(span.name, []).append(span)
    return found


def _parent_id(span: ReadableSpan) -> int | None:
    return span.parent.span_id if span.parent else None


def test_a_chat_with_one_tool_call_records_the_span_tree(
    sample_docs: list[Document], spans: InMemorySpanExporter
) -> None:
    turns = [ChatTurn("", [_CALL]), ChatTurn("Arsenal win.")]
    with trace.get_tracer("test").start_as_current_span("POST /assistant/chat"):
        _service(sample_docs, _Scripted(turns)).chat("Will Arsenal win?")

    found = _by_name(spans)
    (root,) = found["POST /assistant/chat"]
    (retrieve,) = found["assistant.retrieve"]
    (embed,) = found["assistant.embed"]
    (tool,) = found["assistant.tool.predict_match"]
    (route,) = found["assistant.route"]
    for child in [route, retrieve, tool, *found["assistant.generate"]]:
        assert _parent_id(child) == root.context.span_id
    assert _parent_id(embed) == retrieve.context.span_id
    assert retrieve.attributes == {"retrieved_count": 2}
    rounds = [s.attributes["round"] for s in found["assistant.generate"]]  # type: ignore[index]
    assert rounds == [1, 2]
    first_round = found["assistant.generate"][0]
    assert tool.start_time >= first_round.end_time  # type: ignore[operator]
    assert tool.status.status_code is StatusCode.UNSET


def test_a_failing_generator_is_recorded_on_its_span(
    sample_docs: list[Document], spans: InMemorySpanExporter
) -> None:
    service = _service(sample_docs, _Scripted([], ConnectionError("down")))
    with pytest.raises(ConnectionError):
        service.chat("Will Arsenal win?")

    (generate,) = _by_name(spans)["assistant.generate"]
    assert generate.status.status_code is StatusCode.ERROR
    assert [e.name for e in generate.events] == ["exception"]


def test_a_tool_error_marks_its_span(
    sample_docs: list[Document], spans: InMemorySpanExporter
) -> None:
    unknown = ToolCall("no_such_tool", {})
    turns = [ChatTurn("", [unknown]), ChatTurn("Sorry.")]
    _service(sample_docs, _Scripted(turns)).chat("Will Arsenal win?")

    (tool,) = _by_name(spans)["assistant.tool.no_such_tool"]
    assert tool.status.status_code is StatusCode.ERROR


def test_spans_never_carry_the_question(
    sample_docs: list[Document], spans: InMemorySpanExporter
) -> None:
    turns = [ChatTurn("", [_CALL]), ChatTurn("Arsenal win.")]
    _service(sample_docs, _Scripted(turns)).chat("Secret question text")

    for span in spans.get_finished_spans():
        values = [str(v) for v in (span.attributes or {}).values()]
        assert not any("Secret" in v for v in values)

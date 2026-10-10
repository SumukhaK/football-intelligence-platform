"""AssistantService — orchestrates the RAG pipeline end-to-end."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any, TypeVar

from opentelemetry.trace import StatusCode

from assistant.embeddings.embedder import Embedder
from assistant.generation.generator import Generator, ToolCall, ToolCallingGenerator
from assistant.prompting.templates import build_messages
from assistant.retrieval.retriever import RetrievedDoc, retrieve
from assistant.retrieval.vector_store import VectorStore
from assistant.tools.routing import Route, Router
from assistant.tools.tool import Tool, ToolResult, run_tool_checked
from shared.telemetry.events import EventName, emit
from shared.telemetry.tracing import tracer

logger = logging.getLogger(__name__)
_T = TypeVar("_T")


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
# A question needs one or two calls (prediction, then explanation); the cap
# stops a model that keeps calling tools from looping forever.
_MAX_TOOL_ROUNDS = 3


@dataclass
class _Turn:
    """What happened while answering one question, for its telemetry."""

    started: float
    rounds: int = 0
    tools_run: list[str] = field(default_factory=list)


class AssistantService:
    """Retrieval-augmented generation service for football questions.

    Composes: embed → retrieve → prompt → generate → structured response.
    When given tools and a tool-calling generator, the model may call them
    before answering, so its numbers come from the platform's own APIs.
    """

    def __init__(
        self,
        embedder: Embedder,
        generator: Generator,
        store: VectorStore,
        model_name: str,
        top_k: int = 5,
        tools: Sequence[Tool] = (),
        today: Callable[[], date] = date.today,
        router: Router | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Initialise with injected components, optional tools and a router."""
        self._embedder = embedder
        self._generator = generator
        self._store = store
        self._model_name = model_name
        self._top_k = top_k
        self._tools = tuple(tools)
        self._today = today
        self._router = router
        self._clock = clock

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

        turn = _Turn(self._clock())
        route = self._route(question)
        if route is not None and route.reply is not None:
            response = _routed_reply(route.reply)
            self._log_answer(question, response, [], turn, routed=True)
            return response
        # A routed question already has its data; documents would only distract.
        retrieved = self._retrieve(question) if route is None else []
        # Routed season questions need today's date to read their tool results;
        # on other questions it made the 7B model refuse documented answers.
        today = self._today() if route is not None else None
        messages: list[dict[str, Any]] = list(
            build_messages(question, retrieved, today=today)
        )
        if route is not None:
            self._run_calls(messages, route.calls, turn)
        response = self._response(self._answer(messages, turn), retrieved)
        self._log_answer(question, response, retrieved, turn, routed=False)
        return response

    def _log_answer(
        self,
        question: str,
        response: AssistantResponse,
        retrieved: list[RetrievedDoc],
        turn: _Turn,
        routed: bool,
    ) -> None:
        """Log ``assistant.answer``, and ``assistant.abstain`` for a refusal."""
        path = "router" if routed else "model"
        if turn.tools_run:
            path = "model_with_tools"
        emit(
            logger,
            EventName.ASSISTANT_ANSWER,
            f"Chat answered on the {path} path",
            path=path,
            question_chars=len(question),
            retrieved_count=len(retrieved),
            top_score=round(retrieved[0][1], 4) if retrieved else None,
            confidence=response.confidence,
            tool_rounds=turn.rounds,
            model=response.model,
            prompt_tokens=None,
            completion_tokens=None,
            cost_usd=None,
            duration_ms=round((self._clock() - turn.started) * 1000),
        )
        if _NO_INFO_MARKER in response.answer:
            reason = "model_declined" if retrieved or turn.rounds else "no_retrieval"
            emit(
                logger,
                EventName.ASSISTANT_ABSTAIN,
                "The answer says the assistant does not know",
                reason=reason,
            )

    def _response(
        self, answer: str, retrieved: list[RetrievedDoc]
    ) -> AssistantResponse:
        confidence = _compute_confidence(retrieved, answer)
        return AssistantResponse(
            answer=answer,
            sources=_build_sources(retrieved),
            confidence=confidence,
            model=self._model_name,
            retrieved_count=len(retrieved),
        )

    def _route(self, question: str) -> Route | None:
        """Ask the season router whether it answers ``question``, in a span."""
        if self._router is None:
            return None
        with tracer().start_as_current_span("assistant.route") as span:
            route = self._router.route(question)
            span.set_attribute("routed", route is not None)
            return route

    def _retrieve(self, question: str) -> list[RetrievedDoc]:
        with tracer().start_as_current_span("assistant.retrieve") as span:
            with tracer().start_as_current_span("assistant.embed"):
                query_emb = self._embedder.embed([question])[0]
            retrieved = retrieve(query_emb, self._store, self._top_k)
            span.set_attribute("retrieved_count", len(retrieved))
            return retrieved

    def _run_calls(
        self,
        messages: list[dict[str, Any]],
        calls: Sequence[ToolCall],
        turn: _Turn,
        content: str = "",
    ) -> None:
        """Run tool calls and append them and their results to ``messages``."""
        messages.append(_assistant_message(content, calls))
        turn.rounds += 1
        for call in calls:
            started = self._clock()
            result = self._run_tool(call)
            turn.tools_run.append(call.name)
            status = "error" if result.error else "ok"
            emit(
                logger,
                EventName.ASSISTANT_TOOL,
                f"Tool {call.name} finished: {status}",
                tool=call.name,
                status=status,
                duration_ms=round((self._clock() - started) * 1000),
                error=result.error,
            )
            messages.append(
                {"role": "tool", "tool_name": call.name, "content": result.content}
            )

    def _run_tool(self, call: ToolCall) -> ToolResult:
        """Run one tool call in its own span; a tool error marks the span."""
        with tracer().start_as_current_span(f"assistant.tool.{call.name}") as span:
            result = run_tool_checked(self._tools, call.name, call.arguments)
            span.set_attribute("tool", call.name)
            if result.error:
                span.set_status(StatusCode.ERROR)
            return result

    def _generate(self, round_: int, call: Callable[[], _T]) -> _T:
        """Make model call number ``round_`` of this answer, in a span."""
        with tracer().start_as_current_span("assistant.generate") as span:
            span.set_attribute("round", round_)
            span.set_attribute("model", self._model_name)
            return call()

    def _answer(self, messages: list[dict[str, Any]], turn: _Turn) -> str:
        """Generate the answer, running any tool calls the model makes first."""
        generator = self._generator
        if not self._tools or not isinstance(generator, ToolCallingGenerator):
            return self._generate(1, lambda: generator.generate(messages))
        schemas = [tool.schema() for tool in self._tools]
        for round_ in range(1, _MAX_TOOL_ROUNDS + 1):
            step = self._generate(round_, lambda: generator.chat(messages, schemas))
            if not step.tool_calls:
                return step.content
            self._run_calls(messages, step.tool_calls, turn, step.content)
        emit(
            logger,
            EventName.FALLBACK,
            "Tool round limit reached; answering without tools",
            from_path="tool_calling",
            to_path="answer_without_tools",
            cause="tool_round_limit",
        )
        final = _MAX_TOOL_ROUNDS + 1
        return self._generate(final, lambda: generator.chat(messages, [])).content


class VectorStoreEmptyError(RuntimeError):
    """Raised when the vector store has not been populated."""


def _routed_reply(reply: str) -> AssistantResponse:
    """A fixed reply chosen by the router; no model or retrieval was used."""
    return AssistantResponse(
        answer=reply, sources=[], confidence=0.0, model="router", retrieved_count=0
    )


def _assistant_message(content: str, calls: Sequence[Any]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {"function": {"name": c.name, "arguments": c.arguments}} for c in calls
        ],
    }


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

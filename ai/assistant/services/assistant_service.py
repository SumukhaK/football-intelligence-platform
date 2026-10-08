"""AssistantService — orchestrates the RAG pipeline end-to-end."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from assistant.embeddings.embedder import Embedder
from assistant.generation.generator import Generator, ToolCall, ToolCallingGenerator
from assistant.prompting.templates import build_messages
from assistant.retrieval.retriever import RetrievedDoc, retrieve
from assistant.retrieval.vector_store import VectorStore
from assistant.tools.routing import Router
from assistant.tools.tool import Tool, run_tool

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
# A question needs one or two calls (prediction, then explanation); the cap
# stops a model that keeps calling tools from looping forever.
_MAX_TOOL_ROUNDS = 3


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

        route = self._router.route(question) if self._router else None
        if route is not None and route.reply is not None:
            return _routed_reply(route.reply)
        # A routed question already has its data; documents would only distract.
        retrieved = self._retrieve(question) if route is None else []
        messages: list[dict[str, Any]] = list(
            build_messages(question, retrieved, today=self._today())
        )
        if route is not None:
            self._run_calls(messages, route.calls)
        answer = self._answer(messages)

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

    def _retrieve(self, question: str) -> list[RetrievedDoc]:
        query_emb = self._embedder.embed([question])[0]
        return retrieve(query_emb, self._store, self._top_k)

    def _run_calls(
        self,
        messages: list[dict[str, Any]],
        calls: Sequence[ToolCall],
        content: str = "",
    ) -> None:
        """Run tool calls and append them and their results to ``messages``."""
        messages.append(_assistant_message(content, calls))
        for call in calls:
            logger.info("Tool call: %s %s", call.name, call.arguments)
            result = run_tool(self._tools, call.name, call.arguments)
            messages.append({"role": "tool", "tool_name": call.name, "content": result})

    def _answer(self, messages: list[dict[str, Any]]) -> str:
        """Generate the answer, running any tool calls the model makes first."""
        generator = self._generator
        if not self._tools or not isinstance(generator, ToolCallingGenerator):
            return generator.generate(messages)
        schemas = [tool.schema() for tool in self._tools]
        for _ in range(_MAX_TOOL_ROUNDS):
            turn = generator.chat(messages, schemas)
            if not turn.tool_calls:
                return turn.content
            self._run_calls(messages, turn.tool_calls, turn.content)
        return generator.chat(messages, []).content


class VectorStoreEmptyError(RuntimeError):
    """Raised when the vector store has not been populated."""


def _routed_reply(reply: str) -> AssistantResponse:
    """A fixed reply chosen by the router; no model or retrieval was used."""
    logger.info("Chat: answered by the router without the model.")
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

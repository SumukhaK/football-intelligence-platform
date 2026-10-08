"""Deterministic routing in front of the chat model (ADR 021).

Small models often skip a tool they should call. A router reads the question
first: it can answer outright with a fixed reply (no model call at all), or
name the tool calls to run before the model writes the answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from assistant.generation.generator import ToolCall


@dataclass(frozen=True)
class Route:
    """What the router decided for one question."""

    calls: list[ToolCall] = field(default_factory=list)
    reply: str | None = None


class Router(Protocol):
    """Decides, without a model, how a question should be handled."""

    def route(self, question: str) -> Route | None:
        """Return a route, or None to let the model handle the question."""
        ...

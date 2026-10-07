"""Generator protocol and Ollama implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Generator(Protocol):
    """Generates text from a system prompt and a user message."""

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Return the model's response string."""
        ...


@dataclass(frozen=True)
class ToolCall:
    """One function call the chat model asked for."""

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ChatTurn:
    """The model's reply: text, or the tool calls it wants run first."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)


@runtime_checkable
class ToolCallingGenerator(Protocol):
    """A generator that can also offer the model tools to call."""

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ChatTurn:
        """Return the model's turn, which may request tool calls."""
        ...


class OllamaGenerator:
    """Generates responses using the Ollama chat API.

    Requires a running Ollama server with the configured model pulled.
    Raises :class:`OllamaGenerationError` on connection or API errors.
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> None:
        """Initialise with model name, Ollama URL, and generation options."""
        self._model = model
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Send messages to Ollama chat and return the response content."""
        return self.chat(messages, tools=[]).content

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ChatTurn:
        """Send messages and tool schemas to Ollama chat and return its turn."""
        try:
            import ollama  # noqa: PLC0415  # type: ignore[import-untyped,no-redef]

            client = ollama.Client(host=self._base_url)
            response = client.chat(
                model=self._model,
                messages=messages,
                tools=tools or None,
                options={
                    "temperature": self._temperature,
                    "num_predict": self._max_tokens,
                },
            )
        except Exception as exc:
            raise OllamaGenerationError(
                f"Ollama generation failed (model={self._model}): {exc}"
            ) from exc
        message = response.message
        calls = [
            ToolCall(call.function.name, dict(call.function.arguments))
            for call in message.tool_calls or []
        ]
        return ChatTurn(content=str(message.content or ""), tool_calls=calls)


class OllamaGenerationError(RuntimeError):
    """Raised when the Ollama server returns an error during generation."""

"""Generator protocol and Ollama implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Generator(Protocol):
    """Generates text from a system prompt and a user message."""

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Return the model's response string."""
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
        try:
            import ollama  # noqa: PLC0415  # type: ignore[import-untyped,no-redef]

            client = ollama.Client(host=self._base_url)
            response = client.chat(
                model=self._model,
                messages=messages,
                options={
                    "temperature": self._temperature,
                    "num_predict": self._max_tokens,
                },
            )
            return str(response.message.content)
        except Exception as exc:
            raise OllamaGenerationError(
                f"Ollama generation failed (model={self._model}): {exc}"
            ) from exc


class OllamaGenerationError(RuntimeError):
    """Raised when the Ollama server returns an error during generation."""

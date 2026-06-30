"""Embedder protocol and Ollama implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Embedder(Protocol):
    """Converts a list of text strings to a 2-D embedding matrix."""

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an (n_texts, embed_dim) float32 ndarray."""
        ...


class OllamaEmbedder:
    """Embeds text using the Ollama local embedding API.

    Requires a running Ollama server with the configured model pulled.
    Raises :class:`OllamaUnavailableError` when the server is not reachable.
    """

    def __init__(self, model: str, base_url: str) -> None:
        """Initialise with model name and Ollama base URL."""
        self._model = model
        self._base_url = base_url

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an (n, embed_dim) float32 array for the given texts."""
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        try:
            import ollama  # noqa: PLC0415  # type: ignore[import-untyped,no-redef]

            client = ollama.Client(host=self._base_url)
            response = client.embed(model=self._model, input=texts)
            vectors = [list(v) for v in response.embeddings]
            return np.array(vectors, dtype=np.float32)
        except Exception as exc:
            raise OllamaUnavailableError(
                f"Ollama embed failed (model={self._model}, "
                f"url={self._base_url}): {exc}"
            ) from exc


class OllamaUnavailableError(RuntimeError):
    """Raised when the Ollama server cannot be reached or returns an error."""

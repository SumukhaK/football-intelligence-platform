"""Tests for assistant.embeddings.embedder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from assistant.embeddings.embedder import OllamaEmbedder, OllamaUnavailableError


def _make_embed_response(n: int, dim: int = 8) -> MagicMock:
    """Return a fake EmbedResponse with n embeddings of given dim."""
    resp = MagicMock()
    resp.embeddings = [[float(j) for j in range(dim)] for _ in range(n)]
    return resp


def test_embedder_returns_correct_shape() -> None:
    """OllamaEmbedder returns (n, dim) array matching the response."""
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.embed.return_value = _make_embed_response(n=3, dim=8)

        embedder = OllamaEmbedder(model="nomic-embed-text", base_url="http://x:11434")
        result = embedder.embed(["a", "b", "c"])

    assert result.shape == (3, 8)
    assert result.dtype == np.float32


def test_embedder_empty_input_returns_empty() -> None:
    """embed([]) returns an empty array without calling Ollama."""
    with patch("ollama.Client"):
        embedder = OllamaEmbedder(model="m", base_url="http://x:11434")
        result = embedder.embed([])

    assert result.shape[0] == 0


def test_embedder_wraps_connection_error() -> None:
    """OllamaUnavailableError is raised when the client raises."""
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.embed.side_effect = ConnectionError("refused")

        embedder = OllamaEmbedder(model="m", base_url="http://x:11434")
        with pytest.raises(OllamaUnavailableError, match="refused"):
            embedder.embed(["some text"])

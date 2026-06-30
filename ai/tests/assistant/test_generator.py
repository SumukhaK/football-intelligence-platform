"""Tests for assistant.generation.generator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from assistant.generation.generator import OllamaGenerationError, OllamaGenerator


def _make_chat_response(content: str) -> MagicMock:
    resp = MagicMock()
    resp.message = MagicMock()
    resp.message.content = content
    return resp


def test_generator_returns_model_content() -> None:
    """OllamaGenerator extracts response content correctly."""
    with patch("ollama.Client") as mock_cls:
        client = mock_cls.return_value
        client.chat.return_value = _make_chat_response("Predicted: Home win.")

        gen = OllamaGenerator(
            model="llama3.2", base_url="http://x:11434", temperature=0.1
        )
        answer = gen.generate([{"role": "user", "content": "Who will win?"}])

    assert answer == "Predicted: Home win."


def test_generator_wraps_connection_error() -> None:
    """OllamaGenerationError is raised when the client raises."""
    with patch("ollama.Client") as mock_cls:
        client = mock_cls.return_value
        client.chat.side_effect = ConnectionError("refused")

        gen = OllamaGenerator(model="m", base_url="http://x:11434")
        with pytest.raises(OllamaGenerationError, match="refused"):
            gen.generate([{"role": "user", "content": "Q"}])


def test_generator_passes_options() -> None:
    """OllamaGenerator passes temperature and num_predict to client.chat."""
    with patch("ollama.Client") as mock_cls:
        client = mock_cls.return_value
        client.chat.return_value = _make_chat_response("ok")

        gen = OllamaGenerator(
            model="m", base_url="http://x:11434", temperature=0.5, max_tokens=512
        )
        gen.generate([{"role": "user", "content": "Q"}])

        _, kwargs = client.chat.call_args
        assert kwargs.get("options", {}).get("temperature") == 0.5
        assert kwargs.get("options", {}).get("num_predict") == 512

"""Tests for assistant.generation.generator."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from assistant.generation.generator import (
    OllamaGenerationError,
    OllamaGenerator,
    ToolCall,
)


def _make_chat_response(content: str, tool_calls: list[Any] | None = None) -> MagicMock:
    resp = MagicMock()
    resp.message = MagicMock()
    resp.message.content = content
    resp.message.tool_calls = tool_calls
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


def test_chat_passes_tools_and_parses_tool_calls() -> None:
    """chat() offers the tool schemas and returns the calls the model makes."""
    call = MagicMock()
    call.function.name = "predict_match"
    call.function.arguments = {"home_team": "Arsenal", "away_team": "Chelsea"}
    tools = [{"type": "function", "function": {"name": "predict_match"}}]
    with patch("ollama.Client") as mock_cls:
        client = mock_cls.return_value
        client.chat.return_value = _make_chat_response("", [call])

        turn = OllamaGenerator(model="m", base_url="http://x:11434").chat(
            [{"role": "user", "content": "Q"}], tools
        )

        assert client.chat.call_args.kwargs["tools"] == tools
    assert turn.content == ""
    assert turn.tool_calls == [
        ToolCall("predict_match", {"home_team": "Arsenal", "away_team": "Chelsea"})
    ]


def test_generate_offers_no_tools() -> None:
    """generate() keeps the plain chat call, without a tools list."""
    with patch("ollama.Client") as mock_cls:
        client = mock_cls.return_value
        client.chat.return_value = _make_chat_response("ok")

        OllamaGenerator(model="m", base_url="http://x:11434").generate(
            [{"role": "user", "content": "Q"}]
        )

        assert client.chat.call_args.kwargs["tools"] is None

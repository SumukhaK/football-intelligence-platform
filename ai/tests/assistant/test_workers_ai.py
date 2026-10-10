"""Tests for the Workers AI embedder and generator, with no network."""

from __future__ import annotations

import json
from typing import Any

import httpx
import numpy as np
import pytest

from assistant.generation.generator import ToolCall
from assistant.workers_ai import (
    WorkersAIClient,
    WorkersAIEmbedder,
    WorkersAIError,
    WorkersAIGenerator,
    parse_turn,
    to_openai_messages,
)

URL = "https://api.cloudflare.com/client/v4/accounts/acc/ai/v1"


class FakePost:
    """Plays back responses and records each request."""

    def __init__(self, *replies: httpx.Response | Exception) -> None:
        self._replies = list(replies)
        self.requests: list[dict[str, Any]] = []

    def __call__(self, url: str, **kwargs: Any) -> httpx.Response:
        self.requests.append({"url": url, **kwargs})
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        reply.request = httpx.Request("POST", url)
        return reply


def _client(post: FakePost) -> WorkersAIClient:
    return WorkersAIClient("acc", "secret-token", 5.0, post=post, sleep=lambda _: None)


def _completion(
    message: dict[str, Any], usage: dict[str, Any] | None = None
) -> httpx.Response:
    body = {"choices": [{"message": message}], "usage": usage or {}}
    return httpx.Response(200, json=body)


def test_embed_posts_texts_and_orders_rows_by_index() -> None:
    post = FakePost(
        httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.0, 1.0]},
                    {"index": 0, "embedding": [1.0, 0.0]},
                ]
            },
        )
    )
    vectors = WorkersAIEmbedder(_client(post), "@cf/emb").embed(["a", "b"])
    assert vectors.dtype == np.float32
    assert vectors.tolist() == [[1.0, 0.0], [0.0, 1.0]]
    request = post.requests[0]
    assert request["url"] == f"{URL}/embeddings"
    assert request["json"] == {"model": "@cf/emb", "input": ["a", "b"]}
    assert request["headers"] == {"Authorization": "Bearer secret-token"}
    assert request["timeout"] == 5.0


def test_embed_nothing_makes_no_call() -> None:
    post = FakePost()
    assert WorkersAIEmbedder(_client(post), "@cf/emb").embed([]).shape == (0, 0)
    assert post.requests == []


def test_chat_offers_tools_and_reads_tool_calls() -> None:
    call = {
        "id": "c1",
        "type": "function",
        "function": {"name": "predict_match", "arguments": '{"home_team": "Arsenal"}'},
    }
    post = FakePost(_completion({"content": None, "tool_calls": [call]}))
    tools = [{"type": "function", "function": {"name": "predict_match"}}]
    turn = WorkersAIGenerator(_client(post), "@cf/chat").chat(
        [{"role": "user", "content": "Arsenal?"}], tools
    )
    assert turn.content == ""
    assert turn.tool_calls == [ToolCall("predict_match", {"home_team": "Arsenal"})]
    body = post.requests[0]["json"]
    assert post.requests[0]["url"] == f"{URL}/chat/completions"
    assert body["tools"] == tools
    assert body["model"] == "@cf/chat"


def test_generate_offers_no_tools() -> None:
    post = FakePost(_completion({"content": "Hello."}))
    answer = WorkersAIGenerator(_client(post), "@cf/chat").generate(
        [{"role": "user", "content": "Hi"}]
    )
    assert answer == "Hello."
    assert "tools" not in post.requests[0]["json"]


def test_usage_and_cost_are_read_from_the_reply() -> None:
    turn = parse_turn(
        {
            "choices": [{"message": {"content": "x"}}],
            "usage": {"prompt_tokens": 171, "completion_tokens": 25, "neurons": 1000.0},
        }
    )
    assert (turn.prompt_tokens, turn.completion_tokens) == (171, 25)
    assert turn.cost_usd == pytest.approx(0.011)


def test_missing_usage_stays_unreported() -> None:
    turn = parse_turn({"choices": [{"message": {"content": "x"}}]})
    assert (turn.prompt_tokens, turn.completion_tokens, turn.cost_usd) == (
        None,
        None,
        None,
    )


def test_reply_without_a_message_is_an_error() -> None:
    with pytest.raises(WorkersAIError):
        parse_turn({"choices": []})


def test_unreadable_tool_arguments_become_empty() -> None:
    call = {"function": {"name": "predict_match", "arguments": "{not json"}}
    turn = parse_turn({"choices": [{"message": {"tool_calls": [call]}}]})
    assert turn.tool_calls == [ToolCall("predict_match", {})]


def test_tool_results_are_paired_with_their_calls() -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "q"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"function": {"name": "a", "arguments": {"x": 1}}},
                {"function": {"name": "b", "arguments": {}}},
            ],
        },
        {"role": "tool", "tool_name": "a", "content": "ra"},
        {"role": "tool", "tool_name": "b", "content": "rb"},
    ]
    out = to_openai_messages(messages)
    calls = out[2]["tool_calls"]
    assert [c["function"]["name"] for c in calls] == ["a", "b"]
    assert json.loads(calls[0]["function"]["arguments"]) == {"x": 1}
    assert out[2]["content"] == ""
    assert [m["tool_call_id"] for m in out[3:]] == [calls[0]["id"], calls[1]["id"]]
    assert calls[0]["id"] != calls[1]["id"]
    assert out[:2] == [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "q"},
    ]


def test_a_server_error_is_retried_once() -> None:
    post = FakePost(httpx.Response(503), _completion({"content": "ok"}))
    assert WorkersAIGenerator(_client(post), "@cf/chat").generate([]) == "ok"
    assert len(post.requests) == 2


def test_quota_exhausted_after_the_retry_raises() -> None:
    post = FakePost(
        httpx.Response(429, headers={"Retry-After": "1"}), httpx.Response(429)
    )
    with pytest.raises(WorkersAIError, match="HTTP 429"):
        WorkersAIGenerator(_client(post), "@cf/chat").generate([])
    assert len(post.requests) == 2


def test_a_client_error_is_not_retried() -> None:
    post = FakePost(httpx.Response(401))
    with pytest.raises(WorkersAIError, match="HTTP 401"):
        WorkersAIEmbedder(_client(post), "@cf/emb").embed(["a"])
    assert len(post.requests) == 1


def test_a_timeout_never_leaks_the_token() -> None:
    post = FakePost(httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow"))
    with pytest.raises(WorkersAIError) as caught:
        WorkersAIEmbedder(_client(post), "@cf/emb").embed(["a"])
    assert "secret-token" not in str(caught.value)
    assert "ReadTimeout" in str(caught.value)

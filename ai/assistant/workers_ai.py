"""Cloudflare Workers AI embedder and generator (ADR 025).

Both talk to Workers AI's OpenAI-compatible REST endpoints. The assistant
builds its messages in Ollama's shape, so the generator translates tool calls
and tool results on the way out and back. Every call has a deadline and is
retried at most once on a timeout, a connection error, a 429 or a 5xx.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

import httpx
import numpy as np

from assistant.generation.generator import ChatTurn, ToolCall
from shared.telemetry.retry import RetryPolicy, call_with_retry, classify_httpx_error

API_ROOT = "https://api.cloudflare.com/client/v4/accounts"
# One retry, and never a long wait: the user is waiting for the answer.
RETRY_POLICY = RetryPolicy(max_attempts=2, base_delay_s=0.5, max_delay_s=2.0)
# Workers AI bills neurons beyond the free daily allowance at this price.
USD_PER_1K_NEURONS = 0.011

Post = Callable[..., httpx.Response]


class WorkersAIError(RuntimeError):
    """Raised when Workers AI cannot answer: quota, deadline or server error."""


class WorkersAIClient:
    """Posts JSON to one account's OpenAI-compatible Workers AI endpoints."""

    def __init__(
        self,
        account_id: str,
        api_token: str,
        timeout_s: float,
        post: Post = httpx.post,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Bind the account, its token, the per-attempt deadline and transport."""
        self._base = f"{API_ROOT}/{account_id}/ai/v1"
        self._headers = {"Authorization": f"Bearer {api_token}"}
        self._timeout_s = timeout_s
        self._post = post
        self._sleep = sleep

    def post(self, path: str, body: dict[str, Any]) -> Any:
        """POST ``body`` to ``path`` and return the decoded JSON reply."""

        def send() -> Any:
            response = self._post(
                f"{self._base}/{path}",
                json=body,
                headers=self._headers,
                timeout=self._timeout_s,
            )
            response.raise_for_status()
            return response.json()

        try:
            return call_with_retry(
                send,
                dependency="workers_ai",
                operation=path,
                policy=RETRY_POLICY,
                classify=classify_httpx_error,
                sleep=self._sleep,
            )
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            raise WorkersAIError(f"Workers AI answered HTTP {code}") from exc
        except httpx.HTTPError as exc:
            raise WorkersAIError(
                f"Workers AI unreachable: {type(exc).__name__}"
            ) from exc


class WorkersAIEmbedder:
    """Embeds text with a Workers AI embedding model."""

    def __init__(self, client: WorkersAIClient, model: str) -> None:
        """Use ``model`` through ``client``."""
        self._client = client
        self._model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an (n, embed_dim) float32 array for the given texts."""
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        reply = self._client.post("embeddings", {"model": self._model, "input": texts})
        rows = sorted(reply["data"], key=lambda row: row["index"])
        return np.array([row["embedding"] for row in rows], dtype=np.float32)


class WorkersAIGenerator:
    """Chats with a Workers AI model that supports function calling (ADR 018)."""

    def __init__(
        self,
        client: WorkersAIClient,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> None:
        """Use ``model`` through ``client`` with these generation options."""
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, messages: list[dict[str, str]]) -> str:
        """Return the model's answer to ``messages``, offering no tools."""
        return self.chat(messages, tools=[]).content

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> ChatTurn:
        """Return the model's turn, which may request tool calls."""
        body: dict[str, Any] = {
            "model": self._model,
            "messages": to_openai_messages(messages),
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if tools:
            body["tools"] = tools
        reply = self._client.post("chat/completions", body)
        return parse_turn(reply)


def to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate Ollama-shaped messages into the OpenAI chat format.

    OpenAI pairs each tool result with its call by ID, and wants arguments as
    a JSON string. The assistant runs calls in order, so each tool message
    answers the next unanswered call of the assistant message before it.
    """
    out: list[dict[str, Any]] = []
    pending: list[str] = []
    for message in messages:
        if message.get("role") == "assistant" and message.get("tool_calls"):
            calls = [
                _openai_call(i, len(out), c)
                for i, c in enumerate(message["tool_calls"])
            ]
            pending = [call["id"] for call in calls]
            out.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": calls,
                }
            )
        elif message.get("role") == "tool":
            call_id = pending.pop(0) if pending else "call_unmatched"
            out.append(
                {"role": "tool", "tool_call_id": call_id, "content": message["content"]}
            )
        else:
            out.append({"role": message["role"], "content": message["content"]})
    return out


def _openai_call(index: int, position: int, call: dict[str, Any]) -> dict[str, Any]:
    function = call["function"]
    return {
        "id": f"call_{position}_{index}",
        "type": "function",
        "function": {
            "name": function["name"],
            "arguments": json.dumps(function.get("arguments") or {}),
        },
    }


def parse_turn(reply: dict[str, Any]) -> ChatTurn:
    """Read the model's turn and its token usage from a chat completion."""
    try:
        message = reply["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise WorkersAIError("Workers AI returned no message") from exc
    calls = [_tool_call(call) for call in message.get("tool_calls") or []]
    usage = reply.get("usage") or {}
    neurons = usage.get("neurons")
    return ChatTurn(
        content=str(message.get("content") or "").strip(),
        tool_calls=calls,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        cost_usd=None if neurons is None else neurons * USD_PER_1K_NEURONS / 1000,
    )


def _tool_call(call: dict[str, Any]) -> ToolCall:
    function = call["function"]
    raw = function.get("arguments") or {}
    try:
        arguments = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        # The tool rejects the empty arguments and the model sees why.
        arguments = {}
    return ToolCall(function["name"], arguments if isinstance(arguments, dict) else {})

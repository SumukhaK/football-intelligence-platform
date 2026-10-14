"""Signed, trimmed chat history from the app (ADR 030)."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence
from dataclasses import dataclass

from backend.app.schemas.assistant import HistoryTurn

MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_TOKENS = 1200
MAX_ANSWER_CHARS = 1500
# A rough count that needs no tokenizer; it only has to bound the cost.
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class CheckedHistory:
    """The history the model may see, and why any of it was left out."""

    messages: list[dict[str, str]]
    dropped: bool = False
    trimmed: bool = False

    @property
    def user_questions(self) -> list[str]:
        """The user's earlier questions, oldest first."""
        return [m["content"] for m in self.messages if m["role"] == "user"]


class ChatHistory:
    """Signs answers and checks the history the app sends back."""

    def __init__(self, key: str) -> None:
        """Use ``key`` (``HISTORY_KEY``) for every signature."""
        self._key = key.encode()

    def sign(self, user: str, conversation_id: str, answer: str) -> str:
        """The HMAC-SHA256 of ``answer`` for this user and conversation."""
        message = "\x1f".join([user, conversation_id, answer]).encode()
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()

    def check(
        self, user: str, conversation_id: str | None, turns: Sequence[HistoryTurn]
    ) -> CheckedHistory:
        """Keep ``turns`` only if every answer in them is one we signed.

        A bad or missing signature drops the whole history, since the model
        would otherwise read words the server never said.
        """
        if not turns:
            return CheckedHistory([])
        if conversation_id is None or not all(
            turn.role == "user" or self._signed(user, conversation_id, turn)
            for turn in turns
        ):
            return CheckedHistory([], dropped=True)
        messages = [
            {"role": t.role, "content": t.content[:MAX_ANSWER_CHARS]} for t in turns
        ]
        kept = trim(messages)
        return CheckedHistory(kept, trimmed=len(kept) < len(messages))

    def _signed(self, user: str, conversation_id: str, turn: HistoryTurn) -> bool:
        expected = self.sign(user, conversation_id, turn.content)
        return turn.signature is not None and hmac.compare_digest(
            expected, turn.signature
        )


def trim(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """The newest messages within the turn and token caps, oldest dropped first.

    The kept history always starts with a user turn, so the model never sees
    an answer without the question it answered.
    """
    kept = messages[-MAX_HISTORY_MESSAGES:]
    while kept and (
        sum(len(m["content"]) for m in kept) > MAX_HISTORY_TOKENS * CHARS_PER_TOKEN
        or kept[0]["role"] != "user"
    ):
        kept = kept[1:]
    return kept

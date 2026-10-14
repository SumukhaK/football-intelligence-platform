"""Request and response schemas for the assistant chat endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# A football question fits easily; longer input only costs model tokens.
MAX_MESSAGE_CHARS = 1000
# The app keeps the last 4 exchanges (ADR 030); longer answers are cut.
MAX_HISTORY_ITEMS = 8
MAX_HISTORY_ITEM_CHARS = 1500


class HistoryTurn(BaseModel):
    """One earlier message of the chat, as the app kept it (ADR 030)."""

    role: Literal["user", "assistant"] = Field(
        ..., description="Who wrote it: the user or the assistant."
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=MAX_HISTORY_ITEM_CHARS,
        description="The message as shown in the app.",
    )
    signature: str | None = Field(
        default=None,
        pattern="^[0-9a-f]{64}$",
        description="The signature the server sent with this answer; "
        "required on assistant turns.",
    )


class ChatRequest(BaseModel):
    """Input for POST /assistant/chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_CHARS,
        description="The user's question or message to the assistant.",
        examples=["What was the model's test accuracy?"],
    )
    conversation_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=64,
        pattern="^[A-Za-z0-9_-]+$",
        description="The app's ID for this chat; needed when history is sent.",
    )
    history: list[HistoryTurn] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_ITEMS,
        description="Earlier messages of this chat, oldest first (ADR 030). "
        "Answers without a valid signature drop the whole history.",
    )


class SourceCitation(BaseModel):
    """A single retrieved document that contributed to the answer."""

    source: str = Field(..., description="Filename or path of the source document.")
    excerpt: str = Field(..., description="Short excerpt from the source text.")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Cosine similarity score in [0, 1]."
    )


class ChatResponse(BaseModel):
    """Response body for POST /assistant/chat."""

    answer: str = Field(..., description="The assistant's grounded answer.")
    sources: list[SourceCitation] = Field(
        ..., description="Retrieved documents that informed the answer."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Proxy confidence based on retrieval score."
    )
    model: str = Field(
        ...,
        description=(
            "Chat model that wrote the answer, 'router', or 'safety' for a "
            "refused question."
        ),
    )
    retrieved_count: int = Field(
        ..., ge=0, description="Number of document chunks retrieved."
    )
    signature: str | None = Field(
        default=None,
        description="Signature to send back with this answer in the history "
        "(ADR 030); null when no conversation_id was sent.",
    )

"""Request and response schemas for the assistant chat endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Input for POST /assistant/chat."""

    message: str = Field(
        ...,
        min_length=1,
        description="The user's question or message to the assistant.",
        examples=["What was the model's test accuracy?"],
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
    model: str = Field(..., description="Ollama model used for generation.")
    retrieved_count: int = Field(
        ..., ge=0, description="Number of document chunks retrieved."
    )

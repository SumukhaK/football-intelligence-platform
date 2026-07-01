"""ChatService — bridges API requests to the AI AssistantService."""

from __future__ import annotations

from backend.app.exceptions import AssistantNotAvailableError
from backend.app.schemas.assistant import ChatRequest, ChatResponse, SourceCitation


class ChatService:
    """Wraps the AI AssistantService for use in FastAPI route handlers."""

    def __init__(self, assistant_service: object) -> None:
        """Initialise with an AI-layer AssistantService instance."""
        self._service = assistant_service

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Answer the user's question and return a structured response.

        Raises:
            :class:`AssistantNotAvailableError`: When the underlying service
                raises a runtime error (Ollama down, empty index, etc.).
        """
        try:
            result = self._service.chat(request.message)  # type: ignore[attr-defined]
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            raise AssistantNotAvailableError(str(exc)) from exc

        sources = [
            SourceCitation(
                source=s.source,
                excerpt=s.excerpt,
                relevance_score=s.relevance_score,
            )
            for s in result.sources
        ]
        return ChatResponse(
            answer=result.answer,
            sources=sources,
            confidence=result.confidence,
            model=result.model,
            retrieved_count=result.retrieved_count,
        )

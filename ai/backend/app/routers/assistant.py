"""Router for POST /assistant/chat."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.exceptions import AssistantNotAvailableError
from backend.app.schemas.assistant import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService

router = APIRouter(tags=["Assistant"])


def _get_chat_service(request: Request) -> ChatService:
    """Read the ChatService from app.state; raise 503 if not loaded."""
    service: ChatService | None = getattr(request.app.state, "chat_service", None)
    if service is None:
        raise AssistantNotAvailableError(
            "Assistant service is not available. "
            "Ensure Ollama is running and the index has been built.",
            component="assistant",
        )
    return service


@router.post(
    "/assistant/chat",
    response_model=ChatResponse,
    summary="Chat with the Football Intelligence Assistant",
    description=(
        "Send a question to the RAG-powered Football Intelligence Assistant. "
        "Answers are grounded in local knowledge sources (model cards, "
        "evaluation reports, SHAP summaries, ADRs). "
        "The assistant never invents facts beyond the retrieved context."
    ),
)
def chat(
    request_body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """Answer a football intelligence question using RAG.

    A plain ``def`` so FastAPI runs the blocking model call in its thread pool,
    and the question is never logged (users opt in to storing it, ADR 022).
    """
    service = _get_chat_service(request)
    return service.chat(request_body)

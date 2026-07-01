"""Router for POST /assistant/chat."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from backend.app.exceptions import AssistantNotAvailableError
from backend.app.schemas.assistant import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Assistant"])


def _get_chat_service(request: Request) -> ChatService:
    """Read the ChatService from app.state; raise 503 if not loaded."""
    service: ChatService | None = getattr(request.app.state, "chat_service", None)
    if service is None:
        raise AssistantNotAvailableError(
            "Assistant service is not available. "
            "Ensure Ollama is running and the index has been built."
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
async def chat(
    request_body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """Answer a football intelligence question using RAG."""
    service = _get_chat_service(request)
    logger.info("Assistant chat: message=%r", request_body.message[:80])
    return service.chat(request_body)

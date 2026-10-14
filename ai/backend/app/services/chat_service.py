"""ChatService — bridges API requests to the AI AssistantService."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from assistant.prompting.templates import strip_citations
from backend.app.exceptions import AssistantNotAvailableError
from backend.app.schemas.assistant import ChatRequest, ChatResponse
from backend.app.services.account_service import MAX_STRIKES, AccountService
from backend.app.services.account_store import User
from shared.telemetry.events import EventName, emit

if TYPE_CHECKING:
    from assistant.safety import SafetyCheck

logger = logging.getLogger(__name__)


class ChatService:
    """Wraps the AI AssistantService for use in FastAPI route handlers."""

    def __init__(
        self,
        assistant_service: object,
        safety: SafetyCheck | None = None,
        accounts: AccountService | None = None,
    ) -> None:
        """Initialise with the AI service, and the safety check and accounts.

        With ``safety``, each question is checked first, and a harmful one
        adds a strike to the signed-in user through ``accounts`` (ADR 027).
        """
        self._service = assistant_service
        self._safety = safety
        self._accounts = accounts

    def chat(self, request: ChatRequest, user: User | None = None) -> ChatResponse:
        """Answer the user's question and return a structured response.

        Raises:
            :class:`AssistantNotAvailableError`: When the underlying service
                raises a runtime error (provider down, empty index, etc.).
        """
        try:
            harmful = (
                self._safety.harmful_categories(request.message) if self._safety else []
            )
            if harmful:
                return self._refuse(harmful, user)
            result = self._service.chat(request.message)  # type: ignore[attr-defined]
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            raise AssistantNotAvailableError(str(exc)) from exc

        # Sources and citations go to the logs (assistant.answer), not to
        # users (ADR 029).
        return ChatResponse(
            answer=strip_citations(result.answer),
            sources=[],
            confidence=result.confidence,
            model=result.model,
            retrieved_count=result.retrieved_count,
        )

    def _refuse(self, categories: list[str], user: User | None) -> ChatResponse:
        """A fixed refusal; the user's strike count goes up when signed in."""
        answer = "I can't help with that question."
        outcome = "refused"
        if user is not None and self._accounts is not None:
            user = self._accounts.add_strike(user.email)
            outcome = "banned" if user.status == "banned" else "strike"
            answer = _strike_message(user.strikes)
        emit(
            logger,
            EventName.GUARDRAIL_EVENT,
            f"Safety check blocked a question: {outcome}",
            kind="safety",
            outcome=outcome,
            categories=categories,
        )
        return ChatResponse(
            answer=answer, sources=[], confidence=0.0, model="safety", retrieved_count=0
        )


def _strike_message(strikes: int) -> str:
    if strikes >= MAX_STRIKES:
        return (
            "I can't help with that question. That was your last strike, so "
            "this account is now blocked."
        )
    return (
        "I can't help with that question. Questions meant to harm or abuse "
        f"count as strikes, and {MAX_STRIKES} strikes block the account. "
        f"Strikes so far: {strikes} of {MAX_STRIKES}."
    )

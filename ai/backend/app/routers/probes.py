"""Liveness and readiness probes for the hosting platform (ADR 025)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.app.middleware.request_context import record_error_code
from backend.app.schemas.common import ErrorResponse, LiveResponse, ReadyResponse
from backend.app.services.readiness import missing_components

router = APIRouter(tags=["Health"])
NOT_READY = "Not ready"


@router.get(
    "/live",
    response_model=LiveResponse,
    summary="Liveness probe",
    description=(
        "Answers 200 while the process serves requests. It checks nothing "
        "else, so a platform only restarts an instance that has stopped "
        "responding."
    ),
)
async def live() -> LiveResponse:
    """Report that the process is serving requests.

    Async on purpose: it runs on the event loop, so a thread pool busy with
    slow assistant calls cannot make the platform restart a healthy instance.
    """
    return LiveResponse(status="alive")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness probe",
    description=(
        "Answers 200 when every component predictions need loaded at startup, "
        "and 503 naming the missing ones otherwise. It never calls the "
        "assistant's model provider."
    ),
    responses={503: {"model": ErrorResponse, "description": "Not ready."}},
)
async def ready(request: Request) -> ReadyResponse | JSONResponse:
    """Report whether every required component loaded."""
    missing = missing_components(request.app.state)
    if not missing:
        return ReadyResponse(status="ready")
    record_error_code(request, NOT_READY)
    body = ErrorResponse(
        error=NOT_READY, detail=f"Components not loaded: {', '.join(missing)}"
    )
    return JSONResponse(status_code=503, content=body.model_dump())

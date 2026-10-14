"""Domain exceptions and FastAPI exception handlers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.app.middleware.request_context import (
    INTERNAL_ERROR,
    record_error_code,
    route_template,
)
from shared.telemetry.context import get_request_id
from shared.telemetry.events import EventName, emit
from shared.telemetry.request_id import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


class UnavailableError(Exception):
    """A 503: something the request needs is not available.

    ``component`` names the contract component when the cause is that it did
    not load at startup; it is None for failures while running.
    """

    def __init__(self, message: str, component: str | None = None) -> None:
        """Record the message and the component that is not loaded, if any."""
        super().__init__(message)
        self.component = component


class ModelNotAvailableError(UnavailableError):
    """Raised when the prediction model has not been loaded."""


class AssistantNotAvailableError(UnavailableError):
    """Raised when the assistant or its dependencies are not available."""


class InsightsNotAvailableError(UnavailableError):
    """Raised when the goals model could not be fitted at startup."""


class FixturesNotAvailableError(UnavailableError):
    """Raised when no upcoming fixtures dataset is loaded."""


class SeasonOutlookNotAvailableError(UnavailableError):
    """Raised when a season outlook cannot be computed from the loaded data."""


class FeatureMissingError(Exception):
    """Raised when required feature columns are absent from the request."""

    def __init__(self, missing: list[str]) -> None:
        """Initialise with the list of missing column names."""
        self.missing = missing
        super().__init__(f"Missing feature columns: {missing}")


class FixtureFeaturesNotAvailableError(UnavailableError):
    """Raised when features are needed but no match history is loaded."""


class UnknownTeamError(Exception):
    """Raised when a requested team is not in the served competition's season."""

    def __init__(self, team: str, competition: str, season: str) -> None:
        """Record the unknown team and where it was looked up."""
        self.team = team
        self.competition = competition
        self.season = season
        super().__init__(f"'{team}' did not play in {competition} {season}")


class UnknownCompetitionError(Exception):
    """Raised when a request names a league the API does not serve."""

    def __init__(self, competition: str, supported: list[str]) -> None:
        """Record the requested league and the served ones."""
        self.competition = competition
        self.supported = supported
        super().__init__(
            f"'{competition}' is not served; choose one of: {', '.join(supported)}"
        )


def exception_type(exc: BaseException) -> str:
    """Return the exception's fully qualified class name."""
    kind = type(exc)
    return f"{kind.__module__}.{kind.__qualname__}"


def _respond(
    request: Request, exc: Exception, status: int, content: dict[str, Any]
) -> JSONResponse:
    """Log ``app.error`` for a typed error and return its JSON response."""
    error = content["error"]
    emit(
        logger,
        EventName.APP_ERROR,
        f"Request failed: {error}",
        route=route_template(request.scope),
        status=status,
        error_code=error,
        exception_type=exception_type(exc),
    )
    record_error_code(request, error)
    return JSONResponse(status_code=status, content=content)


def _unavailable(error: str) -> Callable[[Request, Exception], JSONResponse]:
    """Return a handler answering 503 with ``error``."""

    def handler(request: Request, exc: Exception) -> JSONResponse:
        component = getattr(exc, "component", None)
        if component is not None:
            emit(
                logger,
                EventName.COMPONENT_DEGRADED,
                f"Request needs {component}, which is not loaded",
                component=component,
                route=route_template(request.scope),
            )
        return _respond(request, exc, 503, {"error": error, "detail": str(exc)})

    handler.__doc__ = f"Return a 503 {error!r} response."
    return handler


model_not_available_handler = _unavailable("Model not available")
assistant_not_available_handler = _unavailable("Assistant not available")
insights_not_available_handler = _unavailable("Insights not available")
fixtures_not_available_handler = _unavailable("Fixtures not available")
season_outlook_not_available_handler = _unavailable("Season outlook not available")
fixture_features_not_available_handler = _unavailable("Match features not available")


def unknown_competition_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 naming the unknown league and the served ones."""
    assert isinstance(exc, UnknownCompetitionError)
    content = {
        "error": "Unknown competition",
        "detail": str(exc),
        "competition": exc.competition,
        "supported": exc.supported,
    }
    return _respond(request, exc, 422, content)


def unknown_team_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 naming the team that is not in the served season."""
    assert isinstance(exc, UnknownTeamError)
    content = {"error": "Unknown team", "detail": str(exc), "team": exc.team}
    return _respond(request, exc, 422, content)


def feature_missing_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 when feature columns are missing from the request."""
    assert isinstance(exc, FeatureMissingError)
    content = {
        "error": "Missing feature columns",
        "detail": str(exc),
        "missing": exc.missing,
    }
    return _respond(request, exc, 422, content)


def auth_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return an account error with its own status (ADR 022)."""
    from backend.app.services.account_service import AuthError  # noqa: PLC0415

    assert isinstance(exc, AuthError)
    content = {"error": exc.error, "detail": str(exc)}
    return _respond(request, exc, exc.status_code, content)


def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a 500 for any unhandled exception — no stack trace exposed."""
    emit(
        logger,
        EventName.APP_CRASH,
        "Unexpected error",
        exc_info=exc,
        route=route_template(request.scope),
        exception_type=exception_type(exc),
    )
    # This handler runs outside RequestContextMiddleware, so it adds the header.
    request_id = get_request_id()
    return JSONResponse(
        status_code=500,
        content={"error": INTERNAL_ERROR, "detail": "An unexpected error occurred."},
        headers={REQUEST_ID_HEADER: request_id} if request_id else None,
    )

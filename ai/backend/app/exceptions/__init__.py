"""Domain exceptions and FastAPI exception handlers."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ModelNotAvailableError(Exception):
    """Raised when the prediction model has not been loaded."""


class AssistantNotAvailableError(Exception):
    """Raised when the assistant or its dependencies are not available."""


class InsightsNotAvailableError(Exception):
    """Raised when the goals model could not be fitted at startup."""


class FixturesNotAvailableError(Exception):
    """Raised when no upcoming fixtures dataset is loaded."""


class SeasonOutlookNotAvailableError(Exception):
    """Raised when a season outlook cannot be computed from the loaded data."""


class FeatureMissingError(Exception):
    """Raised when required feature columns are absent from the request."""

    def __init__(self, missing: list[str]) -> None:
        """Initialise with the list of missing column names."""
        self.missing = missing
        super().__init__(f"Missing feature columns: {missing}")


class FixtureFeaturesNotAvailableError(Exception):
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


def unknown_competition_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 naming the unknown league and the served ones."""
    assert isinstance(exc, UnknownCompetitionError)
    logger.warning("Unknown competition: %s", exc)
    return JSONResponse(
        status_code=422,
        content={
            "error": "Unknown competition",
            "detail": str(exc),
            "competition": exc.competition,
            "supported": exc.supported,
        },
    )


def fixture_features_not_available_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Return a 503 when features must be computed but history is not loaded."""
    logger.error("Fixture features not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Match features not available", "detail": str(exc)},
    )


def unknown_team_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 naming the team that is not in the served season."""
    assert isinstance(exc, UnknownTeamError)
    logger.warning("Unknown team: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"error": "Unknown team", "detail": str(exc), "team": exc.team},
    )


def assistant_not_available_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 503 when the assistant service is unavailable."""
    logger.error("Assistant not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Assistant not available", "detail": str(exc)},
    )


def insights_not_available_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 503 when the goals model is not available."""
    logger.error("Insights not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Insights not available", "detail": str(exc)},
    )


def fixtures_not_available_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 503 when no fixtures dataset is loaded."""
    logger.error("Fixtures not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Fixtures not available", "detail": str(exc)},
    )


def season_outlook_not_available_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Return a 503 when the season outlook cannot be computed."""
    logger.error("Season outlook not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Season outlook not available", "detail": str(exc)},
    )


def model_not_available_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 503 when the model is not loaded."""
    logger.error("Model not available: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Model not available", "detail": str(exc)},
    )


def feature_missing_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 422 when feature columns are missing from the request."""
    assert isinstance(exc, FeatureMissingError)
    logger.warning("Missing features: %s", exc.missing)
    return JSONResponse(
        status_code=422,
        content={
            "error": "Missing feature columns",
            "detail": str(exc),
            "missing": exc.missing,
        },
    )


def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a 500 for any unhandled exception — no stack trace exposed."""
    logger.exception("Unexpected error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred.",
        },
    )


def auth_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return an account error with its own status (ADR 022)."""
    from backend.app.services.account_service import AuthError  # noqa: PLC0415

    assert isinstance(exc, AuthError)
    logger.info("Account error: %s", exc.error)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "detail": str(exc)},
    )

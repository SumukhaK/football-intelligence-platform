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

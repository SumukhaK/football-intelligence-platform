"""Domain exceptions and FastAPI exception handlers."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ModelNotAvailableError(Exception):
    """Raised when the prediction model has not been loaded."""


class FeatureMissingError(Exception):
    """Raised when required feature columns are absent from the request."""

    def __init__(self, missing: list[str]) -> None:
        """Initialise with the list of missing column names."""
        self.missing = missing
        super().__init__(f"Missing feature columns: {missing}")


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

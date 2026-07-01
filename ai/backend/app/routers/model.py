"""Model registry endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.app.exceptions import ModelNotAvailableError
from backend.app.schemas.common import ModelInfoResponse

router = APIRouter(tags=["Model"])


@router.get(
    "/model",
    response_model=ModelInfoResponse,
    summary="Current model information",
    description=(
        "Returns metadata for the currently loaded model: "
        "version, dataset version, training timestamp, git commit, and metrics."
    ),
    responses={
        503: {"description": "Model registry not available."},
    },
)
def model_info(request: Request) -> ModelInfoResponse:
    """Return metadata for the currently active model."""
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise ModelNotAvailableError("Model registry is not available.")

    entry = registry.latest()
    if entry is None:
        raise ModelNotAvailableError("No model versions registered.")

    return ModelInfoResponse(
        model_version=entry.version,
        dataset_version=entry.source_dataset_version,
        training_timestamp=entry.created_at.isoformat(),
        git_commit=entry.git_commit,
        metrics=entry.metrics,
    )

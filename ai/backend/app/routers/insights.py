"""Goals insights endpoint: likely scores, expected goals and goal markets."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.app.dependencies import InsightsServiceDep, ServedCompetitionsDep
from backend.app.schemas.insights import InsightsRequest, InsightsResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Insights"])


@router.post(
    "/insights",
    response_model=InsightsResponse,
    summary="Likely scores and goal markets for a fixture",
    description=(
        "Returns the goals model's view of a fixture: the five most likely "
        "scores, expected goals, both teams to score, over/under lines, clean "
        "sheets, team strengths and plain-language reasons (ADR 009). The model "
        "is fitted on the server's match history at startup. Probabilities are "
        "likelihoods, not betting advice."
    ),
    responses={
        422: {"description": "Unknown league, or a team not in its latest season."},
        503: {"description": "Goals model not available."},
    },
)
def insights(
    request: InsightsRequest,
    service: InsightsServiceDep,
    competitions: ServedCompetitionsDep,
) -> InsightsResponse:
    """Return scorelines and goal markets for one fixture."""
    competition = competitions.resolve(request.competition)
    response = service.insights(request, competition)
    logger.info(
        "insights: %s home=%s away=%s xg=%.2f-%.2f",
        competition,
        request.home_team,
        request.away_team,
        response.expected_goals.home,
        response.expected_goals.away,
    )
    return response

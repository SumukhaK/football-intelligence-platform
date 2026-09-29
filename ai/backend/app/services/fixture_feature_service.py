"""Fixture feature service — fills in match features from history (ADR 008)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from backend.app.exceptions import FixtureFeaturesNotAvailableError, UnknownTeamError
from backend.app.schemas.prediction import PredictionRequest
from backend.app.schemas.teams import TeamsResponse
from inference.fixture_features import Fixture, FixtureFeatureBuilder
from inference.fixture_features import UnknownTeamError as AIUnknownTeamError


class FixtureFeatureService:
    """Computes features for the served competition's fixtures."""

    def __init__(
        self,
        builder: FixtureFeatureBuilder,
        competition: str,
        today: Callable[[], date] = date.today,
    ) -> None:
        """Initialise with a loaded builder and the competition the API serves."""
        self._builder = builder
        self._competition = competition
        self._today = today

    def features_for(self, request: PredictionRequest) -> dict[str, float]:
        """Return the request's features, computing them when it has none.

        Raises:
            UnknownTeamError: If a team is not in the latest season.
        """
        if request.features is not None:
            return request.features
        fixture = Fixture(
            home_team=request.home_team,
            away_team=request.away_team,
            competition=self._competition,
            match_date=request.match_date or self._today(),
        )
        try:
            return self._builder.build(fixture)
        except AIUnknownTeamError as exc:
            raise UnknownTeamError(exc.team, exc.competition, exc.season) from exc

    def matches_through(self) -> str:
        """Date of the latest served-competition match in the loaded history."""
        return self._builder.latest_match_date(self._competition)

    def teams(self) -> TeamsResponse:
        """Return the latest season's teams for the served competition."""
        season, teams = self._builder.teams(self._competition)
        return TeamsResponse(competition=self._competition, season=season, teams=teams)


def resolve_features(
    request: PredictionRequest, service: FixtureFeatureService | None
) -> dict[str, float]:
    """Return supplied features, or computed ones when the service is loaded.

    Raises:
        FixtureFeaturesNotAvailableError: If features are missing and no match
            history is loaded.
    """
    if request.features is not None:
        return request.features
    if service is None:
        raise FixtureFeaturesNotAvailableError(
            "Request has no features and no match history is loaded. "
            "Send features, or check MATCHES_DIR in configuration."
        )
    return service.features_for(request)

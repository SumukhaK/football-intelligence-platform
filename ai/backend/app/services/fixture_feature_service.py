"""Fixture feature service — fills in match features from history (ADR 008).

One service covers every served league; callers pass the league already
resolved by ``ServedCompetitions`` (ADR 012).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from backend.app.exceptions import FixtureFeaturesNotAvailableError, UnknownTeamError
from backend.app.schemas.prediction import PredictionRequest
from backend.app.schemas.teams import TeamsResponse
from inference.fixture_features import Fixture, FixtureFeatureBuilder
from inference.fixture_features import UnknownTeamError as AIUnknownTeamError


class FixtureFeatureService:
    """Computes features for fixtures in any league held in the history."""

    def __init__(
        self,
        builder: FixtureFeatureBuilder,
        today: Callable[[], date] = date.today,
    ) -> None:
        """Initialise with a loaded builder."""
        self._builder = builder
        self._today = today

    def features_for(
        self, request: PredictionRequest, competition: str
    ) -> dict[str, float]:
        """Return the request's features, computing them when it has none.

        Raises:
            UnknownTeamError: If a team is not in the league's latest season.
            FixtureFeaturesNotAvailableError: If the league has no history.
        """
        if request.features is not None:
            return request.features
        fixture = Fixture(
            home_team=request.home_team,
            away_team=request.away_team,
            competition=competition,
            match_date=request.match_date or self._today(),
        )
        try:
            return self._builder.build(fixture)
        except AIUnknownTeamError as exc:
            raise UnknownTeamError(exc.team, exc.competition, exc.season) from exc
        except KeyError as exc:
            raise _no_history(competition) from exc

    def matches_through(self, competition: str) -> str:
        """Date of the league's latest match in the loaded history."""
        try:
            return self._builder.latest_match_date(competition)
        except KeyError as exc:
            raise _no_history(competition) from exc

    def teams(self, competition: str) -> TeamsResponse:
        """Return the league's latest season and its teams."""
        try:
            season, teams = self._builder.teams(competition)
        except KeyError as exc:
            raise _no_history(competition) from exc
        return TeamsResponse(competition=competition, season=season, teams=teams)


def _no_history(competition: str) -> FixtureFeaturesNotAvailableError:
    return FixtureFeaturesNotAvailableError(
        f"No match history loaded for {competition}."
    )


def resolve_features(
    request: PredictionRequest,
    service: FixtureFeatureService | None,
    competition: str,
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
            "Send features, or check MATCHES_DIR in configuration.",
            component="match_history",
        )
    return service.features_for(request, competition)

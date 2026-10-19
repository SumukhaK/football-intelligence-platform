"""Server-owned account favourites, grounded in the existing team catalog."""

from pydantic import ValidationError

from backend.app.schemas.account_preferences import (
    AccountFavourite,
    AccountPreferencesResponse,
)
from backend.app.services.account_service import AuthError
from backend.app.services.account_store import AccountStore, User
from backend.app.services.competitions import ServedCompetitions
from backend.app.services.fixture_feature_service import FixtureFeatureService


class PreferencesUnavailableError(AuthError):
    """The account store or catalog could not confirm usable preferences."""

    status_code, error = 503, "Account preferences unavailable"


class InvalidFavouriteError(AuthError):
    """The league/team pair is not in the canonical supported catalog."""

    status_code, error = 422, "Invalid favourite"


class AccountPreferencesService:
    """Validates and narrowly patches favourites in the existing account store."""

    def __init__(
        self,
        store: AccountStore,
        competitions: ServedCompetitions,
        catalog: FixtureFeatureService | None,
    ) -> None:
        """Use the same account store and catalog as authentication and /teams."""
        self._store, self._competitions, self._catalog = store, competitions, catalog

    def read(self, user: User) -> AccountPreferencesResponse:
        """Return a validated favourite or an explicit empty legacy account."""
        if user.favourite is None:
            return AccountPreferencesResponse(email=user.email, favourite=None)
        try:
            favourite = AccountFavourite.model_validate(user.favourite)
            self._validate(favourite)
        except (ValidationError, InvalidFavouriteError) as exc:
            raise PreferencesUnavailableError(
                "The saved favourite is invalid. Please retry or contact support."
            ) from exc
        return AccountPreferencesResponse(email=user.email, favourite=favourite)

    def save(
        self, user: User, favourite: AccountFavourite
    ) -> AccountPreferencesResponse:
        """Persist a validated pair without replacing any other account fields."""
        self._validate(favourite)
        try:
            self._store.set_favourite(user.email, favourite.model_dump())
        except Exception as exc:
            # JSON and Firestore expose different provider errors; none means empty.
            raise PreferencesUnavailableError(
                "Could not save your favourite. Try again."
            ) from exc
        return AccountPreferencesResponse(email=user.email, favourite=favourite)

    def _validate(self, favourite: AccountFavourite) -> None:
        if favourite.league not in self._competitions.names:
            raise InvalidFavouriteError("Choose a league listed by /v2/competitions.")
        if self._catalog is None:
            raise PreferencesUnavailableError(
                "The team catalog is unavailable. Try again."
            )
        try:
            teams = self._catalog.teams(favourite.league).teams
        except Exception as exc:
            raise PreferencesUnavailableError(
                "The team catalog is unavailable. Try again."
            ) from exc
        if favourite.team not in teams:
            raise InvalidFavouriteError(
                "Choose a team listed for this league by /v2/teams."
            )

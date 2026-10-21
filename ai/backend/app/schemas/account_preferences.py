"""Validated account favourite API contract (ADR 035)."""

from pydantic import BaseModel, ConfigDict, Field


class AccountFavourite(BaseModel):
    """Canonical names returned by the served competition and team catalog."""

    model_config = ConfigDict(extra="forbid", strict=True)

    league: str = Field(min_length=1, max_length=100)
    team: str = Field(min_length=1, max_length=100)


class SaveFavouriteRequest(BaseModel):
    """Replace only the current account's favourite; identity is never input."""

    model_config = ConfigDict(extra="forbid")

    favourite: AccountFavourite


class AccountPreferencesResponse(BaseModel):
    """A successful null explicitly confirms that no favourite exists."""

    email: str
    favourite: AccountFavourite | None


class AccountPreferencesError(BaseModel):
    """The structured error returned by every preference endpoint failure."""

    error: str
    detail: str

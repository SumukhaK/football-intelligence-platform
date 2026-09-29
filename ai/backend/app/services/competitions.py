"""The leagues the API serves, and how a request's league is resolved (ADR 012)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.exceptions import UnknownCompetitionError


@dataclass(frozen=True)
class ServedCompetitions:
    """Served league names and the default for requests that name none."""

    names: tuple[str, ...]
    default: str

    def resolve(self, requested: str | None) -> str:
        """Return the league a request means.

        Raises:
            UnknownCompetitionError: If ``requested`` is not a served league.
        """
        if requested is None:
            return self.default
        if requested not in self.names:
            raise UnknownCompetitionError(requested, list(self.names))
        return requested

"""Tests for backend.app.services.team_resolver."""

from __future__ import annotations

import pytest

from backend.app.services.team_resolver import TeamNotFoundError, resolve_team

KNOWN = ["Arsenal", "Bayern Munich", "Man City", "Man United", "Paris SG"]


@pytest.mark.parametrize(
    ("typed", "team"),
    [
        ("Man United", "Man United"),
        ("man united", "Man United"),
        ("Manchester United", "Man United"),
        ("Manchester City FC", "Man City"),
        ("Paris Saint-Germain", "Paris SG"),
        ("FC Bayern München", "Bayern Munich"),
        ("Arsenal FC", "Arsenal"),
    ],
)
def test_resolve_team_maps_common_names(typed: str, team: str) -> None:
    """Full club names, case and accents all map to the data's name."""
    assert resolve_team(typed, KNOWN) == team


def test_resolve_team_suggests_close_names() -> None:
    """A near miss names the likely team instead of guessing."""
    with pytest.raises(TeamNotFoundError, match="Did you mean: Arsenal"):
        resolve_team("Arsenl", KNOWN)


def test_resolve_team_rejects_unknown_teams() -> None:
    """A team that does not exist is an error with no suggestion."""
    with pytest.raises(TeamNotFoundError, match="No team called 'Atlantis FC'"):
        resolve_team("Atlantis FC", KNOWN)

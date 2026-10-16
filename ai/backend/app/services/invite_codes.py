"""Invite codes that are easy to read out and type: ``XXXX-XXXX``.

The alphabet leaves out I, L, O, U, 0 and 1, which are easily confused.
Anything that makes or checks codes (the CLI, the API, the dashboard's invite
page) uses these two functions so the format stays in one place.
"""

from __future__ import annotations

import secrets

INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTVWXYZ23456789"
_GROUP = 4


def new_invite_code() -> str:
    """A random code such as ``K7QM-3XWD`` (8 characters, about 39 bits)."""
    chars = "".join(secrets.choice(INVITE_ALPHABET) for _ in range(2 * _GROUP))
    return f"{chars[:_GROUP]}-{chars[_GROUP:]}"


def normalise_invite_code(code: str) -> str:
    """``code`` as stored: spaces and dashes removed, upper case."""
    return "".join(code.split()).replace("-", "").upper()

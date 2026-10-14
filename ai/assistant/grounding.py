"""Whether an answer's numbers come from its sources (ADR 018, ADR 030)."""

from __future__ import annotations

import re
from collections.abc import Iterable

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
# League names with a digit in them are names, not statistics.
_NAMES_WITH_DIGITS = re.compile(r"\bLigue 1\b")


def numbers_in(text: str) -> list[str]:
    """Every unsigned number written in ``text``, as written."""
    return _NUMBER.findall(text)


def matches(token: str, value: float) -> bool:
    """True when ``token`` is ``value`` (or ``value`` as a percentage) rounded.

    A probability such as 0.4712 matches "47", "47.1" or "0.47", but not "0"
    or "1": a bare integer only matches it as a percentage.
    """
    decimals = len(token.partition(".")[2])
    tolerance = 0.5 * 10**-decimals + 1e-9
    candidates = [abs(value) * 100]
    if decimals >= 2 or abs(value) >= 1:
        candidates.append(abs(value))
    return any(abs(float(token) - c) <= tolerance for c in candidates)


def ungrounded_numbers(answer: str, sources: Iterable[str]) -> list[str]:
    """Numbers in ``answer`` that no number in ``sources`` accounts for."""
    values = [float(t) for source in sources for t in numbers_in(source)]
    claimed = numbers_in(_NAMES_WITH_DIGITS.sub("", answer))
    return [t for t in claimed if not any(matches(t, v) for v in values)]

"""Telemetry for loading components: ``component.load`` and ``data.freshness``."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from typing import Protocol

from shared.telemetry.events import EventName, emit

logger = logging.getLogger(__name__)


class MatchHistory(Protocol):
    """Anything that knows the date of each league's latest match."""

    def matches_through(self, competition: str) -> str:
        """Return the date (YYYY-MM-DD) of the league's latest match."""


def load_component[T](
    name: str,
    load: Callable[[], T],
    clock: Callable[[], float] = time.monotonic,
) -> T | None:
    """Run ``load`` and log ``component.load``; None when it raised.

    A failed component leaves its service as None, so its endpoints answer 503.
    """
    started = clock()
    try:
        service = load()
    except Exception as exc:  # noqa: BLE001 — the component degrades, the API runs
        _log_load(name, "failed", started, clock, str(exc))
        return None
    _log_load(name, "ok", started, clock, None)
    return service


def _log_load(
    name: str,
    status: str,
    started: float,
    clock: Callable[[], float],
    reason: str | None,
) -> None:
    emit(
        logger,
        EventName.COMPONENT_LOAD,
        (
            f"Component {name} failed to load: {reason}"
            if reason
            else f"Component {name} loaded"
        ),
        component=name,
        status=status,
        duration_ms=round((clock() - started) * 1000),
        reason=reason,
    )


def age_hours(matches_through: str, now: datetime) -> float:
    """Hours from the start of the ``matches_through`` day (UTC) to ``now``."""
    day = date.fromisoformat(matches_through)
    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    return round((now - start).total_seconds() / 3600, 1)


def log_freshness(
    history: MatchHistory | None,
    competitions: Iterable[str],
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> None:
    """Log ``data.freshness`` for each league; nulls when there is no history."""
    moment = now()
    for competition in competitions:
        through: str | None = None
        if history is not None:
            try:
                through = history.matches_through(competition)
            except Exception:  # noqa: BLE001 — a league without data is just stale
                through = None
        emit(
            logger,
            EventName.DATA_FRESHNESS,
            f"{competition} match data checked",
            competition=competition,
            matches_through=through,
            age_hours=age_hours(through, moment) if through else None,
        )


def log_fallback(from_path: str, to_path: str, cause: str, message: str) -> None:
    """Log ``fallback`` for a degraded path taken instead of the normal one."""
    emit(
        logger,
        EventName.FALLBACK,
        message,
        from_path=from_path,
        to_path=to_path,
        cause=cause,
    )

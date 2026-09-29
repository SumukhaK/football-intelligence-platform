"""Daily refresh of the served match data, inside the backend (ADR 013).

Once a day, at a configured local hour, the service downloads the season in
progress, writes a new live dataset and reloads the services built from it
(server-side match features and the goals model). Requests keep using the
old data until the new services are ready, so nothing restarts. A failed
refresh is logged and the old data stays in place.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def next_run(now: datetime, hour: int) -> datetime:
    """The next time the clock reads ``hour``:00, strictly after ``now``."""
    candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    return candidate if candidate > now else candidate + timedelta(days=1)


def last_scheduled(now: datetime, hour: int) -> datetime:
    """The most recent time the clock read ``hour``:00, at or before ``now``."""
    return next_run(now, hour) - timedelta(days=1)


def is_due(built_at: datetime | None, now: datetime, hour: int) -> bool:
    """True when the data was built before the most recent scheduled refresh.

    Times must share a timezone. Data of unknown age is always due.
    """
    return built_at is None or built_at < last_scheduled(now, hour)


@dataclass(frozen=True)
class RefreshOutcome:
    """Result of one refresh attempt."""

    attempted_at: datetime
    dataset: Path | None
    error: str | None


class LiveRefreshService:
    """Runs the refresh and reload steps and remembers the last outcome."""

    def __init__(
        self,
        refresh: Callable[[], Path],
        reload: Callable[[], None],
        clock: Callable[[], datetime],
    ) -> None:
        """Initialise with the download step, the reload step and a clock."""
        self._refresh = refresh
        self._reload = reload
        self._clock = clock
        self.last_outcome: RefreshOutcome | None = None

    def run_once(self) -> RefreshOutcome:
        """Refresh the data and reload the services; never raises."""
        attempted = self._clock()
        try:
            dataset = self._refresh()
            self._reload()
        except Exception as exc:  # noqa: BLE001 — keep serving the old data
            logger.warning("Live data refresh failed: %s", exc)
            outcome = RefreshOutcome(attempted, None, str(exc))
        else:
            logger.info("Live data refreshed: %s", dataset.name)
            outcome = RefreshOutcome(attempted, dataset, None)
        self.last_outcome = outcome
        return outcome

    async def run_daily(self, hour: int, due_now: bool) -> None:
        """Refresh now if ``due_now``, then every day at ``hour``:00."""
        if due_now:
            await asyncio.to_thread(self.run_once)
        while True:
            wait = (next_run(self._clock(), hour) - self._clock()).total_seconds()
            await asyncio.sleep(max(wait, 0.0))
            await asyncio.to_thread(self.run_once)

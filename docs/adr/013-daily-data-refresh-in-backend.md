# ADR 013 — Refresh Match Data Daily Inside the Backend

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The server computes match features (ADR 008) and fits the goals model (ADR 009)
from the newest live dataset. Keeping that dataset current was manual: run
`scripts.refresh_live_dataset --confirm`, then restart the backend. Predictions
quietly went stale whenever nobody did.

The in-progress raw files are stored once per division per day and are
immutable (ADR 006, `ingestion/in_progress.py`). So refreshing more than once a
day adds nothing, and a daily refresh is the natural unit.

The project standards ask for local development with a single command, and for
background work through FastAPI or a simple queue rather than Celery.

## Decision

1. **Where.** The backend refreshes itself. At startup its lifespan starts one
   asyncio task that runs the refresh daily at `LIVE_REFRESH_HOUR`:00 local
   time (default 6). If the newest live dataset was built before the most
   recent scheduled time, it refreshes straight away.
2. **What.** A refresh downloads the season in progress for the top five
   leagues, writes a new `match_results_live_v<timestamp>.csv`
   (`ingestion.live_refresh.refresh_live_dataset`, shared with the script), and
   rebuilds the services that read it: server-side features and the goals
   model. The download and the rebuild run in a worker thread. Requests keep
   using the old services until the new ones replace them, so nothing restarts.
3. **Failure.** A failed refresh is logged, the old data stays in service, and
   `/health` reports `last_refresh_at` and `last_refresh_error`. `/health` also
   reports `matches_through`, the latest result date the server knows.
4. **Off switch.** An unset `LIVE_REFRESH_HOUR` turns the refresh off. The test
   suite disables it with an autouse fixture, so tests never download.

## Alternatives rejected

- **OS scheduler (Task Scheduler or cron) plus a restart.** This is
  platform-specific, is another thing to install, and drops requests during the
  restart.
- **An admin reload endpoint.** It needs authentication, which the project does
  not have yet (CLAUDE.md non-goals).
- **Refreshing every few hours.** The once-a-day raw snapshots would make
  later runs on the same day no-ops.

## Consequences

- The server stays current with no manual step; new results appear the day
  after football-data.co.uk publishes them. That source updates a few times a
  week, so `matches_through` can lag the real fixtures by a few days.
- Running the backend implies a daily download from football-data.co.uk.
  Turn it off with an unset `LIVE_REFRESH_HOUR` when offline.
- Each refresh writes a new versioned live dataset. Old versions are kept, as
  for every processed dataset.
- With more than one server process, each would refresh on its own. That is
  acceptable for local use, but a shared job would be needed at scale.

# syntax=docker/dockerfile:1
# The API image for Cloud Run (ADR 025). Build from the repository root after
# `uv run python -m scripts.build_snapshot --out ../snapshot` (run in ai/):
#   docker build --platform linux/amd64 -t football-api .
# The snapshot's files land where the backend's default paths expect them.

FROM python:3.12.11-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.1 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app/ai
COPY ai/pyproject.toml ai/uv.lock ./
# The server runs from ai/, so the project's own packages import from there
# and only the locked dependencies are installed.
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12.11-slim-bookworm
# XGBoost needs the OpenMP runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home app
COPY --from=build /app/.venv /app/.venv
COPY ai/ /app/ai/
COPY datasets/schemas/ /app/datasets/schemas/
COPY snapshot/ /app/
# Files stay root-owned, so the app user can read but never change them.
RUN /app/.venv/bin/python -m compileall -q /app/ai \
    && cd /app/ai && /app/.venv/bin/python -m scripts.build_snapshot --verify /app

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    NUMBA_CACHE_DIR=/tmp/numba \
    PORT=8080 \
    LIVE_REFRESH_HOUR=off \
    LOG_FORMAT=json \
    ASSISTANT_PROVIDER=off
WORKDIR /app/ai
USER app
EXPOSE 8080
# exec, so uvicorn gets Cloud Run's SIGTERM directly; one worker (ADR 025).
CMD exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" --workers 1

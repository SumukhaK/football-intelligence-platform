# Observability

This folder holds the telemetry contract: the agreement on what the backend
writes to its logs and traces, and what the ops console may read from them.

- [`telemetry-contract.md`](telemetry-contract.md): log line format, request
  IDs, the event catalogue, trace span names and the metrics derived from
  events.
- [`telemetry-events.json`](telemetry-events.json): the machine-readable copy
  of the event catalogue. `ai/tests/docs/test_telemetry_contract.py` checks
  that it lists the same events as the markdown catalogue.

The backend implements it in `ai/shared/telemetry/` and
`ai/backend/app/middleware/request_context.py`. Set `LOG_FORMAT=json` to get
the contract's log lines; plain text stays the local default.

Traces are off unless `TRACE_EXPORTER` is `otlp` (a local collector at
`OTLP_ENDPOINT`) or `gcp` (Cloud Trace). `ai/shared/telemetry/tracing.py` sets
up the provider; `main.py` adds one server span per request (not `/health` or
the docs pages). Child spans:

| Span | Where |
|---|---|
| `assistant.route`, `assistant.retrieve`, `assistant.embed`, `assistant.generate`, `assistant.tool.<name>` | `assistant/services/assistant_service.py` |
| `refresh.run` (the refresh's root), `refresh.download`, `refresh.reload` | `backend/app/services/live_refresh_service.py` |
| `dependency.<name>` (one per attempt, with a `retry` span event before each retry) | `shared/telemetry/retry.py` |

Inside a sampled span, JSON log lines carry `trace_id`,
`logging.googleapis.com/spanId` and, with `GCP_PROJECT_ID` set,
`logging.googleapis.com/trace`. The request span's query string is dropped and
its client address replaced by the `client_ref` hash.

Where each event is emitted:

| Event | Where |
|---|---|
| `http.request` | `backend/app/middleware/request_context.py` |
| `app.error`, `app.crash`, `component.degraded` | `backend/app/exceptions/__init__.py` |
| `component.load`, `data.freshness`, `fallback` (data) | `backend/app/startup_telemetry.py`, called from `main.py` |
| `ratelimit.rejected` | `backend/app/middleware/rate_limit.py` |
| `auth.event` | `backend/app/services/account_service.py` |
| `refresh.run`, `fallback` (refresh) | `backend/app/services/live_refresh_service.py` |
| `assistant.answer`, `assistant.tool`, `assistant.abstain`, `fallback` (tools) | `assistant/services/assistant_service.py` |
| `dependency.call`, `retry` | `shared/telemetry/retry.py`, used by `ingestion/downloader.py` (`HttpxTransport`) |

Downloads from football-data.co.uk (`football_data`) and openfootball
(`openfootball`) retry timeouts, connection errors, 429 (honouring a numeric
`Retry-After`) and 500/502/503/504 with full-jitter backoff, up to
`FOOTBALL_AI_HTTP_MAX_RETRIES` retries. Ollama calls are not retried yet; the
hosted provider adapter will use the same helper. `guardrail.event` comes with
hosting step 3b. `ai/tests/shared/telemetry/test_contract_conformance.py`
checks every event the tests emit against `telemetry-events.json`, and
`ai/tests/backend/test_log_privacy.py` checks that no question or email is
logged.

Contract version: **1.0.0**. The decision behind it is
[ADR 024](../adr/024-structured-telemetry-and-opentelemetry.md).

The read-only ops console lives in its own repository,
`SumukhaK/football-dashboard`, which keeps a copy of the JSON file at
`contract/telemetry-events.json`.

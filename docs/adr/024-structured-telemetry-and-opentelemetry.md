# ADR 024 — Structured Telemetry and OpenTelemetry

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The backend logs plain-text lines through Python's `logging`. A line carries
no request ID, so the lines written while handling one request cannot be
grouped, and nothing ties a slow chat answer to the retrieval, tool calls and
model calls inside it.

The hosted target is Cloud Run (`docs/plans/hosting-plans.md`, phase 6). Cloud
Run sends stdout to Cloud Logging, which understands JSON lines with special
keys for severity and trace. The whole hosted setup has to fit a $10 monthly
budget, so the observability stack must use what Google Cloud gives for free
or near free rather than a paid metrics backend.

Step 4 of `docs/plans/hosting-execution-tracker.md` asks for a request ID on
every request and log line, traces of each chat request, metrics for latency,
tokens, cost, errors and 429s, and one dashboard with alerts. Done when one
slow chat request can be explained from its trace alone.

## Decision

The backend writes structured JSON telemetry against one versioned contract,
`docs/observability/telemetry-contract.md`.

1. **JSON logs to stdout.** Every log line is one JSON object in the
   contract's format (section 1), with `request_id`, the Cloud Logging trace
   keys, `service`, `revision`, `api_version` and `contract_version`.
2. **One event catalogue.** The backend emits only the events and attributes
   listed in the contract (section 3). The catalogue is also kept as
   `docs/observability/telemetry-events.json`, which both repositories test
   against.
3. **Request IDs.** `X-Request-ID` is accepted when well formed, created
   otherwise, and returned on every response (section 2).
4. **Traces with OpenTelemetry.** One root span per request and the named
   child spans in section 4. Spans are exported to Cloud Trace in the cloud,
   to a local OTLP collector over HTTP in development, and nowhere in tests.
5. **Metrics from logs.** Metrics are derived from events as Cloud Logging
   log-based metrics, not emitted through a metrics SDK (section 5). Locally
   the Grafana stack queries the logs.
6. **Alerts in Cloud Monitoring** on those log-based metrics.
7. **A separate read-only console.** The ops dashboard lives in its own
   repository, `SumukhaK/football-dashboard`, and only reads telemetry.

### Dependencies this allows

Added in step M4, not before:

- `opentelemetry-api` and `opentelemetry-sdk`: the tracing API and SDK.
- `opentelemetry-instrumentation-fastapi`: the root span per request.
- `opentelemetry-exporter-otlp-proto-http`: export to the local collector.
- `opentelemetry-exporter-gcp-trace`: export to Cloud Trace.

## Consequences

- **Privacy.** Logs and span attributes never carry question or answer text,
  email addresses, passwords, tokens, invite codes, request bodies, query
  strings or `Authorization` headers. Users and client addresses appear only
  as HMAC references keyed with `TELEMETRY_SALT`. The JSON file lists the
  forbidden attribute names so tests can enforce this.
- **Sampling.** Every request gets a log line, so metrics stay exact. Traces
  can be sampled to keep within the Cloud Trace free tier without losing
  metrics, because metrics do not come from spans.
- **Contract versioning.** Any change to an event or field bumps the contract
  version: a new event or optional field is a minor bump, a renamed or removed
  field is a major bump. Both repositories pin the version they read.
- **Easier:** one request can be followed across logs and its trace; Cloud
  Logging, Error Reporting and Cloud Trace work without extra services.
- **Harder:** every new log line has to fit the catalogue, and tests that
  asserted on old log text move to asserting on events.
- **Work split.** M1 commits this contract and ADR. M2 to M6 implement it,
  each as its own pull request into `develop`; M4 adds the tracing
  dependencies above and M6 defines the log-based metrics.

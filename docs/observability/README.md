# Observability

This folder holds the telemetry contract: the agreement on what the backend
writes to its logs and traces, and what the ops console may read from them.

- [`telemetry-contract.md`](telemetry-contract.md): log line format, request
  IDs, the event catalogue, trace span names and the metrics derived from
  events.
- [`telemetry-events.json`](telemetry-events.json): the machine-readable copy
  of the event catalogue. `ai/tests/docs/test_telemetry_contract.py` checks
  that it lists the same events as the markdown catalogue.

Contract version: **1.0.0**. The decision behind it is
[ADR 024](../adr/024-structured-telemetry-and-opentelemetry.md).

The read-only ops console lives in its own repository,
`SumukhaK/football-dashboard`, which keeps a copy of the JSON file at
`contract/telemetry-events.json`.

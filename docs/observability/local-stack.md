# Local observability stack

One command gives you traces and dashboards on your own machine, with no cloud account. The stack is Grafana's `otel-lgtm` image (Grafana, Tempo for traces, Loki, Prometheus and an OpenTelemetry collector in one container), pinned in [`docker-compose.observability.yml`](../../docker-compose.observability.yml). It is for local use only; the cloud uses Cloud Logging, Trace and Monitoring (ADR 024).

## Start it

From the repository root:

```sh
docker compose -f docker-compose.observability.yml up -d
```

Grafana is at http://localhost:3000. The collector listens for OTLP on ports 4317 (gRPC) and 4318 (HTTP).

## Point the API at it

Add these lines to `ai/.env`:

```sh
TRACE_EXPORTER=otlp
OTLP_ENDPOINT=http://localhost:4318/v1/traces
LOG_FORMAT=json
```

Then run the API from `ai/` and keep its JSON logs in a file as well as on screen:

```sh
uv run uvicorn backend.app.main:app 2>&1 | tee api.log
```

## Find a request's trace

1. Make a request, for example a chat question in the app or `POST /v2/assistant/chat` in http://localhost:8000/docs.
2. Find its log line and copy the `trace_id`:

   ```sh
   jq -c 'select(.event == "assistant.answer") | {trace_id, request_id, attributes}' api.log
   ```

3. In Grafana open **Explore**, choose the **Tempo** data source, and paste the `trace_id` into the TraceQL box. The trace shows `assistant.route`, `assistant.retrieve`, each `assistant.generate` round and each `assistant.tool.*` call with their durations.

Other useful `jq` searches over `api.log`:

```sh
jq -c 'select(.severity == "ERROR")' api.log                    # every error
jq -c 'select(.event == "http.request") | .attributes' api.log  # each request's route, status and duration
jq -c 'select(.request_id == "<id>")' api.log                  # everything for one request
```

Logs stay in the file rather than in Loki: the API writes JSON to stdout, which is all Cloud Run needs, and `jq` is enough locally.

## Stop it

```sh
docker compose -f docker-compose.observability.yml down      # keep the data
docker compose -f docker-compose.observability.yml down -v   # also delete the volume
```

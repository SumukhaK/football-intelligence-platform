# Hosting Plans

Status: Proposed. Reviewed 5 October 2026; production AI target added 8 October 2026. This document creates no cloud resources.
Execution order and status: [hosting-execution-tracker.md](hosting-execution-tracker.md).
Goal: cloud deployment, measured AI quality, cold-start evidence and operational recovery for a personal portfolio application.

## Architecture and repository baseline

Use Cloud Run CPU serving, Cloudflare Workers AI hosted inference, and the existing NumPy retrieval store. Prepare model/data/index artifacts locally and publish an immutable serving snapshot. Preserve the local Ollama workflow. Do not add Qdrant, Kubernetes, GPUs or a relational database without a measured need.

Inspected implementation:
- Python 3.12 workspace: ai/pyproject.toml. Run backend.app.main:app from ai/.
- ai/backend/app/main.py loads v1/v2 model artifacts, SHAP, match data, fixtures and fits Dixon-Coles models at startup.
- assistant/pipeline.py supports injected Embedder/Generator protocols; backend startup still directly constructs Ollama implementations.
- Both document embeddings AND query embeddings depend on Ollama. Precomputed vectors alone do not remove that dependency.
- assistant/retrieval/vector_store.py stores embeddings.npy and documents.json.
- LIVE_REFRESH_HOUR=off disables the in-process scheduler. Its local design is documented in ADR 013.
- /v2/health always reports status=ok, with component availability fields; it is not strict readiness.
- Android NetworkConfig has 5-second connection and 30-second request timeouts.
- Chat calls synchronous code from an async route; rate limiting is process-local. Review both before concurrent cloud usage.

Before implementation, write the next unused ADR (currently 025) covering cloud serving, provider adapters, immutable snapshots and refresh scheduling. Explain the cloud extension to ADR 013 and invited-demo authentication. Local defaults remain unchanged. Follow the repository workflow with one task/PR into develop per phase. Fine-tuning remains outside project scope.

Architecture:
Android HTTPS -> Cloud Run FastAPI -> prediction/SHAP/goals models + NumPy retrieval -> hosted query embedding and generation.
Local artifact preparation -> validation -> immutable container -> staging -> promotion.
Later scheduled refresh -> validated snapshot -> staged release.

## Production AI target

The point of hosting is production experience with an AI system end to end: serving, releasing, evaluating, observing, troubleshooting and paying for it. The design favours what a senior AI engineer is expected to have run, at hobby cost (planning target $0-10/month).

| Area | Choice | What it teaches |
|---|---|---|
| Serving | FastAPI on Cloud Run, CPU only, scale to zero; separate staging and prod services; revision traffic splitting | Containers, cold starts, canary releases, rollback |
| LLM backends | One `Generator`/`Embedder` interface, two backends: Workers AI (hosted, free tier) for everyday traffic, and `qwen2.5:7b-instruct` in an Ollama container on a Cloud Run GPU, started only for eval runs and demo windows | Hosted APIs, quotas, failover; self-hosting weights, GPU cold starts, cost and latency trade-offs |
| Tool calling | The cloud model must support function calling (ADR 018). The Workers AI adapter implements `ToolCallingGenerator`; without it `AssistantService` silently drops the tools | Provider capability checks |
| Retrieval | Rebuild the index with the hosted embedding model and re-measure the 0.81 cut-off (it is tied to `nomic-embed-text`) with the abstention eval's questions | Embedding-space compatibility |
| Release gate | `evaluation.assistant_grounding` and `evaluation.assistant_abstention` run against staging in GitHub Actions before every promotion and every model or prompt change; a candidate model must pass both (ADR 019) | Evals as CI, not one-off scripts |
| Online quality | A sample of production answers goes through the deterministic grounding checker (no LLM judge, no quota); invented-number rate and refusal rate are metrics with alerts | Monitoring model behaviour, not just uptime |
| Observability | Request IDs; OpenTelemetry traces across retrieval, tool calls and generation; structured logs; metrics for p50/p95 latency, tokens, cost per answer, tool-call rate, refusal rate, provider errors and 429s; one dashboard and SLO alerts, all on Cloud Logging, Trace and Monitoring free tiers | Debugging a multi-step AI request |
| Operations | Budget caps, runbook, deliberate failure drills (provider outage, quota exhausted, bad model release, bad data snapshot) each written up as an incident report | Troubleshooting and post-mortems |

Not included, because they cost more than they teach here: Kubernetes, an always-on GPU, a managed vector database, a relational database, fine-tuning.

The API holds no user data, so there is no database to connect. "Connecting storage" means a Cloud Storage bucket for versioned model, data and index snapshots, plus Secret Manager for the provider token; object storage needs its own ADR first (Phase 7).

Interview evidence comes only from what is actually run: numbers, dashboards and incident write-ups from these phases, not from this plan.

## Free tools and budget

Planning target: $0-$10/month for low demo traffic, not a guaranteed bill. Do not rely on introductory credits. Taxes, bandwidth, data licences and storage are separate.

| Component | Choice | Cost/limit |
|---|---|---|
| CPU API serving | Cloud Run request-based billing, minimum instances 0 | Monthly free allowance based on us-central1: 180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests; aggregated per billing account |
| Generation/query embeddings | Workers AI Free | 10,000 neurons/day shared across inference; model-dependent, not a number of questions; choose free-eligible models |
| Vector retrieval | Existing NumPy store | No external service charge; limited by RAM/index size |
| CI/CD | Standard Actions runners on public repo | Free execution; external services and storage have separate costs |
| Registry/secrets/monitoring | Artifact Registry, Secret Manager, native logging/metrics | Review their separate pricing/free allowances; large ML images and excess logs can cost money |
| Training/ingestion/evaluation | Existing computer, uv, pytest, evaluation modules | No cloud compute charge; hosted evaluation consumes inference quota |
| Infrastructure | OpenTofu or Terraform and gcloud | Tooling can be free; created resources are billed |
| Optional vector DB | Qdrant Cloud Free | 1 GB RAM, 4 GB disk, single node; defer migration |
| Landing page | GitHub Pages/provider URL | No custom domain required |

Use local Linux/WSL Docker Engine or review Docker Desktop licensing. Avoid always-warm servers, paid GPUs, VPC connector/NAT, load balancers, Cloud SQL and paid monitoring SaaS initially.

Cost controls:
- [ ] Dedicated GCP project, $10 budget; alerts at $2/$5/$8.
- [ ] Review supported spend-cap budgets. Alerts-only budgets do not stop spending.
- [ ] Min instances 0, service max instances 1 initially; instance limits are not a hard dollar cap.
- [ ] Limit request sizes, concurrent chat, output tokens and total provider deadlines.
- [ ] Stay on Workers AI Free; fail gracefully when daily quota is exhausted.
- [ ] Retain current/previous/candidate images only and bounded logs.
- [ ] Inspect billing daily for week one; document actual resource costs, not just credits.
- [ ] Stop procedure: disable public access/chat, stop schedules, then deliberately remove billable resources.

## Does free hosting support a first-launch cold boot?

Yes: Cloud Run starts CPU instances from zero for incoming traffic, consuming its usage allowance. Billing still needs configuration; this is not an always-on free server.

Separate two measurements:
1. Application boot: imports, artifact loading, SHAP initialization, goals-model fitting and readiness.
2. Hosted inference first call: provider connection, queuing and generation. Workers AI operates serving; you are not hosting custom Ollama weights there.

Cloud Run's runtime contract requires listening within four minutes; request timeout includes startup and pending requests have a separate queue policy. Health-check docs currently describe longer configurable probe windows. Do not assume those override the runtime contract; validate actual staging behaviour and target much shorter startup.

Workers AI supports requests to free-eligible models under quota/capacity limits. Its reviewed docs do not guarantee a fast first inference or reserved warm capacity. Measure first-call behaviour; provider-side cold state cannot be proven from your application logs.

Never train, fetch historical data, download chat weights or rebuild the index at API startup. Never depend on a real generation call for readiness/liveness; probes could consume quota or trigger restarts during provider outages. Avoid keep-alive pings that hide scale-to-zero behaviour.

Proposed goals (not achieved metrics): boot <=20s; cold prediction <=25s; warm prediction p95 <=2s; warm chat <=20s under stated test conditions. Check these against the actual Android 30s request budget. Optimise boot before extending timeouts; preserve the fast offline fallback.

## Phase 0: local inventory and baseline

1. Read AGENTS.md, setup/quick-start.md, api.md and ADRs 009/013/014/015.
2. Record branch, commit, Python/dependency versions, served model versions, registry and dataset freshness.
3. From ai/, run uv sync --extra dev, uv run ruff check ., uv run black --check ., uv run mypy ., and uv run pytest -m "not integration".
4. Follow the quick start to prepare real artifacts; then run integration checks.
5. With live refresh off, measure startup and peak RAM. Time imports, CSV loading, both model loads, SHAP and goals fitting separately.
6. Inventory model.joblib, frozen v1 model, registry.json, processed results/fixtures and vector files. Check source redistribution rights.
7. Save a manifest with paths, hashes, sizes, code/dependency versions, embedding model/revision/dimensions, chunk configuration and source timestamps.

Exit: reproducible baseline and complete snapshot; no claims inferred from README alone.

## Phase 1: hosted adapters and a compatible embedding space

1. Create a Cloudflare account; choose one free-eligible generation model and one embedding model from the current catalog. Start small and evaluate.
2. Create a scoped inference token; use ignored local .env and Secret Manager for cloud. Never put it in Git/APK/image.
3. Implement Cloudflare Generator/Embedder against existing protocols with HTTP deadlines and explicit error mapping.
4. Add validated provider selection to AssistantSettings/backend Settings and inject adapters in backend startup; retain Ollama defaults.
5. REST: POST https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL_ID}; follow model-specific payload/response documentation.
6. Rebuild all document vectors with the chosen hosted embedding model. Use exactly the same model/revision/preprocessing for queries; nomic vectors cannot be searched with unrelated hosted embeddings, even at matching dimensions.
7. Keep separate local/cloud indexes and reject incompatible manifests at startup.
8. If embedding quotas prove insufficient, evaluate a small local CPU embedder: package weights beforehand, benchmark RAM/boot, rebuild the corpus with that exact model.
9. Report actual provider/model metadata in every chat response; do not leave cloud responses labelled with the local model name.
10. Bound embedding plus generation with one overall deadline and at most one retry for retryable errors. Respect Retry-After within that deadline.
11. Return structured temporary assistant-unavailable errors on capacity/quota failures; predictions remain usable.
12. Add fixture-based adapter tests and a small real evaluation. CI must not need live provider secrets for unit tests.
13. Choose a Workers AI model that supports function calling; implement tool calls in the adapter and test that the tools are actually offered.
14. Re-run both assistant evals against the hosted model; it must pass both before it serves traffic.

Exit: cloud chat with citations works; local mode and provider-failure tests pass.

## Phase 2: packaging and deterministic boot

1. Create Dockerfile/.dockerignore: Python 3.12 Linux amd64, pinned resolution, non-root runtime user and working directory matching ai/.
2. Copy serving code and trusted, validated snapshot only. Exclude secrets, raw downloads, private documents and unused training outputs.
3. Set explicit MODEL_PATH, V1_MODEL_PATH, REGISTRY_PATH, MATCHES_DIR, FIXTURES_DIR and ASSISTANT_VECTOR_STORE_PATH. Preserve v1 API/artifacts.
4. Cloud setting LIVE_REFRESH_HOUR=off is supported today. Local daily refresh remains unchanged.
5. Package artifacts read-only with manifest. Only load trusted joblib files. Container disk is ephemeral and writes consume memory.
6. If goals fitting dominates boot, introduce versioned precomputed artifacts with compatibility tests/reference outputs before changing loaders.
7. Use one Uvicorn worker initially. Select memory from measured peak plus headroom; 1 vCPU/1 GiB is a trial setting, not a capacity guarantee.
8. Entrypoint must expand injected PORT, listen on 0.0.0.0 and forward termination correctly. Current module: backend.app.main:app.
9. Implement proposed /v2/ready for required artifacts and /v2/live for cheap process health; update api.md. Preserve /v2/health diagnostics.
10. Do not check remote generation in probes. Separate configured assistant/index readiness from provider availability.
11. Remove raw message logging from assistant router for cloud; record request IDs, outcome and component durations instead.
12. Address sync chat work inside async route with bounded thread offload or async design; test concurrency and shutdown.
13. Test a constrained local container without Ollama or startup network downloads.

Exit: deterministic boot, accurate readiness and safe missing-artifact failures.

## Phase 3: GCP provisioning and private staging

1. Install/authenticate gcloud; create dedicated project, attach billing and configure budgets first.
2. Choose one region. us-central1 is pricing reference; Mumbai/Singapore can improve client latency but check region costs/egress. Registry and API share a region.
3. Enable run.googleapis.com, artifactregistry.googleapis.com and secretmanager.googleapis.com.
4. Create a Docker Artifact Registry repository and dedicated runtime service account in Console. Grant only needed secret access; separate deployer from runtime.
5. Configure registry Docker authentication. Build locally initially to avoid Cloud Build usage; push a commit-tagged image and record its digest.
6. Store provider token securely as a versioned secret. Do not paste it into command history. Provider-selection settings are proposed Phase 1 work, not existing settings.
7. Deploy private staging in Console: request-based billing; min 0/max 1; concurrency 4; one worker; trial 1 vCPU/1 GiB; 60s staging diagnostic request timeout; no GPU.
8. Configure supported startup/liveness probes after Phase 2, within verified runtime constraints.
9. Inject artifact paths, hosted provider settings and secret versions; set LIVE_REFRESH_HOUR=off.
10. Authenticate staging via gcloud run services proxy football-api-staging --region <region> --port 8080. Use another terminal for HTTP checks.
11. Verify real fixtures, predictions, SHAP, insights and grounded chat; inspect memory and billing before public access.
12. Record reproducible gcloud commands/IaC with actual project IDs and image digest in a private runbook; credentials remain outside the repository.

Exit: private staging works with real assets and scoped identity.

## Phase 4: first deployment and idle-wake verification

1. Deploy a new tagged revision; capture boot logs, revision, manifest and initialization timings. Deployment itself may boot an instance, so its first HTTP request does not alone prove request-triggered cold boot.
2. Disable uptime probes/proxy traffic and wait until metrics show zero instances. Trigger one authenticated prediction; correlate request time/ID with a new startup log.
3. Repeat several independently observed restarts; capture failures, time to first byte, total latency and component timings.
4. Compare with at least 20 warm samples. Test first hosted embedding/generation after inactivity separately; do not assert provider-side cold state.
5. Use real api.md payloads. curl.exe timing options: -sS -o NUL -w "status=%{http_code} first_byte=%{time_starttransfer} total=%{time_total}".
6. Open Android after observed scale-to-zero. Test fixtures/predict/chat, loading state, retry, saved data and readable errors.
7. Test unreachable network separately. Preserve 5s connection fallback; adjust per-operation request budgets only with measured evidence and client tests.
8. If boot is slow, move fitting offline, reduce unnecessary imports/data copies and tune memory/thread usage. Do not hide delay behind unrestricted timeouts.
9. Simulate provider 429/quota/timeout/5xx in staging. Predictions survive and probes do not restart the service.
10. Write docs/reports/hosting-cold-start.md: instance-state evidence, sample count, region/resources, cold/warm p50/p95/max, errors and actual costs.
11. Resolve any runtime/probe-documentation discrepancy against observed staging behaviour before release.

Exit: first-launch and zero-to-one behaviour recorded, without free-tier latency promises.

## Phase 5: invited/public demo and Android access

1. Keep staging private. Design short-lived tester credentials or a small auth flow before public chat; Cloud Run IAM is not automatically usable by existing Android code.
2. Never embed privileged/static provider or cloud tokens in the APK. Scope and expire demo credentials.
3. Bound bodies, context, output and concurrent chat. Validate proxy/client identity before trusting forwarded addresses.
4. Process-local quotas reset on restart and do not aggregate; document limitations and use shared quota state before stronger/multi-instance guarantees.
5. Set HTTPS base URL through existing client configuration; preserve emulator/local mode and API version.
6. Structured errors/citations/freshness; no internal stack traces. CORS is only needed for a browser page and is not authentication.
7. Test prompt injection and unsupported questions. LLM narratives must not invent prediction probabilities.
8. Publish GitHub Pages links to demo/video/APK/source and current limitations, including idle-wake delay.

Exit: a controlled demo with no exposed paid-provider credentials.

## Phase 6: evaluation, monitoring, CI/CD and recovery

1. Extend existing evaluation with 50-100 versioned questions/expected evidence, unsupported and injection cases; separate tuning from held-out data.
2. Score retrieval relevance, correctness, citation support and abstention; human-review a sample. LLM grading needs calibration and quota.
3. Preserve season-based prediction splits; report baselines/calibration, scope/dates and leakage controls.
4. Measure warm/cold latency, errors/429s, RAM, embedding/generation duration, usage and data freshness. Estimate cost without credits as well as actual bill.
5. Native logs/metrics first; request/revision/model/index IDs, bounded retention, no secrets/raw user content.
5a. Trace each chat request across retrieval, each tool call and generation (OpenTelemetry to Cloud Trace); record tokens and cost per answer.
5b. Score a sample of production answers with the grounding checker and alert on invented numbers or a jump in refusals.
6. Load-test locally at concurrency 1/2/4, then briefly in staging with stop thresholds.
7. CI: existing lint/types/tests -> image -> staging -> readiness + real smoke tests -> manual promotion -> rollback rehearsal.
8. Use GitHub OIDC/Google Workload Identity Federation scoped to trusted repository/ref; untrusted PRs must not deploy or access secrets.
9. Immutable image digests and snapshot manifest; retain known-good revision. Encode verified infrastructure in IaC and protect state.
10. Rehearse failed candidate rollback and snapshot restoration. Prove API/data/index compatibility after recovery.
11. Add monitoring after cold tests; frequent probes can keep the API warm, so document that trade-off.

Exit: repeatable releases and measured quality/performance/recovery evidence.

## Phase 7: refresh without an always-on server

Initially refresh locally from ai/: uv run python -m scripts.refresh_live_dataset --confirm and uv run python -m scripts.refresh_fixtures --confirm.
1. Validate results/fixtures; retain immutable source timestamps. Rebuild dependent index/artifacts when sources change.
2. Produce a new coherent snapshot/image; stage/smoke-test/promote atomically. Keep last-known-good on failure. No automatic retraining without promotion criteria.
3. Later schedule GitHub Actions plus workflow_dispatch. Schedules can be delayed; expose stale/missed refresh status.
4. CI must fetch a trusted baseline/model if absent from checkout. Do not retrain merely because CI lacks artifacts.
5. Keep licensed/private snapshots out of public Actions artifacts; use rights-reviewed private storage/registry.
6. Enforce one release workflow at a time; document UTC schedule, source lag and freshness. Cloud startup must never download/rebuild everything.
7. Object storage/runtime download design requires another ADR; ephemeral disk cannot be the source of truth.

Exit: refresh survives restarts, stale data is visible and validation failures preserve service.

## Phase 7b: self-hosted model window

1. Package `qwen2.5:7b-instruct` in an Ollama (or vLLM) container with the weights baked into the image; no download at startup.
2. Deploy it as a separate Cloud Run GPU service, min 0, max 1, private; confirm the current GPU price and region availability first.
3. Point staging's generator at it through config only; run both evals and record cold start, tokens per second, latency and cost per answer against Workers AI.
4. Scale back to zero after each window; set a budget alert specific to the GPU service.

Exit: a measured hosted-versus-self-hosted comparison in docs/reports, with the switch done by configuration.

## Phase 8: operate and teardown

1. Invite testers and record actual usage/feedback. Observe initially for 2-4 weeks; duration alone is not reliability proof.
2. Rehearse provider outage, bad artifact, rollback and restore; document incidents and fixes.
3. Publish an operational report with usage, measurements, resources, costs and remaining limits.
4. Resume claims must reflect completed personal-project evidence; no invented commercial production/users/metrics.
5. Teardown: stop schedules, revoke public access, remove unused services/images, review secret/storage/log costs and verify billing. Stopping traffic alone does not remove all billable resources.

## Completion checklist

- [ ] Architecture ADR and local fallback retained.
- [ ] GCP deployment and hosted inference verified.
- [ ] Compatible versioned query/document embedding space.
- [ ] Required readiness and graceful provider outage.
- [ ] Verified cold/idle-wake tests and Android first-launch behaviour.
- [ ] Held-out AI quality and performance evaluation.
- [ ] Secrets, admission limits, release automation and rollback.
- [ ] Atomic refresh, freshness visibility and restoration.
- [ ] Actual budget checks and teardown procedure.
- [ ] Tool-calling cloud model passing both assistant evals; evals gate every release.
- [ ] Traces, online grounding checks and alerts on model behaviour.
- [ ] Hosted versus self-hosted model comparison measured.
- [ ] Failure drills written up as incident reports.

## Official sources

Checked 5 October 2026; recheck before execution.
- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
- [Health checks](https://docs.cloud.google.com/run/docs/configuring/healthchecks)
- [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Workers AI limits](https://developers.cloudflare.com/workers-ai/platform/limits/)
- [Workers AI REST setup](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)
- [Spend-cap budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)
- [Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage)
- [Qdrant pricing](https://qdrant.tech/pricing/)

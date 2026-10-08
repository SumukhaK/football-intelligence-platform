# Hosting Execution Tracker

Status: Not started. Created 8 October 2026.
Design and detail: [hosting-plans.md](hosting-plans.md). This file is the order of work and its status.

Work one step at a time, one PR into `develop` per step (or per sub-step when it grows). A step is done only when its "Done when" checks pass and its evidence is saved. Update the Status column and the date in the same PR.

Status values: `Not started`, `In progress`, `Blocked (reason)`, `Done (date)`.

| # | Step | Plan phase | Status |
|---|---|---|---|
| 0 | Baseline, accounts and budget guardrails | 0, 3.1 | Not started |
| 1 | Host the API: container and private staging | 2, 3 | Not started |
| 2 | Connect storage and secrets | 3, 7 | Not started |
| 3 | Connect the hosted LLM | 1 | Not started |
| 4 | Observability: logs, traces, metrics, alerts | 6 | Not started |
| 5 | CI/CD with the eval gate | 6 | Not started |
| 6 | Cold-start and idle-wake measurement | 4 | Not started |
| 7 | Production service and the Android app | 5 | Not started |
| 8 | Online quality monitoring | 6 | Not started |
| 9 | Self-hosted model window | 7b | Not started |
| 10 | Scheduled data refresh | 7 | Not started |
| 11 | Failure drills and runbook | 6, 8 | Not started |
| 12 | Operate, report, teardown plan | 8 | Not started |

---

## 0. Baseline, accounts and budget guardrails

- [ ] ADR 020: cloud serving, provider adapters, immutable snapshots, refresh scheduling.
- [ ] Local baseline: lint, types, tests; startup time and peak RAM with `LIVE_REFRESH_HOUR=off`.
- [ ] Snapshot manifest: model, registry, datasets, fixtures, index; hashes and sizes.
- [ ] GCP project with billing; budget $10 with alerts at $2, $5, $8.
- [ ] Cloudflare account; Workers AI free plan; scoped API token kept out of Git.

Done when: baseline numbers are recorded and budget alerts fire on a test threshold.
Evidence: baseline table in `docs/reports/hosting-baseline.md`.

## 1. Host the API: container and private staging

- [ ] Dockerfile and `.dockerignore`: Python 3.12, non-root, artifacts copied read-only, no Ollama.
- [ ] `/v2/live` and `/v2/ready`; `docs/api.md` updated.
- [ ] Chat route no longer blocks the event loop; raw message logging removed.
- [ ] Image pushed to Artifact Registry by digest.
- [ ] Cloud Run staging: private, min 0, max 1, one worker, `LIVE_REFRESH_HOUR=off`, assistant off.
- [ ] Fixtures, predict, explain and insights work through `gcloud run services proxy`.

Done when: staging serves real predictions from a pinned image digest.
Evidence: deploy commands in the private runbook; screenshot of a staging prediction.

## 2. Connect storage and secrets

- [ ] ADR: Cloud Storage bucket for versioned snapshots (model, data, fixtures, index).
- [ ] Bucket with versioning; runtime service account can read only.
- [ ] Startup loads the snapshot named in config; fails loudly on a missing or mismatched manifest.
- [ ] Provider token in Secret Manager, mounted as a versioned secret.

Done when: a new snapshot reaches staging by changing config, without rebuilding the image.
Evidence: the manifest check failing on a deliberately wrong snapshot.

## 3. Connect the hosted LLM

- [ ] Workers AI `Generator` and `Embedder` adapters behind the existing protocols, with deadlines and error mapping.
- [ ] A function-calling model chosen; the adapter implements tool calls (ADR 018).
- [ ] Index rebuilt with the hosted embedding model; 0.81 cut-off re-measured with the abstention questions.
- [ ] Provider selection in settings; local Ollama stays the default.
- [ ] Quota, timeout and 5xx return a structured 503; predictions keep working.
- [ ] Grounding and abstention evals pass against staging.

Done when: staging chat answers with citations and quotes the API's numbers, and both evals pass.
Evidence: eval output saved under `docs/reports/`.

## 4. Observability: logs, traces, metrics, alerts

- [ ] Request ID on every request and log line.
- [ ] OpenTelemetry traces: retrieval, each tool call, generation, to Cloud Trace.
- [ ] Metrics: p50/p95 latency, tokens, cost per answer, tool-call rate, refusal rate, provider errors and 429s.
- [ ] One dashboard; alerts on error rate, p95 latency and provider failures.

Done when: one slow chat request can be explained from its trace alone.
Evidence: dashboard screenshot and one annotated trace.

## 5. CI/CD with the eval gate

- [ ] GitHub OIDC with Workload Identity Federation; no long-lived keys.
- [ ] Pipeline: lint, types, tests, image, staging deploy, readiness and smoke tests, both assistant evals, manual promotion.
- [ ] Untrusted PRs cannot deploy or read secrets.
- [ ] Rollback rehearsed on staging.

Done when: a change reaches staging without manual commands, and a failing eval blocks promotion.
Evidence: a pipeline run blocked by a deliberately broken prompt.

## 6. Cold-start and idle-wake measurement

- [ ] Observed scale-to-zero, then cold requests correlated with startup logs.
- [ ] At least 20 warm samples; cold and warm p50, p95 and max.
- [ ] First hosted-model call after idle measured separately.

Done when: `docs/reports/hosting-cold-start.md` exists with the numbers.
Evidence: that report.

## 7. Production service and the Android app

- [ ] Prod service from the same image digest as staging; traffic splitting for canaries.
- [ ] Demo access without secrets in the APK; request, body and chat limits.
- [ ] App points at the HTTPS URL through config; local mode still works.
- [ ] Timeouts adjusted only from step 6 measurements.

Done when: the app works against prod after the service has scaled to zero.
Evidence: screen recording from a cold start.

## 8. Online quality monitoring

- [ ] A sample of prod answers scored with the grounding checker.
- [ ] Invented-number rate and refusal rate as metrics, with alerts.
- [ ] Eval question set grown towards 50-100 versioned cases, held-out split kept.

Done when: a deliberately degraded prompt in staging trips the alert.
Evidence: the alert and the metric chart.

## 9. Self-hosted model window

- [ ] `qwen2.5:7b-instruct` container with weights baked in; private Cloud Run GPU service, min 0, max 1.
- [ ] GPU price and region checked; GPU-specific budget alert.
- [ ] Staging switched to it by config; both evals run; cold start, tokens per second, latency and cost compared with Workers AI.
- [ ] Scaled back to zero after each window.

Done when: the comparison report exists and the GPU service costs nothing while idle.
Evidence: `docs/reports/hosted-vs-self-hosted.md`.

## 10. Scheduled data refresh

- [ ] Refresh job (Cloud Run Jobs or GitHub Actions) builds and validates a new snapshot.
- [ ] Stage, smoke-test, promote; last known good kept on failure.
- [ ] Data freshness visible in `/v2/health` and on the dashboard.

Done when: a refresh runs unattended and a failing validation leaves prod untouched.
Evidence: one successful and one deliberately failed run.

## 11. Failure drills and runbook

- [ ] Drills: provider outage, quota exhausted, bad model release, bad data snapshot, cold start under load.
- [ ] Each drill: what broke, how it was detected, how long to recover, what changed.
- [ ] Runbook covers deploy, rollback, rotate secret, restore snapshot, stop spending.

Done when: every drill has a written incident report.
Evidence: `docs/reports/incidents/`.

## 12. Operate, report, teardown plan

- [ ] Two to four weeks of invited use; usage, costs and feedback recorded.
- [ ] Operations report with measurements, real costs and remaining limits.
- [ ] Teardown procedure tested on staging.

Done when: the operations report is published.
Evidence: `docs/reports/hosting-operations.md`.

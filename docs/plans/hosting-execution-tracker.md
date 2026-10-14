# Hosting Execution Tracker

Status: In progress (staging is live with the assistant on; the app walkthrough, alerts and evals against staging are next). Created 8 October 2026; reordered and step 5a added 8 October 2026; statuses updated 14 October 2026.
Design and detail: [hosting-plans.md](hosting-plans.md). This file is the order of work and its status.

Work one step at a time, one PR into `develop` per step (or per sub-step when it grows). A step is done only when its "Done when" checks pass and its evidence is saved. Update the Status column and the date in the same PR.

Steps run in table order. Step 3a comes before 3 because its remaining Firestore store needs the cloud project and fits with step 2, and the hosted LLM needs the secret store from step 2.

Status values: `Not started`, `In progress`, `Blocked (reason)`, `Done (date)`.

| # | Step | Plan phase | Status |
|---|---|---|---|
| 0a | Chat route fix | this tracker | Done (8 October 2026) |
| 0 | Baseline, accounts and budget guardrails | 0, 3.1 | In progress (budget alert test to go) |
| 1 | Host the API: container and private staging | 2, 3 | Done (14 October 2026) |
| 2 | Connect storage and secrets | 3, 7 | Not started |
| 3a | Invite-only accounts and consent | [plan](accounts-and-consent-plan.md) | In progress (sign-in and consent checked on staging through the API on 14 October 2026; the app walkthrough to go) |
| 3 | Connect the hosted LLM | 1 | In progress (on in staging since 14 October 2026 and quoting the API's numbers; evals against staging to go) |
| 3b | Guardrails gateway: safety, scope router, cache, limits | [analysis](assistant-guardrails-analysis.md) | In progress (safety check and strikes done, ADR 027; cache, budgets and the rules sheet to go) |
| 3c | Short-term chat memory | [plan](chat-memory-plan.md) | In progress (built and released in v2.5.0; staging deploy with the `history-key` secret to go) |
| 4 | Observability: logs, traces, metrics, alerts | 6 | In progress (request IDs, traces, local stack, and metrics and alerts as code done; apply and dashboard to go) |
| 5 | CI/CD with the eval gate | 6 | Not started |
| 5a | Security hardening | this tracker | Done (11 October 2026) |
| 6 | Cold-start and idle-wake measurement | 4 | In progress (first cold boot on Cloud Run: 19 s to ready) |
| 6a | Closed beta on staging | 5 | In progress (staging build variant done) |
| 7 | Production service and the Android app | 5 | Not started |
| 8 | Online quality monitoring | 6 | Not started |
| 9 | Self-hosted model window | 7b | Not started |
| 10 | Scheduled data refresh | 7 | Not started |
| 11 | Failure drills and runbook | 6, 8 | Not started |
| 12 | Operate, report, teardown plan | 8 | Not started |

---

## 0a. Chat route fix

Can land any time, before step 0.

- [x] Chat route no longer blocks the event loop; raw message logging removed.

Done when: the chat route runs the model call off the event loop and no question text is logged unless the user opted in ([accounts plan](accounts-and-consent-plan.md)).
Evidence: tests.

## 0. Baseline, accounts and budget guardrails

- [x] Next free ADR (currently 025; check develop and open PRs): cloud serving, provider adapters, immutable snapshots, refresh scheduling. ADR 025; ADR 026 covers the Firestore account store.
- [x] Local baseline: lint, types, tests; startup time and peak RAM with `LIVE_REFRESH_HOUR=off`. See [hosting-baseline.md](../reports/hosting-baseline.md).
- [x] Snapshot manifest: model, registry, datasets, fixtures, index; hashes and sizes.
- [x] GCP project with billing; budget $10 with alerts at $2, $5, $8. Set up 10 October 2026 as a ₹500 monthly budget on the whole billing account, alerting at 50%, 90%, 100% and 150%.
- [x] Cloudflare account; Workers AI free plan; scoped API token kept out of Git (local `ai/.env` and Secret Manager).

Done when: baseline numbers are recorded and budget alerts fire on a test threshold.
Evidence: baseline table in `docs/reports/hosting-baseline.md`.

## 1. Host the API: container and private staging

- [x] Dockerfile and `.dockerignore`: Python 3.12, non-root, artifacts copied read-only, no Ollama.
- [x] `/v2/live` and `/v2/ready`; `docs/api.md` updated.
- [x] Image pushed to Artifact Registry by digest.
- [x] Cloud Run staging: private, min 0, max 1, one worker, `LIVE_REFRESH_HOUR=off`, assistant off. Deployed 14 October 2026 from v2.2.0, with a 4-minute startup probe.
- [ ] Fixtures, predict, explain and insights work through `gcloud run services proxy`. Fixtures, predict and explain checked 14 October 2026 with a signed-in, consented user; the assistant answered with the prediction's numbers and the safety check refused a harmful question. Insights still to try.

Done when: staging serves real predictions from a pinned image digest.
Evidence: deploy commands in the private runbook; screenshot of a staging prediction.

## 2. Connect storage and secrets

- [ ] ADR: Cloud Storage bucket for versioned snapshots (model, data, fixtures, index).
- [ ] Bucket with versioning; runtime service account can read only.
- [ ] Startup loads the snapshot named in config; fails loudly on a missing or mismatched manifest.
- [ ] Provider token in Secret Manager, mounted as a versioned secret.

Done when: a new snapshot reaches staging by changing config, without rebuilding the image.
Evidence: the manifest check failing on a deliberately wrong snapshot.

## 3a. Invite-only accounts and consent

Backend first, then the Android screens. Details in [accounts-and-consent-plan.md](accounts-and-consent-plan.md).

- [x] ADR 022 for accounts, sessions and consent.
- [x] Store interface, a JSON file store, and a Firestore store chosen with `ACCOUNT_STORE=firestore` (ADR 026).
- [x] Invites, scrypt passwords, login lockout, revocable sessions.
- [x] `/v2/auth/*`, `/v2/me`, `/v2/me/consent`; every `/v2` data route needs a session and current consent when `AUTH_REQUIRED` is on.
- [x] Owner script: invite (also resets a password), ban, unban.
- [x] Android: redeem invite, sign in, consent screen, token storage, 401 and 403 handling (#84).

Done when: an invited friend can redeem an invite, agree to the notice and use the app, and nobody else can.
Evidence: integration tests and a staging walkthrough.

## 3. Connect the hosted LLM

- [x] Workers AI `Generator` and `Embedder` adapters behind the existing protocols, with deadlines and error mapping.
- [x] A function-calling model chosen (`@cf/google/gemma-4-26b-a4b-it`, thinking off); the adapter implements tool calls (ADR 018). See [hosted-assistant-evals.md](../reports/hosted-assistant-evals.md).
- [x] Index rebuilt with the hosted embedding model; cut-off re-measured with the abstention questions (0.77, recorded in the index).
- [x] Provider selection in settings; local Ollama stays the default.
- [x] Quota, timeout and 5xx return a structured 503; predictions keep working.
- [ ] Grounding and abstention evals pass against staging.

Done when: staging chat answers with citations and quotes the API's numbers, and both evals pass.
Evidence: eval output saved under `docs/reports/`.

## 3b. Guardrails gateway: safety, scope router, cache, limits

The season router (ADR 021) is the first piece.

- [x] Safety check before the model; three strikes means a permanent ban that revokes sessions. Llama Guard 3 on Workers AI, `ASSISTANT_SAFETY=true` (ADR 027); needed before friends use the beta.
- [ ] Scope router extended beyond season questions.
- [ ] Answer cache keyed on the normalised question, data snapshot, model and prompt version.
- [ ] Daily token budget per user and a global daily budget; **off in staging**, on in prod from beta numbers.
- [ ] Remaining allowance returned to the app; rules sheet and info button in the Assistant screen.

Done when: a harmful question adds a strike without a model call, and in prod an over-budget user is refused before any tokens are spent.
Evidence: tests and staging logs.

## 3c. Short-term chat memory

Plan: [chat-memory-plan.md](chat-memory-plan.md). Decision: [ADR 030](../adr/030-short-term-chat-memory.md). Ships in v2.5.0.

- [x] Design approved: signed history on the phone, 4 exchanges, 30-minute reset, consent unchanged (15 October 2026).
- [x] Backend: optional `history`, `conversation_id` and `signature`; HMAC with `HISTORY_KEY`; trimming; Llama Guard over the user's turns; the history prompt rule; log counts.
- [x] `evaluation/assistant_conversation.py` passes on Workers AI (8/8), and abstention (20/20), grounding (11/11) and season (7/7) still pass (15 October 2026).
- [x] App: keeps the signed window, New chat, 30-minute idle reset (ViewModel tests first; checked on the emulator 15 October 2026).
- [ ] Staging: `history-key` secret mounted; history tokens and neurons per answer checked in the logs.

Done when: a follow-up such as "and the draw?" is answered from the conversation on staging, a forged turn is ignored, and all four evals pass.
Evidence: eval output in `docs/reports/hosted-assistant-evals.md` and staging logs.

## 4. Observability: logs, traces, metrics, alerts

Contract: [telemetry contract](../observability/telemetry-contract.md) and [ADR 024](../adr/024-structured-telemetry-and-opentelemetry.md).

- [x] Request ID on every request and log line.
- [x] OpenTelemetry traces: retrieval, each tool call, generation, to Cloud Trace (#91).
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

## 5a. Security hardening

Lands before friends use the beta (step 6a).

- [x] Rate limiter keys on the real client address behind Cloud Run's proxy (`TRUSTED_PROXY_HOPS=1` reads the address Cloud Run's front end appended to `X-Forwarded-For`), with a test.
- [x] Size limit on chat messages in the request schema; request body size limit.
- [x] CORS and security headers reviewed for the hosted API. Decision: no CORS middleware, because the only client is the Android app and CORS only matters to browsers; every response sends `X-Content-Type-Options: nosniff`. HSTS is left to Cloud Run, which serves HTTPS only.
- [x] The server refuses to start on Cloud Run (`K_REVISION` set) with `AUTH_REQUIRED` off or the development `TELEMETRY_SALT`.
- [x] Dependency vulnerability scans in CI for Python and Gradle (`dependency-scan.yml`, on every PR, push and weekly: pip-audit over `uv.lock`, and OSV-Scanner over the app's release runtime dependencies).
- [x] App: retry with exponential backoff and jitter for idempotent GET requests only, honouring `Retry-After` on 429 and 503; no retry on POST. Up to two retries on 429, 502, 503 and 504, waits capped at 8 s; connection failures are not retried, so the offline fallback stays fast.
- [x] App: R8 resource shrinking on for release builds; release build checked for working Ktor and serialization keep rules. Checked 11 October 2026 on an emulator: sign-in, consent, teams, fixtures, predict, explain, insights and outlook all load in the shrunk build.
- [x] Decision recorded: no SSL pinning (Cloud Run certificates rotate without notice; HTTPS plus no secrets in the APK covers the risk) and no Play Integrity for an invite-only app; revisit if the app goes public.

Done when: every checkbox has a test or a recorded decision.
Evidence: tests, and the decision note in this file (or an ADR if the ADR policy requires one).

## 6. Cold-start and idle-wake measurement

- [ ] Observed scale-to-zero, then cold requests correlated with startup logs. First deploy: 19 s from instance start to ready (14 October 2026), against nearly 4 minutes for a cold image locally.
- [ ] At least 20 warm samples; cold and warm p50, p95 and max.
- [ ] First hosted-model call after idle measured separately.

Done when: `docs/reports/hosting-cold-start.md` exists with the numbers.
Evidence: that report.

## 6a. Closed beta on staging

- [x] Staging build variant: its own application ID, build number and a "-stg" app name, pointing at the staging URL (`staging` flavor; the URL comes from `frontend/local.properties`).
- [x] Crash reports from the staging app with Firebase Crashlytics, sent only after consent; the notice (version 2) says so (ADR 028).
- [ ] APK shared directly with invited friends.
- [ ] Usage recorded per consented user: questions per day, tokens, latency, refusals, router and cache hits, tool use. Question text only with opt-in.
- [ ] Weekly summary to set production budgets and limits.

Done when: two weeks of beta usage are summarised and the prod limits are chosen from them.
Evidence: `docs/reports/beta-usage.md`.

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

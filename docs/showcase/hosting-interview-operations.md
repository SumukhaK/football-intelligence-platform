# Hosting Interview Guide — Verify, Use and Recover

[Preparation](hosting-interview-guide.md) · [Cloud setup](hosting-interview-cloud.md) · [Interview Q&A](interview-guide.md)

All commands are **PowerShell templates**, not commands run in this documentation task. Continue with the verified variables from the cloud page. Preserve exact revision/digest/snapshot/model/index identities in a private runbook.

## 1. Reach a private service and check the correct probes

```powershell
gcloud run services proxy $service --region=$region --project=$projectId --port=8080
```

This runs a local forwarding proxy using your Google login. `--region`/`--project` select the service; `--port` selects the local port. Keep that terminal open. In another PowerShell terminal:

```powershell
$baseUrl = "http://localhost:8080"
Invoke-RestMethod -Uri "$baseUrl/v2/live"
Invoke-RestMethod -Uri "$baseUrl/v2/ready"
Invoke-RestMethod -Uri "$baseUrl/v2/health"
```

`Invoke-RestMethod` sends HTTP and decodes JSON; `-Uri` is the URL. For the app-accessible service, replace baseUrl with the recorded HTTPS staging URL only after its access policy is configured.

Expect live=alive, ready=ready, and health component/version/freshness fields. /health status=ok alone is insufficient: it can still report unloaded components. No probe spends hosted inference quota. [API contract](../api.md).

A timeout/503 needs component logs and request IDs; repeatedly hitting chat is not a health check.

## 2. Create an invited test account deliberately

For a **new isolated test email**, owner tooling from ai/ can use Firestore via local ADC:

```powershell
$env:ACCOUNT_STORE = "firestore"
$env:GCP_PROJECT_ID = "<verified-project-id>"
$env:FIRESTORE_DATABASE = "(default)"
$env:FIRESTORE_COLLECTION_PREFIX = "staging_"
uv run python -m scripts.manage_accounts invite --email "<test-email>"
```

`--email` identifies the account receiving the one-time invite. This prints a sensitive invite code; give it only to that tester. The operation can reset an existing account's password and revoke sessions, so do not use an existing beta email accidentally. Nothing is emailed by this command.

Redeem in the Android Invite code tab, or follow POST /v2/auth/redeem-invite in API docs. Invite normalization accepts case/spaces/dashes; password minimum 10 characters. The backend stores hashes, not plaintext passwords/tokens.

## 3. Sign in, read the notice and accept the current version

A template that keeps the password out of literal shell history:

```powershell
$credentials = Get-Credential -Message "Staging test account"
$loginBody = @{
  email = $credentials.UserName
  password = $credentials.GetNetworkCredential().Password
} | ConvertTo-Json
$session = Invoke-RestMethod -Uri "$baseUrl/v2/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
$headers = @{ Authorization = "Bearer $($session.token)" }
$me = Invoke-RestMethod -Uri "$baseUrl/v2/me" -Headers $headers
$me.consent_text
```

`Get-Credential` prompts; `-Message` labels the prompt. `ConvertTo-Json` serializes a PowerShell object. HTTP `-Method` chooses POST; `-ContentType` declares JSON; `-Body` is that JSON; `-Headers` sends the bearer token. The password/token still exist in process memory: do not print loginBody/session/headers or capture them in shared transcripts.

Read the returned notice first. If consent_required is true and the tester chooses to accept, use the returned version:

```powershell
$consentBody = @{ version = $me.consent_version; store_questions = $false } | ConvertTo-Json
$me = Invoke-RestMethod -Uri "$baseUrl/v2/me/consent" -Method Post -Headers $headers -ContentType "application/json" -Body $consentBody
```

store_questions=false avoids saving test question text. Opting in enables separate 90-day question records, not raw request logs or stored answers. Consent v2 discloses Cloudflare model processing and staging Firebase crash reports. [ADRs 022](../adr/022-invite-only-accounts-and-consent.md), [028](../adr/028-crash-reports-in-the-staging-app.md), [034](../adr/034-storing-opted-in-question-text.md).

## 4. Exercise the real artifact paths

```powershell
$fixtures = Invoke-RestMethod -Uri "$baseUrl/v2/fixtures?competition=Premier%20League" -Headers $headers
```

Inspect that fixtures are available/current, then choose a returned pair. If the list is empty, stop and diagnose freshness rather than indexing blindly:

```powershell
$fixture = $fixtures.fixtures[0]
$matchBody = @{
  home_team = $fixture.home_team
  away_team = $fixture.away_team
  competition = "Premier League"
} | ConvertTo-Json
$prediction = Invoke-RestMethod -Uri "$baseUrl/v2/predict" -Method Post -Headers $headers -ContentType "application/json" -Body $matchBody
$explanation = Invoke-RestMethod -Uri "$baseUrl/v2/explain" -Method Post -Headers $headers -ContentType "application/json" -Body $matchBody
$insights = Invoke-RestMethod -Uri "$baseUrl/v2/insights" -Method Post -Headers $headers -ContentType "application/json" -Body $matchBody
```

Check H/D/A probabilities, model version, finite SHAP contributions and likely scores. A 1–1 top exact score alongside a win pick is not necessarily a contradiction: the win sums many scorelines. Predictor and goals model are separate.

The tracker records fixtures/predict/explain checks 14 October; insights remains unchecked in that item. Running a template later must create its own dated evidence rather than rewriting history.

## 5. Test hosted chat and signed follow-ups

```powershell
$conversationId = [guid]::NewGuid().ToString()
$question = "Who is favourite: $($fixture.home_team) against $($fixture.away_team) in the Premier League?"
$chatBody = @{ message = $question; conversation_id = $conversationId } | ConvertTo-Json
$answer = Invoke-RestMethod -Uri "$baseUrl/v2/assistant/chat" -Method Post -Headers $headers -ContentType "application/json" -Body $chatBody
$followBody = @{
  message = "And the draw?"
  conversation_id = $conversationId
  history = @(
    @{ role = "user"; content = $question }
    @{ role = "assistant"; content = $answer.answer; signature = $answer.signature }
  )
} | ConvertTo-Json -Depth 6
$followup = Invoke-RestMethod -Uri "$baseUrl/v2/assistant/chat" -Method Post -Headers $headers -ContentType "application/json" -Body $followBody
```

`[guid]::NewGuid()` creates a conversation ID. `-Depth 6` makes nested history objects serialize fully. Compare answer numbers with the current prediction/tool outputs, not football intuition. The server verifies HMAC signatures bound to user/conversation; the app keeps only four completed exchanges.

Current answers intentionally contain no visible citations; sources is empty. Retrieval/tool provenance is logged in assistant.answer. Do not make “answer contains citations” a staging pass criterion just because an older plan says so. [ADR 029](../adr/029-assistant-sources-logged-not-shown.md), [ADR 030](../adr/030-short-term-chat-memory.md).

Safety tests belong to a disposable account: the third harmful-question strike bans it and revokes sessions. Guard failure should produce 503 without a strike. The 15 October report covers finite safety/conversation cases; it does not prove no false positives or prompt injection bypasses.

## 6. Build the Android staging app

The Android flavor gives a separate app ID/name alongside local. From repository root:

```powershell
Set-Location frontend
.\gradlew.bat assembleStagingDebug "-PstagingBaseUrl=https://football-api-staging-147318467723.asia-south1.run.app"
adb install -r app/build/outputs/apk/staging/debug/app-staging-debug.apk
```

`assembleStagingDebug` selects the staging/debug variant. `-PstagingBaseUrl` is a Gradle project property, with base URL only (the network layer adds /v2). Alternatively set staging.baseUrl in ignored local.properties. `adb install -r` replaces the installed same-ID app while retaining data.

For Crashlytics, the owner supplies ignored app/src/staging/google-services.json. Missing config still builds but sends no crash reports. Collection defaults off until consent; local flavor has no Firebase code.

Walk through invite/sign-in/consent, favourite picker, Fixtures, Predict->Explain, My Team/outlook and Assistant follow-up/New chat. Test after observed scale-to-zero, then unreachable network and cached-data banners. App auth sessions are not Google IAM tokens. No provider/Google service-account secret belongs in the APK.

## 7. Observe a request before tuning

```powershell
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="football-api-staging"' --project=$projectId --limit=30 --format=json
```

`logging read` queries existing logs; `--limit` bounds entries; `--format=json` emits structured output. Correlate request_id/trace/revision with component.load, dependency.call, tool and assistant events. Avoid copying user/account data into public reports.

TRACE_EXPORTER=gcp plus the runtime trace role sends sampled traces. Follow one slow chat through safety, embedding, retrieval, tools and generation. Server logs omit raw questions; opted-in text lives only in the account store's questions collection.

Metrics/alerts exist as code under [infrastructure/monitoring](../../infrastructure/monitoring/). The [v2.3 release record](../releases/v2.3.0.md) says seven alert policies were applied. The older tracker checkbox still needs reconciliation; metric/notification delivery checks and a complete dashboard remain pending. Counts combine staging/production by default; lockout policy counts locked_out events, not unique accounts. Do not call a dashboard screenshot evidence of a working backend contract without checking its contract version.

Measure a cold request only after observing zero instances and correlating the request with a new startup. Capture at least 20 warm samples plus independent cold starts, reporting p50/p95/max, errors and region/resources. The recorded 19 seconds is one startup-to-ready sample, not a statistically measured cold p95. Provider first-call-after-idle latency is separate.

## 8. Rollback is a traffic choice, not a retrain

Inspect revisions and retain a verified known-good revision/image/snapshot before changing traffic:

```powershell
gcloud run revisions list --service=$service --region=$region --project=$projectId
gcloud run services update-traffic $service --to-revisions="<known-good-full-revision>=100" --region=$region --project=$projectId
```

`--service` filters revisions; `--to-revisions name=100` routes 100% to that revision. Recheck probes, authenticated predictions and chat afterward. This is a recovery **template**; tracker still says rollback rehearsal pending. [Cloud Run rollback documentation](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration).

Traffic rollback does not reverse Firestore writes, secret version deletion or external side effects. An old revision must remain compatible with current account/consent data and referenced secrets. The removed 14 October image is not a guaranteed rebuild/rollback source.

## 9. Data freshness needs a release

LIVE_REFRESH_HOUR=off is intentional in Cloud Run. A local daily scheduler cannot durably update a container that scales to zero. Today's workflow is: refresh locally -> validate -> build new snapshot -> verify -> image -> stage -> smoke/evaluate -> promote; retain the last good snapshot/image.

Do not train automatically on every refresh or rewrite the frozen model's test evidence. A bucket-loaded snapshot and unattended scheduled publishing are **pending** and need their own accepted design before implementation. Inspect health matches_through/last_refresh fields and fixture updated_at; a ready 200 says artifacts loaded, not that they are today's data.

## 10. What can you honestly say is unfinished?

As recorded by the tracker, these remain incomplete or need evidence reconciliation:

- Budget alert delivery test and actual usage/billing report.
- Full staging app walkthrough, insights check and complete assistant evals against staging.
- Cold/warm latency distribution and first provider call after idle.
- Reconcile the older alert-application checkbox with v2.3 evidence; verify metric/notification delivery and complete dashboard/quality monitoring.
- User/global daily budgets, answer cache and in-app conduct/rules sheet.
- GitHub OIDC deployment pipeline with staging eval gate; rollback rehearsal.
- Production promotion, scheduled snapshot refresh and bucket-backed snapshot loading.
- Failure drills, recovery/secret rotation/stop-spending runbook and measured beta period.

The project's cloud experience is real but still an invite-only staged rollout. Describe that state plainly. Never claim exact deployment commands, costs, production traffic or all pending checks as completed without dated evidence.

[Back to interview Q&A](interview-guide.md) · [Hosting concepts and recorded facts](hosting-interview-guide.md)

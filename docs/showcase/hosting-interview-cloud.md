# Hosting Interview Guide — Cloud Setup and Deployment

[Preparation](hosting-interview-guide.md) · [Verification and operation](hosting-interview-operations.md)

Every command here is a **PowerShell template**, not recorded shell history and not executed for this update. The supplied private runbooks now identify the original project, registry and runtime identity; their recorded Bash/PowerShell commands and explanations are preserved in the local docs/prompt-book/staging-command-reference*.md companion. Public examples retain placeholders. Resource creation and deployment can cost money; the live full image digest is not included in the supplied records.

## 1. Establish the project and budget

Install the Google Cloud CLI. Sign in as the owner/deployer; local Application Default Credentials are a separate login for Python tools such as Firestore invitations:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud projects describe "147318467723" --format="value(projectId)"
```

The last command is a read-only way to resolve the recorded project number; its output has not been obtained by this guide. `--format` selects the output field. Do not replace PROJECT_ID with the numeric project number by guessing.

For a new project, create/link billing in Console first. For this existing beta, inspect the existing project rather than creating a duplicate. In Billing -> Budgets, review the recorded ₹500 monthly billing-account budget and its 50/90/100/150% notifications; testing delivery is still pending. A budget alert normally **does not stop spending**. [Google budget documentation](https://docs.cloud.google.com/billing/docs/how-to/budgets).

Use verified values in the same PowerShell session:

```powershell
$projectId = "<verified-project-id>"
$region = "asia-south1"
$repo = "<verified-docker-repository>"
$runtimeSa = "<verified-runtime-service-account-email>"
$service = "football-api-staging"
$image = "${region}-docker.pkg.dev/$projectId/$repo/football-api"
$tag = "<candidate-code-tag>"
$imageTag = "${image}:$tag"
gcloud config set project $projectId
```

These are variables, not secrets. `gcloud config set project` changes the local CLI default; subsequent templates still include `--project` to make their destination explicit. Region is recorded for Cloud Run; the registry location must be verified before constructing its hostname.

## 2. Enable services and assign identities

The deployer installs/releases the program; the **runtime service account** is the identity of the running backend. Cloud Build has another build identity. Avoid giving the running app Owner/Editor just to bypass permissions errors. [Service identity](https://docs.cloud.google.com/run/docs/securing/service-identity).

```powershell
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com firestore.googleapis.com cloudtrace.googleapis.com logging.googleapis.com monitoring.googleapis.com --project=$projectId
```

`services enable` activates APIs. The named services provide execution, image storage/building, secrets, accounts, traces, logs and alerts. `--project` is the destination project.

If they do not already exist, these are **creation templates**; choose the actual repository/identity names in Console:

```powershell
gcloud artifacts repositories create $repo --repository-format=docker --location=$region --project=$projectId
gcloud iam service-accounts create football-runtime --display-name="Football API runtime" --project=$projectId
```

`--repository-format=docker` selects container images; `--location` chooses the repository region; `--display-name` is a label for people. Set `$runtimeSa` to the resulting verified account email rather than assuming the example is the existing staging identity.

Runtime permissions, scoped to this project:

```powershell
gcloud projects add-iam-policy-binding $projectId --member="serviceAccount:$runtimeSa" --role="roles/datastore.user"
gcloud projects add-iam-policy-binding $projectId --member="serviceAccount:$runtimeSa" --role="roles/cloudtrace.agent"
```

`--member` names who gets access; `--role` names the permission bundle. Datastore User permits Firestore application data access; Cloud Trace Agent permits trace export. Logs written to stdout are collected by Cloud Run. Grant Secret Accessor on each required secret below, not all project secrets.

Separately, the human deployer needs Cloud Run deployment rights, permission to act as the runtime account and access to the image. The builder needs repository write access; Cloud Run's service agent needs image read access. Check the actual principals and organization policy rather than granting broad project roles to every identity.

## 3. Firestore is durable account storage

Create/verify a Firestore **Native mode** database in Console, checking its chosen location before creation. Database location is not inferred from the Cloud Run URL. Existing staging uses Firestore per [ADR 026](../adr/026-firestore-account-store.md).

Configure `ACCOUNT_STORE=firestore`, `FIRESTORE_DATABASE=(default)`, `GCP_PROJECT_ID` and `FIRESTORE_COLLECTION_PREFIX=staging_`. Prefixes separate staging accounts from future production within a database. Container disk is ephemeral, so JSON accounts would disappear on restart.

The store uses server SDK credentials from the runtime service account. Android calls FastAPI; it does not access Firestore directly. No service-account JSON key belongs in the app or image.

[ADR 034](../adr/034-storing-opted-in-question-text.md) adds question records only for signed-in users who opted in. TTL setup is an operation, not automatic merely because expires_at is saved:

```powershell
gcloud firestore fields ttls update expires_at --collection-group=staging_questions --enable-ttl --database="(default)" --project=$projectId
gcloud firestore fields ttls list --database="(default)" --project=$projectId
```

`expires_at` is the timestamp field; `--collection-group` selects all collections of that name; `--enable-ttl` turns deletion on; `--database` selects the database. Tracker records staging ACTIVE on 17 October. TTL is asynchronous, generally deleting within 24 hours after expiry; this is not a strict 90-day deletion deadline. [Firestore TTL](https://docs.cloud.google.com/firestore/native/docs/ttl).

## 4. Secrets stay behind the API

Create secret containers through Console or this example template:

```powershell
gcloud secrets create workers-ai-token --replication-policy=automatic --project=$projectId
gcloud secrets create telemetry-salt --replication-policy=automatic --project=$projectId
gcloud secrets create history-key --replication-policy=automatic --project=$projectId
```

`--replication-policy=automatic` lets Google manage replication. The supplied initial runbook names workers-ai-token and telemetry-salt; the later tracker records history-key. Their numeric versions must be verified for the target revision. Inspect existing secrets rather than creating duplicates. Add secret **values/versions** through the owner's secure Console flow. Do not put values into source, command history or a shared screenshot.

For each existing secret, grant only the runtime identity read access:

```powershell
gcloud secrets add-iam-policy-binding workers-ai-token --member="serviceAccount:$runtimeSa" --role="roles/secretmanager.secretAccessor" --project=$projectId
```

Repeat for the other two secrets. `add-iam-policy-binding` updates access policy; `secretAccessor` permits reading secret versions. Choose a numeric version for each deployment reference; environment-secret values resolve at instance startup. Rotation should produce a reviewed new revision. [Cloud Run secrets](https://docs.cloud.google.com/run/docs/configuring/services/secrets).

Create a scoped Workers AI inference token in Cloudflare. The backend needs account ID, token, a tool-capable chat model, embeddings and Llama Guard. Current recorded choices are Gemma 4 thinking off, Qwen3 embedding 0.6B and Llama Guard 3. Follow [Workers AI REST setup](https://developers.cloudflare.com/workers-ai/get-started/rest-api/).

Workers Free currently has 10,000 neurons/day shared across requests/models, resetting 00:00 UTC; it is not 10,000 questions. Confirm model eligibility/prices and avoid assuming a cost/latency guarantee. [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/).

## 5. Build and store one immutable image

From repository root, with the verified `snapshot/` already present:

```powershell
gcloud auth configure-docker "${region}-docker.pkg.dev"
docker build --platform linux/amd64 --tag $imageTag .
docker push $imageTag
gcloud artifacts docker images list $image --include-tags --project=$projectId
```

`configure-docker` lets Docker obtain registry credentials. `--platform linux/amd64` targets the server architecture; `--tag` labels the image; trailing `.` is the build context. `push` uploads it. `--include-tags` shows labels alongside digests. Record the full `sha256:...` from registry output. [Artifact Registry image guide](https://docs.cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling).

The tracker records **Cloud Build** for the 15/17 October releases. The supplied v2.6 runbook includes its exact 17 October command and temporary upload rules; those are preserved in the private local companion. A reusable **template** is:

```powershell
gcloud builds submit <clean-upload-context> --tag=$imageTag --project=$projectId
```

`submit` uploads source; `--tag` asks Cloud Build to build its Dockerfile and push that name. Prepare a fresh reviewed context containing only Dockerfile, required ai source/lock files, datasets/schemas and the verified snapshot. Inspect the upload list before submitting: default gcloud ignore rules can exclude the Git-ignored snapshot, while an overly broad upload can expose ai/.env/accounts. Do not assume Docker's .dockerignore protects the earlier source upload. [Cloud Build guide](https://docs.cloud.google.com/build/docs/build-push-docker-image).

## 6. Describe the deployment configuration explicitly

Create a **private, uncommitted** YAML file outside the checkout, replacing PROJECT_ID/ACCOUNT_ID. It contains non-secret settings; secret values are injected separately.

```yaml
GCP_PROJECT_ID: "<verified-project-id>"
AUTH_REQUIRED: "true"
ACCOUNT_STORE: "firestore"
FIRESTORE_DATABASE: "(default)"
FIRESTORE_COLLECTION_PREFIX: "staging_"
LIVE_REFRESH_HOUR: "off"
LOG_FORMAT: "json"
TRUSTED_PROXY_HOPS: "1"
TRACE_EXPORTER: "gcp"
ASSISTANT_PROVIDER: "workers_ai"
ASSISTANT_SAFETY: "true"
ASSISTANT_VECTOR_STORE_PATH: "assistant/vector_store_workers_ai"
WORKERS_AI_ACCOUNT_ID: "<verified-cloudflare-account-id>"
WORKERS_AI_CHAT_MODEL: "@cf/google/gemma-4-26b-a4b-it"
WORKERS_AI_EMBED_MODEL: "@cf/qwen/qwen3-embedding-0.6b"
WORKERS_AI_GUARD_MODEL: "@cf/meta/llama-guard-3-8b"
WORKERS_AI_THINKING: "false"
```

The snapshot must contain that exact index path/model. Auth and safety are enabled; logs are structured and trace export uses the runtime identity. Refresh off means data changes only through publishing a new snapshot. Secrets provide non-development telemetry salt and HMAC history key; no token appears in this YAML.

## 7. Deploy privately first

Choose verified numeric secret versions and actual digest/settings path:

```powershell
$imageDigest = "${image}@sha256:<full-verified-digest>"
$settingsFile = "<private-path>/staging-env.yaml"
$providerVersion = "<numeric-version>"
$saltVersion = "<numeric-version>"
$historyVersion = "<numeric-version>"
gcloud run deploy $service --image=$imageDigest --region=$region --project=$projectId --service-account=$runtimeSa --cpu=1 --memory=1Gi --min=0 --max=1 --concurrency=4 --timeout=60s --port=8080 --env-vars-file=$settingsFile --update-secrets="WORKERS_AI_API_TOKEN=workers-ai-token:$providerVersion,TELEMETRY_SALT=telemetry-salt:$saltVersion,HISTORY_KEY=history-key:$historyVersion" --startup-probe="httpGet.path=/v2/ready,initialDelaySeconds=0,periodSeconds=10,timeoutSeconds=5,failureThreshold=24" --liveness-probe="httpGet.path=/v2/live,periodSeconds=30,timeoutSeconds=5,failureThreshold=3" --no-allow-unauthenticated
```

This is a **trial template**, not a claim of staging's exact resources. 1 CPU/1 GiB/concurrency 4/request 60 s come from the design trial; measure them. Recorded facts are min 0/max 1, one worker and a four-minute startup allowance.

| Flag | Meaning |
|---|---|
| `--image` | Exact content digest to execute |
| `--region`, `--project` | Execution location and project |
| `--service-account` | Identity used by Python Google clients |
| `--cpu`, `--memory` | CPU/RAM allocation per instance |
| `--min=0`, `--max=1` | Service-level scaling limits; allow idle scale-to-zero and bound normal scale-out |
| `--concurrency=4` | Maximum requests routed concurrently to one instance, not four Python worker processes |
| `--timeout=60s` | Server request deadline; it does not extend Android's request timeout |
| `--port=8080` | Container listening port, passed as PORT |
| `--env-vars-file` | Load the complete non-secret environment file; check existing settings before replacing |
| `--update-secrets` | Map each environment name to a secret:numeric-version reference; preserve other mappings |
| `--startup-probe` | Wait for artifact readiness before treating startup as successful |
| `--liveness-probe` | Detect a nonresponding process; never use paid LLM calls here |
| `--no-allow-unauthenticated` | Require Google IAM invocation; this is separate from app sign-in |

For probe fields, httpGet.path is the GET URL; initialDelaySeconds delays the first check; periodSeconds is interval; timeoutSeconds is per-check limit; failureThreshold is consecutive failures. 24 × 10 gives a 240-second configured startup window. A four-minute probe window is not a promise every boot fits mobile timeouts. [Health checks](https://docs.cloud.google.com/run/docs/configuring/healthchecks), [deploy flags](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy).

The service max is a scaling guard, not a hard cost cap or a substitute for race-safe account counters. Budget, provider quota, storage/build/log costs and revision overlap still need review.

## 8. Choose how a phone reaches staging

Private IAM staging works through a developer proxy, but the current Android app does not obtain Google IAM identity tokens. It uses the application's bearer session. These are two different gates.

Only after verifying AUTH_REQUIRED/safety/consent and smoke checks, an authorized owner can use this **optional access-change template**:

```powershell
gcloud run services add-iam-policy-binding $service --member="allUsers" --role="roles/run.invoker" --region=$region --project=$projectId
```

This allows the public internet to reach the service's HTTP handler; data routes still require app sessions/consent. `allUsers` is everyone, `run.invoker` is permission to invoke. Organization policy may forbid it. The tracker records public-URL testing 15 October, but this exact IAM command is not recorded history.

Next: [verify the API, build staging Android and rehearse recovery](hosting-interview-operations.md).

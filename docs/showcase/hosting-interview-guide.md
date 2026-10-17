# Hosting Interview Guide — From Android to Cloud

[Interview questions](interview-guide.md) · [Cloud commands](hosting-interview-cloud.md) · [Operate and verify](hosting-interview-operations.md)

For an Android developer learning backend/AI hosting. Updated 18 October 2026. This is an explanation and a set of **command templates**, not a transcript of commands run for this documentation update.

## 1. What actually moves off the laptop?

An APK is installed on a phone. The backend is a long-running program listening for HTTP requests. Hosting puts that program on a computer managed by a provider so another phone can reach it over HTTPS while your laptop is off.

| Familiar Android idea | Equivalent here |
|---|---|
| APK plus resources | Container image plus bundled model/data/index |
| Install an APK | Deploy an image as a Cloud Run revision |
| Application process | Container instance running one Uvicorn worker |
| Build variant | Separate staging service and Android staging flavor |
| App version | Code release, image digest, snapshot ID and model version: separate identities |
| SharedPreferences | Local configuration only; server accounts need durable Firestore |
| Remote API key | Backend Secret Manager reference, never a value inside the APK |

The flow is:

```text
Android -> HTTPS -> Cloud Run /v2 -> FastAPI services
                                  |- XGBoost + SHAP + Dixon-Coles (CPU)
                                  |- NumPy retrieval index (in memory/files)
                                  |- Firestore (accounts, sessions, opted-in questions)
                                  |- Workers AI (guard, query embeddings, generation)
```

Cloud Run runs our Python code. Cloudflare runs the hosted LLM/embedding weights. A saved embedding index does not remove the need to embed each new retrieval query with the same model.

Local mode keeps Ollama and JSON accounts. No Kubernetes, managed vector database or always-on GPU is needed. [ADR 025](../adr/025-cloud-serving-on-cloud-run.md), [ADR 026](../adr/026-firestore-account-store.md).

## 2. What has actually been recorded?

Use these as dated project evidence, not a claim that cloud state was queried today.

| Evidence | Recorded fact | What it does not prove |
|---|---|---|
| [Execution tracker](../plans/hosting-execution-tracker.md) | First private staging deploy 14 October from v2.2.0; min 0/max 1, one worker, refresh off, four-minute startup probe | Full deployment command history or current capacity |
| Same tracker | v2.5.0 deployed 15 October using Cloud Build; sign-in, consent, predict, signed follow-up and forged history checked through public URL | An automated staging evaluation gate |
| Same tracker | v2.6.0 deployed 17 October: image tag `da8a236`, revision suffix 00005, ready 200 and health version 2.6.0/assistant on | Tag is not a full immutable SHA256 digest |
| Same tracker | `da8a236`, `a2afef3`, `ec72966` retained; first 14 October image removed | Which retained revision is currently safe to roll back to |
| Same tracker | `staging_questions` TTL ACTIVE 17 October | Immediate deletion exactly 90 days after creation |
| Supplied private runbooks (14/17 October) | Staging URL, project/registry/runtime identity and recorded deployment instructions; copied into a private local command reference | A command transcript, current effective configuration or the live full image digest |
| [Hosted eval report](../reports/hosted-assistant-evals.md) | Hosted provider exercised from developer machine; separate 555-chunk, 1,024-dimensional index, cutoff 0.77 | Evals against deployed staging |
| [Tracker](../plans/hosting-execution-tracker.md) | ₹500 monthly whole-billing-account budget, thresholds 50/90/100/150%; budget alert test pending | A hard spending cap |
| [Baseline](../reports/hosting-baseline.md) | Historical local image 2.44 GB; one cloud startup-to-ready sample 19 s in tracker | Cold-request/warm p95 or SLA |

The three supplied private runbooks have now been read. Their dated command blocks and step-by-step flag explanations are saved locally in docs/prompt-book/staging-command-reference.md and staging-command-reference-flags.md (Git-ignored). They identify the project, registry and runtime identity; the live full image digest remains absent. Public examples below keep placeholders. Recorded instructions establish what was prescribed; the dated tracker/release records establish which outcomes were reported. No cloud command was executed for this documentation update.

## 3. Read the identities before touching cloud resources

- **Project ID** is the human-readable API identifier; **project number** is numeric. Do not invent one from the other.
- **Region** chooses where Cloud Run executes; recorded staging isMumbai, `asia-south1`. Firestore/registry locations need their own verification.
- **Image tag** is a convenient label. A **digest** identifies exact image content.
- **Snapshot ID** identifies bundled model/data/index content. A new image can carry the same snapshot.
- **Prediction model version** names the trained XGBoost artifact. It is independent of app release 2.6.0.
- **Service account** is the backend process's Google identity. It is different from your human deployer identity and the Cloud Build identity.

**Shell convention:** every executable block here is PowerShell. Run from the specified directory. `<...>` means substitute a verified value; never run a block with placeholders. `$env:NAME` sets an environment variable for that terminal and child processes. These examples are not executed by reading the guide.

## 4. Prepare the real artifacts locally

A Git checkout lacks ignored models, match files and vector indexes. Cloud Run cannot invent them. First restore trusted existing artifacts, or reproduce them with the [quick start](../setup/quick-start.md). Do not retrain just because the cloud checkout is empty.

From repository root:

```powershell
Set-Location ai
uv sync --frozen --extra dev
uv run pytest -m "not integration"
```

`Set-Location` changes directory. `uv sync` installs dependencies; `--frozen` uses the existing lock without rewriting it; `--extra dev` includes test/lint tools. `uv run` selects that environment. Pytest's `-m` selects a marker expression; this excludes artifact/network integration tests until their prerequisites are available.

To reproduce historical preparation, these are **templates**, not a required deploy-time retrain:

```powershell
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
uv run python -m feature_engineering.pipeline --input <canonical-results.csv> --output-dir ../datasets/features/top5
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --max-depth 3 --learning-rate 0.03 --n-estimators 400 --no-promote
```

| Argument | Simple meaning |
|---|---|
| Python `-m package.module` | Run a module as a program, with imports resolved from ai |
| `--base-dir` | Dataset root; raw/processed folders live below it |
| `--confirm` | Actually download/write; these refresh/backfill CLIs otherwise print a dry run |
| `--input`, `--output-dir` | Canonical CSV to read and feature output folder |
| `--feature-matrix` | Parquet matrix used by training |
| `--split-strategy season` | Whole-season evaluation boundaries |
| `--val-seasons` | Data used to select stopping/configuration |
| `--test-seasons`, `--holdout-seasons` | Later evaluation seasons |
| `--max-depth` | Maximum complexity of each tree |
| `--learning-rate` | Contribution from each boosting step |
| `--n-estimators` | Upper bound of boosting trees before early stopping |
| `--no-promote` | Save a candidate run without replacing latest/registry serving choice |

Review the reports before promotion. Frozen reporting run `20260928_123224` selected 168 trees; serving refit `20261007_154105` trained through 2025/26. The [refit report](../reports/refit-all-seasons.md) records its separate backtest and reproduction commands. Training completion alone is not a promotion gate.

Download current played results/fixtures before making a new serving snapshot:

```powershell
uv run python -m scripts.refresh_live_dataset --confirm
uv run python -m scripts.refresh_fixtures --confirm
```

Both validate and create versioned CSV outputs. Without `--confirm`, no download/write occurs. Preserve the previous validated files; never edit an old raw partition to “fix” its history.

## 5. Build the hosted embedding index and evaluate

Put the scoped Workers AI token/account ID in ignored `ai/.env`, using the owner-approved secret workflow. Do not paste them into a recorded terminal, Git or APK. The provider settings are documented in [ai/.env.example](../../ai/.env.example).

The **recorded Bash command** in the hosted eval report used `ASSISTANT_PROVIDER=workers_ai VECTOR_STORE_PATH=...`. Below is its **PowerShell equivalent**, with both the standalone pipeline setting and backend setting explicit:

```powershell
$env:ASSISTANT_PROVIDER = "workers_ai"
$env:WORKERS_AI_THINKING = "false"
$env:VECTOR_STORE_PATH = "assistant/vector_store_workers_ai"
$env:ASSISTANT_VECTOR_STORE_PATH = "assistant/vector_store_workers_ai"
$env:LIVE_REFRESH_HOUR = "off"
uv run python -m assistant.pipeline --rebuild --min-relevance 0.77
uv run python -m evaluation.relevance_cutoff
```

`VECTOR_STORE_PATH` is read by standalone AssistantSettings; `ASSISTANT_VECTOR_STORE_PATH` is read by backend Settings/snapshot builder. They must point to the same hosted index. Current source does not alias the two.

`--rebuild` regenerates document vectors; `--min-relevance` stores the retrieval threshold with the model metadata.0.77 is recorded for the earlier hosted corpus, not a universally correct value. Recheck cutoff separation whenever documents/model change. Both indexing and query evaluation call Cloudflare and consume quota.

For the existing local TestClient evaluation CLIs, isolate local auth/account state:

```powershell
$env:AUTH_REQUIRED = "false"
$env:ACCOUNT_STORE = "json"
$env:ASSISTANT_SAFETY = "true"
uv run python -m evaluation.assistant_grounding --per-league 2
uv run python -m evaluation.assistant_abstention
uv run python -m evaluation.assistant_season
uv run python -m evaluation.assistant_conversation
```

`--per-league 2` selects two grounding fixtures per league plus the unsupported-team case. No other flags are needed here. These CLIs launch a **local** app with the hosted provider; they do not accept a staging URL flag. Save dated output, provider/index/model settings and case counts. Safety should be on for representative hosted testing; these test accounts are local, not real beta users. Restore the deployment configuration separately.

## 6. Freeze and verify the snapshot

```powershell
uv run python -m scripts.build_snapshot --out ../snapshot
uv run python -m scripts.build_snapshot --verify ../snapshot
```

`--out` copies selected serving files into a new/empty folder and writes manifest.json. `--verify` checks listed paths, bytes and SHA256. A nonempty destination is refused; retain old snapshots elsewhere rather than overwriting them.

Snapshot builder reads backend settings, so ensure the hosted index path/model/registry/data are correct. It includes the configured v1 artifact even when cloud auth disables v1 routes; that trusted source file must exist. `--no-index` exists for assistant-off snapshots, not a shortcut for assistant-on deployment.

Joblib can execute code while loading. Only package trusted artifacts. Hash verification protects consistency relative to the manifest, not authenticity of an untrusted artifact+manifest pair.

## 7. Understand the Dockerfile before cloud deployment

[Dockerfile](../../Dockerfile) uses Python 3.12.11, frozen uv dependencies and libgomp1 for XGBoost. It copies code, schemas and the snapshot, compiles Python and verifies the snapshot at build time. Runtime uid 10001 cannot modify root-owned code/artifacts.

One Uvicorn worker listens on PORT 8080; container defaults turn live refresh and assistant off. Deployment enables the hosted provider, auth, safety and secret references explicitly. Readiness checks artifacts, never remote generation. It does not train/download/re-index at startup.

Next: [create identities, build the image and deploy staging](hosting-interview-cloud.md).

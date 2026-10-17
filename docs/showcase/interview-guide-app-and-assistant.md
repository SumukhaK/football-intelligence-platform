# Interview Guide — Assistant, API and Android

[Questions 1–28](interview-guide.md) · [Hosting walkthrough](hosting-interview-guide.md)

Updated for v2.6.0 on 17 October 2026. Distinguish implemented behavior, dated experiments and planned operations.

## RAG and assistant

### 29. Why RAG instead of an LLM alone?

**Answer:** The model does not inherently know this app's current data or training results. Retrieval supplies relevant project documents; tools supply fixture/prediction/season numbers from the same services used by the API.

**Trade-off:** Retrieval and tools reduce fabrication risk but do not guarantee every sentence is true. Source quality, routing, prompts and evaluations still matter.

### 30. Why Ollama, and what runs in the cloud?

**Answer:** Local mode uses qwen2.5:7b-instruct and nomic-embed-text through Ollama. Hosting uses Cloudflare Workers AI: Gemma 4 26B with thinking off and Qwen3 embedding 0.6B. Cloud Run hosts FastAPI and CPU prediction code, not that LLM's weights.

**Why:** Local development remains possible without a paid API. Hosted inference makes the beta reachable while my laptop is off.

**Trade-off:** Local and hosted quality/latency/cost differ; switching providers also requires compatible embeddings and evaluation. [ADR 025](../adr/025-cloud-serving-on-cloud-run.md), [provider report](../reports/hosted-assistant-evals.md).

### 31. Why NumPy rather than a managed vector database?

**Answer:** The recorded hosted index had 555 chunks. Brute-force cosine search is simple and small enough for this corpus; an extra database would add operations without demonstrated benefit.

**Trade-off:** Search is linear in chunk count. An ANN index becomes a measured option if corpus/latency grows. Firestore is used for accounts, not vector search.

### 32. How do you reduce hallucination?

**Answer:** Retrieve relevant documents with a measured cutoff, constrain the prompt, call prediction/season tools for numbers, bound tool rounds and retry a follow-up once if its numbers fail the deterministic check. Signed history is context rather than trusted new evidence.

**Limits:** The numeric checker is not full semantic faithfulness: a number can be supported but attached to the wrong claim, and the retry is not recursively validated. Safety classification is a separate check for harmful intent. [Assistant service](../../ai/assistant/services/assistant_service.py), [ADR 030](../adr/030-short-term-chat-memory.md).

### 33. What happens during a provider outage?

**Answer:** Chat returns a structured 503 while independent prediction/SHAP/fixtures routes remain usable if their artifacts loaded. Workers AI calls have per-attempt timeouts and at most one retry. Liveness/readiness never invoke the provider.

**Trade-off:** Multiple safety/embedding/generation stages can exceed one 20-second attempt; there is no single shared end-to-end chat deadline. Do not claim every answer fits the phone budget merely because one evaluation did. [Workers adapter](../../ai/assistant/workers_ai.py).

### 34. What do your assistant evals prove?

**Answer:** Dated provider experiments record abstention 20/20, numeric grounding 11/11, season 7/7 and conversation 8/8 on 15 October. The v2.6.0 release records conversation 9/9 after the favourite-team case. Those are finite scripted checks.

**Limits:** The CLIs construct a local FastAPI TestClient with the configured real provider; they are not automatically staging-URL tests. Full retrieval precision/semantic faithfulness and a staging release gate remain pending. [Hosted evals](../reports/hosted-assistant-evals.md), [v2.6.0](../releases/v2.6.0.md).

### 35. Why chunk documents?

**Answer:** A long document may contain one useful paragraph. Chunking makes retrieval return focused context rather than diluting the embedding with unrelated sections. Current defaults are 600-character chunks with 80-character overlap.

**Trade-off:** Boundaries can split meaning and overlap repeats tokens. Chunk size is a configuration choice to evaluate, not a universal optimum. [Settings](../../ai/assistant/configuration.py).

### 36. Why must embedding models match?

**Answer:** Document and query vectors must use the same embedding space. Local nomic and hosted Qwen indexes are separate; backend loading rejects a model mismatch. The recorded hosted cutoff 0.77 was measured separately from local 0.81.

**Trade-off:** Similar dimensions do not make different models compatible. Rebuild and remeasure when model/corpus changes. Current backend answers strip citations and return an empty sources list; provenance is retained in telemetry rather than shown as citations in the app. [Chat service](../../ai/backend/app/services/chat_service.py), [ADR 029](../adr/029-assistant-sources-logged-not-shown.md).

## Backend

### 37. Why FastAPI?

**Answer:** Pydantic request/response models, dependency injection and generated OpenAPI fit this API. Thin routers call services; blocking chat is a plain def so FastAPI runs it in a worker thread rather than blocking the event loop.

**Trade-off:** Generated docs still depend on accurate declared schemas/error descriptions. A framework does not automatically make the implementation nonblocking or scalable.

### 38. What happens on startup?

**Answer:** Lifespan loads models, SHAP, history, goals, fixtures, season services and optional assistant components. Isolated load failures leave relevant services unavailable. /v2/live is cheap process health; /v2/ready checks required artifact-backed components; /v2/health supplies diagnostics.

**Trade-off:** A health response saying ok is not evidence all components or the remote provider work. [Loaders](../../ai/backend/app/loaders.py), [readiness](../../ai/backend/app/services/readiness.py).

### 39. Why lifespan dependency injection?

**Answer:** Models and data are loaded once into app.state; Depends exposes those services to routes. Tests can override dependencies. Loading a model/explainer inside each request would repeat expensive I/O and setup.

**Trade-off:** Shared services need concurrency/lifecycle discipline. The current refresh reload changes individual components, not an atomic complete service bundle.

### 40. How are malformed requests handled?

**Answer:** Pydantic validates shape and constraints before service work, returning 422 field details. Services validate domain rules such as known league/team/features; typed exceptions map to structured status codes.

**Trade-off:** Standard FastAPI validation uses detail lists; not every error has the custom error/detail string shape. Avoid exposing tracebacks or credentials.

### 41. What distinguishes 422 from 503?

**Answer:** 422 indicates invalid request/domain input;503 means required service/artifact/provider unavailable. The client should correct input for the former and offer a bounded retry/readable unavailable state for the latter.

**Trade-off:** Blindly retrying all failures wastes quota and can repeat writes. Android retries selected GET failures and distinguishes hosting-platform HTML 429 from backend JSON 429.

### 42. How can you test without trained artifacts?

**Answer:** FastAPI TestClient contract tests inject fakes/mocks for routes; separate integration tests use real trained artifacts. Numerical unit tests may train small seeded models. Provider tests use fake transport, while explicit assistant eval CLIs spend real provider quota.

**Limits:** Some integration checks require local artifacts/network. Historical counts are version-specific, and reading tests is not running them. [Test suite](../../ai/tests/), [baseline](../reports/hosting-baseline.md).

### 43. How is authentication implemented?

**Answer:** Invite-only accounts use scrypt password hashes, hashed opaque 30-day session tokens, lockout and versioned consent. AUTH_REQUIRED=true protects v2 data routes and removes legacy v1/unversioned data aliases; health/probes/auth entry routes remain open. Android signs in even in local mode.

**Cloud:** Firestore Native mode stores accounts/invites/sessions; local mode uses JSON. Runtime credentials come from the Cloud Run service account, not an APK key. Opted-in questions are stored separately with 90-day expires_at; TTL must be enabled. [ADR 026](../adr/026-firestore-account-store.md), [ADR 034](../adr/034-storing-opted-in-question-text.md).

### 44. What would break first under more traffic?

**Answer:** The beta intentionally starts with one instance/worker. Rate limiting is process-local, Firestore counter writes are not full transactional updates, and chat consumes provider quota and worker time. Shared account storage and HTTPS already exist for hosting; those are not future work.

**Next:** Measure concurrency, use transactions/shared limits before increasing replicas, enforce user/global budgets, and complete staging evals/recovery drills. A max-instance setting is not a hard spending cap. [Tracker](../plans/hosting-execution-tracker.md).

## Android

### 45. Why Compose Multiplatform?

**Answer:** Kotlin/Compose fits my Android experience and keeps UI/state/repository code organized for potential reuse. The current Gradle configuration has only an Android target.

**Trade-off:** I would not claim an iOS app exists or that KMP guarantees better performance than alternatives. A new platform still needs its own lifecycle, networking and packaging work.

### 46. Why ViewModels in androidMain?

**Answer:** That is this project's chosen source-set boundary: Android lifecycle ViewModels and DI live there; UI/state/repository contracts mostly live in commonMain. It avoids introducing a platform abstraction without a second platform requirement.

**Trade-off:** Do not justify the choice with a blanket claim that modern AndroidX lifecycle has no multiplatform support. Describe the actual pinned project and implementation.

### 47. How is prediction state shared across screens?

**Answer:** Result and Explain obtain PredictionViewModel using the Prediction back-stack entry as ViewModelStoreOwner. They reuse the same instance rather than repeat requests or copy prediction state.

**Trade-off:** Back-stack lifetime matters. Result remembers the last drawn state while exiting so reset-to-Idle does not flash an error. [Navigation](../../frontend/app/src/main/kotlin/com/footballintelligence/app/AppNavigation.kt).

### 48. Does Android compute the 42 features?

**Answer:** No. It sends home/away team names and league; server-side history creates the same pinned features used in training. Android displays outcomes, optional insights and a separate explanation.

**Trade-off:** New predictions need the API. The offline cache only replays saved successful responses on connectivity failure; it does not conceal server rejection and never caches chat.

### 49. What do repository tests verify?

**Answer:** Most MockK repository tests assert forwarding and success/error pass-through over FootballApiService. TeamRepository also tests fixture filtering and cached timestamp preservation. Ktor MockEngine tests separately check JSON/HTTP/auth/retries.

**Trade-off:** Repositories generally do not catch arbitrary thrown exceptions or invent new mappings. Mocks do not prove live networking, device behavior or all race conditions; there is no frontend coverage gate/device CI job.

### 50. What would you do in another two weeks?

**Answer:** Complete the staging app/eval walkthrough and cold/warm measurement first, then rehearse rollback and provider/data failures. Add meaningful quality/freshness monitoring and a release gate before wider usage.

**Why:** Download/provider retries already exist. Budgets, answer cache, production promotion and unattended snapshot publishing remain unfinished; choose the next task from the tracker rather than claiming they are deployed.

[Back to questions 1–28](interview-guide.md) · [Hosting walkthrough](hosting-interview-guide.md)

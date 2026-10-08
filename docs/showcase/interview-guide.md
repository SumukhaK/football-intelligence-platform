# Interview Guide — Football Intelligence Platform

50 questions an interviewer might ask about this project (as of release v2.1.0 and the work merged since), organised by topic, each with a suggested answer, the reasoning behind it, and the trade-offs worth raising proactively.

---

## Data & Feature Engineering

### 1. Why did you split the data by season instead of randomly?

**Answer:** Because the features are rolling-window statistics (form, goals, Elo) computed from a team's prior matches. A random split would let the model train on matches that come *after* some test matches, and their features carry information across time, which is leakage. The model splits by whole seasons: train 2000/01–2021/22, validate 2022/23, test 2023/24, and keep 2024/25–2025/26 as an untouched holdout.

**Reasoning:** This is the most common bug in time-series ML projects, and it inflates test metrics in a way that doesn't show up unless you check for it. Whole seasons also keep league tables and team lists intact.

**Trade-off:** The test set is necessarily the most recent season, which can differ from older ones. The two holdout seasons and a live 2026/27 check guard against a single lucky season. Documented in [ADR 007](../adr/007-season-based-split-and-evaluation.md), which replaced the earlier 70/15/15 chronological split of [ADR 003](../adr/003-chronological-train-val-test-split.md).

---

### 2. How do you prevent leakage in the rolling-window features specifically?

**Answer:** Every rolling feature generator applies `.shift(1)` before computing the window, so a match's features are always built from strictly prior matches, never including the match itself.

**Reasoning:** Without the shift, a 5-match rolling average computed "as of" match N would include match N's own result.

**Trade-off:** This means the very first few matches of a season have sparse or default-value features (no history yet) — filled with training-set medians rather than dropping early-season rows.

---

### 3. Why 42 features specifically — how did you choose them?

**Answer:** They span six categories: rolling form (wins/points, last 5 and last 10), goal statistics (scored/conceded/differential), win percentage and points-per-game, rest days, head-to-head history, league position/points, and Elo ratings (including average opponent Elo faced). Each category captures a different signal: recent form, scoring ability, fatigue, historical matchup, table position, and team strength.

**Reasoning:** Breadth across categories rather than depth in one — avoids overfitting to a single signal type.

**Trade-off:** Many features are correlated (form, goals and Elo overlap). With 39,627 training matches that's fine for a tree model, and SHAP still attributes the prediction fairly across them.

---

### 4. What is Kahn's algorithm doing in your feature pipeline and why do you need it?

**Answer:** Some feature generators depend on outputs of other generators (e.g., a feature that uses Elo needs Elo to be computed first). The `FeatureRegistry` builds a dependency graph between generators and topologically sorts it with Kahn's algorithm so they always run in a valid order, regardless of how they were registered.

**Reasoning:** Without explicit ordering, adding a new generator that depends on an existing one would silently break if registered before its dependency.

**Trade-off:** Adds a small amount of upfront complexity versus just hardcoding generator order — but makes the registry safely extensible.

---

### 5. Why football-data.co.uk and not a richer source like FBref or Understat?

**Answer:** football-data.co.uk gives clean, structured match-result CSVs with minimal preprocessing needed, and covers all five leagues from 2000/01 onwards in one consistent format (46,709 matches, [ADR 005](../adr/005-top-five-leagues-multi-source-data.md)). That kept the pipeline focused on correctness rather than fighting messy HTML scraping. The provider abstraction (`DatasetDownloader`/`DatasetStorage`) was built to support FBref and Understat too — those providers exist in the codebase — but football-data.co.uk was used for the canonical dataset.

**Reasoning:** Get a correct, validated pipeline working end-to-end first; richer data sources are a drop-in extension, not a redesign.

**Trade-off:** football-data.co.uk lacks advanced metrics like xG. xG, FIFA ratings and Champions League rest days from Kaggle were tested and none improved log loss beyond noise ([report](../reports/kaggle-extras.md)).

---

### 6. How do you validate data quality before it enters the pipeline?

**Answer:** `DatasetValidator` enforces 9 explicit rules (e.g., valid date ranges, non-negative goal counts, valid team names, no duplicate matches) before any data is marked "processed." Validation failures are loud errors, not silently skipped rows.

**Reasoning:** Per the project's data engineering philosophy: "data quality failures are loud errors, not silent skips" — silent skips hide problems until they surface much later as model quality issues.

**Trade-off:** Stricter validation means a single bad row can halt the whole pipeline run rather than degrading gracefully — an intentional choice: each league season is its own file, so a failure names the exact file and reason, and fixing it is cheap. Season-integrity checks also verify team counts, double round robins and results matching the score.

---

### 7. Why Parquet over CSV for processed data?

**Answer:** Parquet preserves types (dates, floats) without re-parsing, is columnar (faster for the read patterns used by feature engineering), and is versioned alongside the code that produced it per the project's data engineering conventions.

**Reasoning:** CSV round-trips lose type information (a date becomes a string) and are slower to read repeatedly during pipeline iteration.

**Trade-off:** Parquet isn't human-readable in a text editor the way CSV is — mitigated by keeping raw CSVs as the immutable source of truth.

---

### 8. How did you scale this to a multi-season dataset?

**Answer:** Version one covered one Premier League season. Version two backfills 26 seasons of five leagues (46,709 matches). The main change was Elo: ratings now carry across seasons per league, regressed a third of the way back to 1500 between seasons, and promoted teams start at the average of the teams they replaced. League position and rest days were also made season-aware.

**Reasoning:** Data volume was the biggest lever: this change improved log loss far more than any tuning.

**Trade-off:** Elo pools are per league, so ratings aren't comparable across leagues; the model only compares teams within a league.

---

### 9. What would you do differently if the dataset were 100x larger?

**Answer:** Parquet plus pandas would start to strain; I'd look at Polars or a proper feature store, and the brute-force numpy vector store for RAG would need to become an approximate-nearest-neighbour index (e.g., FAISS or HNSW). The season-split methodology and leakage prevention would not need to change.

**Reasoning:** The architecture is sized appropriately for ~47,000 matches; scaling decisions are about swapping implementations behind the same interfaces, not redesigning the pipeline.

---

### 10. How is feature engineering tested?

**Answer:** Each of the 9 generators has dedicated unit tests verifying both correctness (e.g., rolling average computed correctly) and leakage prevention (a feature for match N must not change if match N+1's data changes). Dozens of tests cover this stage.

**Reasoning:** Leakage bugs don't show up as test failures unless you specifically assert that future data doesn't affect past features — so leakage tests are written as a distinct test category, not bundled into correctness tests.

---

## Model Training & Evaluation

### 11. Why XGBoost over a neural network or logistic regression?

**Answer:** Tabular data (39,627 training rows × 42 features) is exactly XGBoost's strength — it typically matches or beats neural nets on tabular data, trains in minutes on a CPU, and has native, exact SHAP support via `TreeExplainer`. A neural net would need far more data to justify its added complexity and would lose the exact-explainability property.

**Reasoning:** Documented in [ADR 001](../adr/001-use-xgboost-for-predictions.md) — match outcome prediction at this scale and feature mix doesn't benefit from deep learning's representation-learning advantages.

**Trade-off:** XGBoost can't learn from raw unstructured inputs (e.g., player tracking video) the way a neural net could — irrelevant here since the input is already structured tabular data.

---

### 12. Why `multi:softprob` instead of treating this as three binary classifiers?

**Answer:** `multi:softprob` natively models the three mutually exclusive, collectively exhaustive outcomes (H/D/A) as a single softmax, producing probabilities that sum to 1.0 by construction. Three independent binary classifiers would need post-hoc renormalisation and lose the natural constraint.

**Reasoning:** The 3-way structure of football outcomes maps directly onto a multi-class objective.

---

### 13. What's your model's accuracy, and is that good?

**Answer:** 52.5% accuracy and a log loss of 0.976 on the 2023/24 test season (random baseline 33.3%; always picking the home team 43.1%; bookmakers 55.0% and 0.955). On 250 real 2026/27 matches played up to 20 September 2026 it scored 52.4%, against 51.6% for bookmaker favourites. ROC AUC is 0.679. That's realistic: football is very random, and the market, with inside information, is the practical ceiling.

**Reasoning:** I'd rather state this honestly than oversell it, and I report log loss because the app shows probabilities, so they must be trustworthy, not just the top pick.

**Trade-off:** Higher accuracy needs richer data (lineups, injuries, xG). The model never picks a draw, because draw probabilities are calibrated but flat; the app shows a "draw possible" tag instead ([ADR 011](../adr/011-draw-possible-tag.md)).

---

### 14. Why early stopping, and on what metric?

**Answer:** Early stopping on the validation set's multi-class log-loss halts training once additional boosting rounds stop improving generalisation, preventing the model from overfitting to training-set noise.

**Reasoning:** Early stopping on the 2022/23 season stopped the model at round 167 of up to 400; it's a cheap, standard guard against overfitting.

---

### 15. Walk me through your cross-validation strategy.

**Answer:** Season walk-forward cross-validation with 5 folds: train on all seasons up to year N and validate on season N+1, then move forward one season. It's used on training seasons only to tune hyperparameters, so the test and holdout seasons stay untouched. Result: 51.9% ± 1.0% accuracy, log loss 0.994 ± 0.007.

**Reasoning:** Standard k-fold would shuffle and leak future information into training folds, the same issue as a random train/test split.

---

### 16. How is the trained model versioned and made reproducible?

**Answer:** `models/registry.json` records every training run with its version (timestamp-based), the producing git commit hash, framework versions (xgboost, scikit-learn, pandas, etc.), the source dataset version, and evaluation metrics. `models/latest/` symlinks (via copy) to the current best run; every run's artifacts persist under `models/runs/<timestamp>/`.

**Reasoning:** Any prediction served in production can be traced back to the exact code, data, and dependency versions that produced its model — essential for debugging and auditability.

**Trade-off:** The registry currently stores a Windows absolute path for `run_dir`, which isn't portable across machines — a known, documented limitation.

---

### 17. Why joblib instead of pickling the model directly, or ONNX?

**Answer:** joblib is the scikit-learn ecosystem's standard for serialising models with large numpy arrays efficiently, and XGBoost's sklearn-API wrapper serialises cleanly through it. ONNX would add cross-framework portability we don't need (we're not deploying to a non-Python runtime), and raw pickle has worse compression and security implications for sharing artifacts.

**Reasoning:** [ADR 002](../adr/002-joblib-model-serialization.md) — match the serialisation choice to actual deployment needs, not hypothetical future ones.

---

### 18. How would you detect model drift in production?

**Answer:** Not implemented here (no live production deployment), but the architecture supports it: the model registry already tracks evaluation metrics per version, so a drift-detection job could periodically re-evaluate the live model against newly completed matches and compare metrics against the registered baseline, triggering retraining if metrics degrade beyond a threshold.

**Reasoning:** Honest about what's built versus what's designed-for-but-not-implemented — the registry's structure was deliberately built to make this extension straightforward.

---

### 19. What hyperparameters did you tune, and how?

**Answer:** A grid of 27 settings (depth, learning rate, number of trees), scored by season walk-forward cross-validation on training seasons only. The top ten settings were within 0.0006 log loss of each other, so the choice is stable. Winner: depth 3, learning rate 0.03, up to 400 rounds, with early stopping.

**Reasoning:** Tuning on the test season would overfit the evaluation itself. The small spread between settings also shows that data and features matter far more than tuning here.

---

### 20. If you saw the model start predicting "Home Win" for almost everything, how would you debug it?

**Answer:** First check class balance in the training data (home wins are the most common outcome in football generally, so some bias toward H is expected and even correct). Then check feature importance/SHAP summary for the home-win class to see if one feature (e.g., home advantage proxy) is dominating. Then verify the chronological split and `.shift(1)` leakage prevention are still intact — a leakage regression could cause the model to over-rely on a feature that's trivially predictive due to leaked information.

**Reasoning:** Demonstrates a structured debugging process: data distribution → model internals (SHAP) → pipeline correctness, in that order.

---

## Explainability (SHAP)

### 21. Why SHAP over LIME?

**Answer:** SHAP's `TreeExplainer` computes *exact* Shapley values for tree ensembles in polynomial time, using the model structure directly. LIME approximates explanations by perturbing inputs and fitting a local surrogate model — it's model-agnostic but approximate and can be unstable across runs for the same input.

**Reasoning:** [ADR 004](../adr/004-shap-for-explainability.md) — since the model is a tree ensemble, there's no reason to accept LIME's approximation when an exact, faster method exists.

**Trade-off:** SHAP `TreeExplainer` is tied to tree-based models; if the model architecture changed to a neural net, a different SHAP explainer variant (or LIME) would be needed.

---

### 22. What exactly does a SHAP value mean here?

**Answer:** For a given prediction and a given feature, the SHAP value is that feature's contribution (in log-odds/probability space, depending on normalisation) to moving the prediction away from the model's average/base output, computed via a game-theoretic fair-attribution method (Shapley values from cooperative game theory).

**Reasoning:** Concretely: a positive SHAP value for `home_elo_before` means that specific match's home Elo rating pushed the prediction toward the predicted outcome more than the average match would.

---

### 23. How do you handle SHAP for a multi-class model?

**Answer:** XGBoost's multi-class output produces a SHAP tensor of shape `(n_samples, n_features, n_classes)` — one SHAP value per feature *per class*. The `ExplanationService` normalises this and extracts the contributions for whichever class was actually predicted, so `POST /explain` returns attribution relevant to the specific predicted outcome.

**Reasoning:** Without this normalisation, you'd have three sets of SHAP values per prediction and no clear way to decide which is "the" explanation.

---

### 24. Why do you cache the explainer per model version?

**Answer:** Building a `TreeExplainer` involves parsing the full tree structure of the trained model, which has measurable cost. `ExplainerCache` keeps one explainer instance per model version in a class-level dict, so it's built once at first use and reused for every subsequent `/explain` call against that model version.

**Reasoning:** Without caching, every API request would pay the explainer-construction cost — unacceptable for a latency-sensitive endpoint.

**Trade-off:** The cache grows with the number of distinct model versions served in a process lifetime — acceptable since a typical deployment serves one model version at a time and restarts on model updates.

---

### 25. What's the latency of generating an explanation, and why does that matter?

**Answer:** About 7 ms for the core SHAP computation and under 30 ms end-to-end, measured on the v1.0.0 model (Stage 12). The current model is similar in size, and the server now also builds features from history per request, which is still well under a second. It matters because explainability is exposed as a real-time API endpoint consumed by a mobile app — if it took seconds, it couldn't be a synchronous part of the user-facing prediction flow.

**Reasoning:** This is the direct payoff of treating explainability as a product feature with a latency budget, not an offline analysis step.

---

### 26. How would you explain a SHAP waterfall plot to a non-technical stakeholder?

**Answer:** Start from the model's average prediction across all matches, then show each feature as a bar that pushes the prediction up or down from that baseline, in order of impact, until you arrive at this specific match's final predicted probability. It's a running tally of "why this match's prediction differs from the average match's prediction."

**Reasoning:** Demonstrates the ability to translate a technical explainability method into stakeholder-friendly language — a real skill gap in many ML engineers.

---

### 27. What are the limitations of SHAP that you'd flag to a stakeholder?

**Answer:** SHAP explains what the *model* learned, not necessarily true causal relationships in football — a feature with high SHAP attribution is correlated with the model's prediction, not proven to *cause* the outcome. Also, SHAP values are specific to one trained model version; retraining can shift which features matter even if accuracy stays similar.

**Reasoning:** Important to distinguish "model-faithful explanation" from "causal truth" — a common point of confusion that a careful engineer should proactively flag.

---

### 28. Why surface positive *and* negative features separately, rather than just top-N overall?

**Answer:** Football outcome reasoning is naturally "for vs. against" — a user wants to see what favoured this outcome and what worked against it, not just a ranked magnitude list that mixes both directions. The Android Explain screen renders them as "Why the model leans this way" and "What counts against it", in plain football language with Big, Medium or Small impact, for exactly this reason.

**Reasoning:** A UX-driven API design choice — the explanation structure was shaped by how it would actually be consumed, not just how SHAP naturally outputs data.

---

## RAG & AI Assistant

### 29. Why build a RAG pipeline instead of just using the LLM directly?

**Answer:** A general-purpose LLM has no knowledge of this specific platform's model accuracy, dataset, or architecture — asking it directly would produce plausible-sounding but fabricated answers. RAG grounds every answer in actually-retrieved platform documentation (model cards, stage reports), so the assistant can only answer from real, verifiable context.

**Reasoning:** This is the core anti-hallucination strategy and the project's central AI engineering principle: "the assistant never invents facts."

---

### 30. Why Ollama instead of OpenAI/Anthropic API?

**Answer:** Keeps the entire system runnable offline with zero per-request cost and zero data leaving the developer's machine — directly supporting the project's "no cloud dependency" goal. `qwen2.5:7b-instruct` is the smallest local model that passed both assistant evals (ADR 019); the 3B `llama3.2` it replaced misquoted tool numbers.

**Reasoning:** A deliberate architectural constraint, not a budget workaround — local-first is a stated project value.

**Trade-off:** A local 7B model is less capable at open-ended reasoning than a frontier hosted model — acceptable because the task (source-constrained QA) doesn't require frontier-level reasoning.

---

### 31. Why a numpy-based vector store instead of a managed vector database?

**Answer:** At the scale of this knowledge base (a few hundred document chunks from model cards and stage reports), brute-force cosine similarity in numpy is fast enough (well under the latency budget) and avoids the operational overhead of standing up Pinecone, Weaviate, or pgvector for a dataset this small.

**Reasoning:** Right-sizing infrastructure to actual scale — premature infrastructure complexity is a real anti-pattern.

**Trade-off:** Brute-force search is O(n) per query; would need to move to an ANN index (FAISS, HNSW) if the knowledge base grew to tens of thousands of chunks.

---

### 32. How do you prevent the assistant from hallucinating?

**Answer:** Three layers: (1) retrieval — only relevant chunks are fetched via cosine similarity, (2) relevance filtering — low-similarity chunks are dropped before they reach the prompt, (3) a system prompt that explicitly instructs source-only answering and to say "I don't know" rather than guess, and (4) tools: match and season numbers come from the API's own services, never the model ([ADR 018](../adr/018-assistant-tool-calling.md), [ADR 021](../adr/021-season-tools-and-router.md)). The combination means the model is structurally constrained, not just politely asked, to stay grounded.

**Reasoning:** No single layer is sufficient alone — retrieval can return weak matches, and prompting alone doesn't guarantee compliance, so the layers are defence-in-depth.

---

### 33. What happens if Ollama isn't running?

**Answer:** The backend's lifespan startup attempts to load the assistant service; if it fails (Ollama unreachable), `app.state.chat_service` stays `None` and `POST /assistant/chat` returns a structured `503` with a clear error message — the backend doesn't crash, and every other endpoint (predictions, explanations, insights, fixtures, teams, health) continues working normally.

**Reasoning:** Graceful degradation — an optional dependency failing shouldn't take down the whole service. Verified by integration tests.

---

### 34. How would you evaluate whether the assistant's answers are actually faithful to the retrieved context?

**Answer:** Partly done. Three local evals run against Ollama: grounding (answers quote `/v2/predict` and invent no numbers, 11/11), abstention (answers what the documents cover, refuses the rest, 20/20) and season answers (7/7). Faithfulness to retrieved document chunks is not scored yet; that would need a ground-truth Q&A set and an LLM-as-judge or entailment check, and is listed as future scope.

**Reasoning:** Honest acknowledgment of what's structurally enforced versus what's empirically measured — these are different guarantees and shouldn't be conflated.

---

### 35. Why chunk documents before embedding rather than embedding whole files?

**Answer:** Whole-document embeddings dilute relevance signal — a long stage report might be mostly irrelevant to a specific question, with only one paragraph actually answering it. Chunking lets retrieval return just the relevant paragraph, improving both retrieval precision and the signal-to-noise ratio of what reaches the generation prompt.

**Reasoning:** Standard RAG practice, but worth being able to explain *why* rather than reciting it as received wisdom.

---

### 36. What embedding model did you choose and why?

**Answer:** `nomic-embed-text`, run locally via Ollama — chosen for being a capable, open, locally-runnable embedding model that doesn't require a separate hosted embedding API, consistent with the local-first constraint.

**Reasoning:** Same reasoning as the generation model choice — keep the entire pipeline self-hosted.

---

## Backend (FastAPI)

### 37. Why FastAPI over Flask or Django?

**Answer:** Native async support, automatic OpenAPI schema generation from Pydantic models (so `/docs` is always accurate, never hand-written and stale), and first-class Pydantic v2 integration for request/response validation — all of which map directly onto this project's "documentation must be accurate" and "structured validation" requirements.

**Reasoning:** Direct fit between framework strengths and project requirements, not just popularity.

---

### 38. Walk me through what happens when the backend starts up.

**Answer:** FastAPI's lifespan context manager runs once at startup: it loads settings, attempts to load the prediction model (if the artifact exists) into `PredictionService`, attempts to build the explanation service from the same model, and attempts to initialise the assistant service (Ollama connection + vector store). Each of these three is independently optional — a missing model disables prediction/explanation endpoints (503) but the app still starts and `/health` still responds.

**Reasoning:** Demonstrates the graceful-degradation design and the absence of any hard startup dependency that could prevent the whole service from coming up.

---

### 39. Why lifespan-based DI instead of loading the model inside each route handler?

**Answer:** Loading a joblib model file and building a SHAP explainer both have real cost; doing that per-request would add unacceptable latency and redundant I/O. Loading once at startup into `app.state`, then injecting via `Depends`, means every request reuses the already-loaded model.

**Reasoning:** Also avoids global mutable state accessed ad hoc from arbitrary code — `Depends` keeps the dependency graph explicit and testable (overridable in tests via `dependency_overrides`).

---

### 40. How does your backend handle a request with malformed or missing fields?

**Answer:** Pydantic request models enforce field presence, types, and basic constraints (e.g., non-empty team names) automatically — FastAPI returns a `422` with structured field-level error detail before the request handler code even runs. Domain-level errors (e.g., the AI service reports a missing required feature column) are raised as typed exceptions and mapped to specific status codes via registered exception handlers.

**Reasoning:** Two layers of validation — schema-level (free, via Pydantic) and domain-level (explicit, via typed exceptions) — each catching a different class of bad input.

---

### 41. What's the difference between your 422 and 503 responses?

**Answer:** `422` means the request itself was invalid (bad input — missing fields, wrong types, business-rule violation like a missing feature column). `503` means the request was valid but the service needed to fulfil it isn't available (model not loaded, Ollama unreachable) — a server-side, not client-side, condition.

**Reasoning:** This distinction matters for API consumers — a `422` means "fix your request," a `503` means "retry later, your request was fine."

---

### 42. How is the backend tested without a real model present?

**Answer:** Stage 9's contract tests use `TestClient` with `dependency_overrides` injecting mocked `PredictionService`/`ExplanationService`/`ChatService` instances, so the API contract (status codes, response shape, validation behaviour) is verified independent of whether a real model is trained. Stage 12 then adds a separate integration suite that *does* use the real model, to catch what mocks can't.

**Reasoning:** Deliberate two-tier testing strategy — fast, deterministic contract tests plus slower, real-artifact integration tests, each serving a distinct purpose.

---

### 43. How would you add authentication to this backend?

**Answer:** It now has it, for hosted deployments ([ADR 022](../adr/022-invite-only-accounts-and-consent.md)): invite-only accounts, scrypt password hashes from the standard library, opaque 30-day session tokens stored as hashes, a login lockout and a consent notice. With `AUTH_REQUIRED=true` every `/v2` data route needs a token and current consent, and `/v1` is not mounted. It is off by default on the server. The Android app always opens on sign-in, with a Sign in tab and an Invite code tab, then shows the notice if it still needs accepting; it sends the token on every request and returns to sign-in on any 401.

**Reasoning:** Distinguishes "didn't think about it" from "deliberately scoped out, with a clear extension path."

---

### 44. What would break first if this backend had to handle real production traffic?

**Answer:** Sign-in exists but is off by default, and the account store is a single JSON file, which suits one process only. There is a rate limiter (120 requests per minute per client, 429 with `Retry-After`, [ADR 014](../adr/014-api-versioning-and-rate-limiting.md)), but it lives in memory per process, so behind a load balancer each instance would count separately. The assistant is the heaviest path, since a local LLM answer can take many seconds. First steps: a shared account store, a shared rate-limit store such as Redis, HTTPS, and a queue or separate limit for the assistant.

---

## Android (Compose Multiplatform)

### 45. Why Compose Multiplatform instead of plain Android Views or React Native?

**Answer:** Compose Multiplatform gives a modern declarative UI toolkit with a clear path to sharing UI code across platforms in the future, while staying fully native (Kotlin, not a JS bridge) — better performance and tooling integration than React Native, and a more maintainable state-management model than the View system's imperative updates.

**Reasoning:** Matches the project's "Android-first, KMP-ready" scoping decision in the architecture docs.

---

### 46. Why are ViewModels in `androidMain` but Composables in `commonMain`?

**Answer:** `androidx.lifecycle.ViewModel` and `viewModelScope` are Android-specific APIs (not yet stably multiplatform at the time this was built), so ViewModels live in `androidMain`. Composables, UI state classes, and repository interfaces have no Android-specific dependency and live in `commonMain`, ready to be reused if another Compose Multiplatform target (iOS, desktop) were added later.

**Reasoning:** Maximises what's actually shareable today without forcing a premature multiplatform ViewModel abstraction that adds complexity for no current benefit.

---

### 47. How do you share state across the Prediction → Result → Explain screen flow?

**Answer:** Using Navigation Compose's `navController.getBackStackEntry(Screen.Prediction.route)` as the `ViewModelStoreOwner` when requesting the ViewModel on the Result and Explain screens — this returns the *same* `PredictionViewModel` instance that was created when the Prediction screen was first entered, scoped to that back-stack entry rather than each individual screen.

**Reasoning:** Avoids re-issuing the prediction request or duplicating state across three screens that are conceptually one user flow.

---

### 48. How does the Android app get the model's 42 features?

**Answer:** It doesn't compute them. The app sends only the two team names and an optional league, and the server builds all 42 features from match history with the same pipeline used in training ([ADR 008](../adr/008-server-side-match-features.md)). Version one sent neutral placeholder values, which was its biggest weakness; moving feature computation to the server fixed it.

**Reasoning:** One code path for training and serving means no training/serving skew, and the app doesn't need the full match history.

**Trade-off:** Every prediction needs the server; the app can't predict a new fixture offline. It does show the last saved answers offline, under a banner.

---

### 49. How are your Android repository tests structured, and what do they verify?

**Answer:** MockK is used to mock `FootballApiService`, and each repository test verifies both the success path (service returns data, repository maps it to `NetworkResult.Success`) and the failure path (service throws or returns an error, repository maps it to `NetworkResult.Error`) — keeping the repository's mapping logic tested independent of real network calls.

**Reasoning:** Repository tests should verify the repository's own logic (response mapping, error translation), not re-test Ktor itself.

---

### 50. If you had another two weeks on this project, what would you build next?

**Answer:** (1) Retrieval hit rate and faithfulness metrics for the assistant, on top of the grounding, abstention and season evals, run on every change. (2) A weekly monitoring job that scores the live season's matches and alerts when log loss or calibration drifts outside the cross-validation range. (3) Retries with backoff for the daily downloads and a timeout plus one retry for LLM calls.

**Reasoning:** The prediction path is measured and honest already; the assistant and live monitoring are the least measured parts, so they come first.

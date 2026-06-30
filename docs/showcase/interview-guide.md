# Interview Guide — Football Intelligence Platform

50 questions an interviewer might ask about this project, organised by topic, each with a suggested answer, the reasoning behind it, and the trade-offs worth raising proactively.

---

## Data & Feature Engineering

### 1. Why did you split the data chronologically instead of randomly?

**Answer:** Because the features are rolling-window statistics (form, goals, Elo) computed from a team's prior matches. A random split would let a model train on a match whose rolling-form features were computed using data from matches that occur *after* some of the test-set matches chronologically, which is leakage — the model would implicitly see "future" outcomes baked into engineered features.

**Reasoning:** This is the single most common bug in time-series ML projects, and it inflates test metrics in a way that doesn't show up unless you specifically check for it.

**Trade-off:** Chronological splitting means the test set is necessarily the *most recent* matches, which can have higher variance (e.g., end-of-season dead rubbers) than a random sample would. Documented in [ADR 003](../adr/003-chronological-train-val-test-split.md).

---

### 2. How do you prevent leakage in the rolling-window features specifically?

**Answer:** Every rolling feature generator applies `.shift(1)` before computing the window, so a match's features are always built from strictly prior matches, never including the match itself.

**Reasoning:** Without the shift, a 5-match rolling average computed "as of" match N would include match N's own result.

**Trade-off:** This means the very first few matches of a season have sparse or default-value features (no history yet) — handled with neutral defaults rather than dropping early-season rows.

---

### 3. Why 42 features specifically — how did you choose them?

**Answer:** They span six categories: rolling form (wins/points, last 5 and last 10), goal statistics (scored/conceded/differential), win percentage and points-per-game, rest days, head-to-head history, league position/points, and Elo ratings (including average opponent Elo faced). Each category captures a different signal: recent form, scoring ability, fatigue, historical matchup, table position, and team strength.

**Reasoning:** Breadth across categories rather than depth in one — avoids overfitting to a single signal type.

**Trade-off:** 42 features on 380 matches is a high feature-to-sample ratio for a tree model; mitigated by XGBoost's built-in regularisation and early stopping.

---

### 4. What is Kahn's algorithm doing in your feature pipeline and why do you need it?

**Answer:** Some feature generators depend on outputs of other generators (e.g., a feature that uses Elo needs Elo to be computed first). The `FeatureRegistry` builds a dependency graph between generators and topologically sorts it with Kahn's algorithm so they always run in a valid order, regardless of how they were registered.

**Reasoning:** Without explicit ordering, adding a new generator that depends on an existing one would silently break if registered before its dependency.

**Trade-off:** Adds a small amount of upfront complexity versus just hardcoding generator order — but makes the registry safely extensible.

---

### 5. Why football-data.co.uk and not a richer source like FBref or Understat?

**Answer:** football-data.co.uk gives clean, structured match-result CSVs with minimal preprocessing needed, which kept Stage 4-5 focused on building a *correct* ingestion framework rather than fighting messy HTML scraping. The provider abstraction (`DatasetDownloader`/`DatasetStorage`) was built to support FBref and Understat too — those providers exist in the codebase — but football-data.co.uk was used for the canonical dataset.

**Reasoning:** Get a correct, validated pipeline working end-to-end first; richer data sources are a drop-in extension, not a redesign.

**Trade-off:** football-data.co.uk lacks advanced metrics like xG, which Understat provides — a documented future extension.

---

### 6. How do you validate data quality before it enters the pipeline?

**Answer:** `DatasetValidator` enforces 9 explicit rules (e.g., valid date ranges, non-negative goal counts, valid team names, no duplicate matches) before any data is marked "processed." Validation failures are loud errors, not silently skipped rows.

**Reasoning:** Per the project's data engineering philosophy: "data quality failures are loud errors, not silent skips" — silent skips hide problems until they surface much later as model quality issues.

**Trade-off:** Stricter validation means a single bad row can halt the whole pipeline run rather than degrading gracefully — an intentional choice given the dataset size (380 matches) makes manual review of a halted run cheap.

---

### 7. Why Parquet over CSV for processed data?

**Answer:** Parquet preserves types (dates, floats) without re-parsing, is columnar (faster for the read patterns used by feature engineering), and is versioned alongside the code that produced it per the project's data engineering conventions.

**Reasoning:** CSV round-trips lose type information (a date becomes a string) and are slower to read repeatedly during pipeline iteration.

**Trade-off:** Parquet isn't human-readable in a text editor the way CSV is — mitigated by keeping raw CSVs as the immutable source of truth.

---

### 8. How would you scale this to a multi-season dataset?

**Answer:** The main blocker is Elo ratings resetting to 1500 at the start of every pipeline run — they'd need to persist and carry over season boundaries (with appropriate season-transition regression toward the mean, a common practice in Elo systems). The ingestion and feature pipelines themselves are already season-agnostic.

**Reasoning:** This is a known, documented limitation (see root README "Future Improvements") rather than something overlooked.

**Trade-off:** Persisting Elo across seasons adds state that needs its own storage and versioning strategy — deliberately deferred rather than half-implemented.

---

### 9. What would you do differently if the dataset were 100x larger?

**Answer:** Parquet plus pandas would start to strain; I'd look at Polars or a proper feature store, and the brute-force numpy vector store for RAG would need to become an approximate-nearest-neighbour index (e.g., FAISS or HNSW). The chronological split methodology and leakage prevention would not need to change.

**Reasoning:** The architecture is sized appropriately for ~380 matches; scaling decisions are about swapping implementations behind the same interfaces, not redesigning the pipeline.

---

### 10. How is feature engineering tested?

**Answer:** Each of the 9 generators has dedicated unit tests verifying both correctness (e.g., rolling average computed correctly) and leakage prevention (a feature for match N must not change if match N+1's data changes). 142 tests cover this stage.

**Reasoning:** Leakage bugs don't show up as test failures unless you specifically assert that future data doesn't affect past features — so leakage tests are written as a distinct test category, not bundled into correctness tests.

---

## Model Training & Evaluation

### 11. Why XGBoost over a neural network or logistic regression?

**Answer:** Tabular, moderate-sized data (380 rows × 42 features) is exactly XGBoost's strength — it typically outperforms neural nets on tabular data at this scale, trains in seconds, and has native, exact SHAP support via `TreeExplainer`. A neural net would need far more data to justify its added complexity and would lose the exact-explainability property.

**Reasoning:** Documented in [ADR 001](../adr/001-use-xgboost-for-predictions.md) — match outcome prediction at this scale and feature mix doesn't benefit from deep learning's representation-learning advantages.

**Trade-off:** XGBoost can't learn from raw unstructured inputs (e.g., player tracking video) the way a neural net could — irrelevant here since the input is already structured tabular data.

---

### 12. Why `multi:softprob` instead of treating this as three binary classifiers?

**Answer:** `multi:softprob` natively models the three mutually exclusive, collectively exhaustive outcomes (H/D/A) as a single softmax, producing probabilities that sum to 1.0 by construction. Three independent binary classifiers would need post-hoc renormalisation and lose the natural constraint.

**Reasoning:** The 3-way structure of football outcomes maps directly onto a multi-class objective.

---

### 13. What's your model's accuracy, and is that good?

**Answer:** 56.1% test accuracy on a 3-class problem with a 33.3% random baseline, 0.625 ROC AUC (one-vs-rest). This is in the realistic range for football outcome prediction — bookmakers and published academic models typically land in the 50-55% range, since football has high inherent randomness (a team's "true" win probability is rarely much above 60% even for strong favourites).

**Reasoning:** I'd rather state this honestly than oversell it — overstating model performance in an interview is a credibility risk, and the project's stated philosophy is to be "honest about what it knows."

**Trade-off:** Higher accuracy is achievable with richer features (xG, lineups, weather) — explicitly out of scope for this dataset.

---

### 14. Why early stopping, and on what metric?

**Answer:** Early stopping on the validation set's multi-class log-loss halts training once additional boosting rounds stop improving generalisation, preventing the model from overfitting to training-set noise.

**Reasoning:** With only 380 matches, overfitting risk is real; early stopping is a cheap, standard regularisation technique appropriate to the data size.

---

### 15. Walk me through your cross-validation strategy.

**Answer:** `TimeSeriesSplit` with 5 folds — each fold trains on an expanding window of past matches and validates on the immediately following chunk, preserving chronological order throughout (never validating on data that precedes training data in time).

**Reasoning:** Standard k-fold CV would shuffle and leak future information into training folds, same issue as the train/test split.

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

**Answer:** The current model uses fixed, reasonable XGBoost hyperparameters (moderate depth, learning rate, with early stopping handling the "how many rounds" question automatically) rather than a full hyperparameter search. Optuna-based tuning is explicitly listed as future scope.

**Reasoning:** With 380 matches, exhaustive hyperparameter search risks overfitting to the validation set itself; I prioritised correct methodology (leakage prevention, chronological CV) over marginal accuracy gains from tuning, which is the higher-leverage problem at this data scale.

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

**Answer:** ~7 ms measured (10-run average) for the core SHAP computation; under 30 ms end-to-end through the FastAPI layer including serialisation. It matters because explainability is exposed as a real-time API endpoint consumed by a mobile app — if it took seconds, it couldn't be a synchronous part of the user-facing prediction flow.

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

**Answer:** Football outcome reasoning is naturally "for vs. against" — a user wants to see what favoured this outcome and what worked against it, not just a ranked magnitude list that mixes both directions. The Android Explain screen renders them as two distinct, colour-coded sections for exactly this reason.

**Reasoning:** A UX-driven API design choice — the explanation structure was shaped by how it would actually be consumed, not just how SHAP naturally outputs data.

---

## RAG & AI Assistant

### 29. Why build a RAG pipeline instead of just using the LLM directly?

**Answer:** A general-purpose LLM has no knowledge of this specific platform's model accuracy, dataset, or architecture — asking it directly would produce plausible-sounding but fabricated answers. RAG grounds every answer in actually-retrieved platform documentation (model cards, stage reports), so the assistant can only answer from real, verifiable context.

**Reasoning:** This is the core anti-hallucination strategy and the project's central AI engineering principle: "the assistant never invents facts."

---

### 30. Why Ollama instead of OpenAI/Anthropic API?

**Answer:** Keeps the entire system runnable offline with zero per-request cost and zero data leaving the developer's machine — directly supporting the project's "no cloud dependency" goal. `llama3.2` is small enough to run on a laptop while still being capable enough for grounded, source-constrained QA.

**Reasoning:** A deliberate architectural constraint, not a budget workaround — local-first is a stated project value.

**Trade-off:** A local 3B-ish parameter model is less capable at open-ended reasoning than a frontier hosted model — acceptable because the task (source-constrained QA) doesn't require frontier-level reasoning.

---

### 31. Why a numpy-based vector store instead of a managed vector database?

**Answer:** At the scale of this knowledge base (a few hundred document chunks from model cards and stage reports), brute-force cosine similarity in numpy is fast enough (well under the latency budget) and avoids the operational overhead of standing up Pinecone, Weaviate, or pgvector for a dataset this small.

**Reasoning:** Right-sizing infrastructure to actual scale — premature infrastructure complexity is a real anti-pattern.

**Trade-off:** Brute-force search is O(n) per query; would need to move to an ANN index (FAISS, HNSW) if the knowledge base grew to tens of thousands of chunks.

---

### 32. How do you prevent the assistant from hallucinating?

**Answer:** Three layers: (1) retrieval — only relevant chunks are fetched via cosine similarity, (2) relevance filtering — low-similarity chunks are dropped before they reach the prompt, (3) a system prompt that explicitly instructs source-only answering and to say "I don't know" rather than guess. The combination means the model is structurally constrained, not just politely asked, to stay grounded.

**Reasoning:** No single layer is sufficient alone — retrieval can return weak matches, and prompting alone doesn't guarantee compliance, so the layers are defence-in-depth.

---

### 33. What happens if Ollama isn't running?

**Answer:** The backend's lifespan startup attempts to load the assistant service; if it fails (Ollama unreachable), `app.state.chat_service` stays `None` and `POST /assistant/chat` returns a structured `503` with a clear error message — the backend doesn't crash, and the other four endpoints (prediction, explanation, health, model info) continue working normally.

**Reasoning:** Graceful degradation — an optional dependency failing shouldn't take down the whole service. Verified by integration tests.

---

### 34. How would you evaluate whether the assistant's answers are actually faithful to the retrieved context?

**Answer:** Not yet implemented as an automated metric — currently relies on manual spot-checking and the structural guarantees (retrieval + filtering + prompt). A proper evaluation would build a ground-truth Q&A set and score faithfulness (e.g., via an LLM-as-judge comparing the answer against only the retrieved chunks, or simpler n-gram/entailment overlap checks). This is explicitly listed as future scope.

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

**Answer:** FastAPI's `Depends` system makes this straightforward to add without restructuring — an `api_key` or JWT-validation dependency could be added to each router and injected the same way the AI services already are. Not implemented here because the project's explicit scope excludes authentication for early stages (per `.claude/CLAUDE.md` non-goals) and the system is designed for local development, not public deployment.

**Reasoning:** Distinguishes "didn't think about it" from "deliberately scoped out, with a clear extension path."

---

### 44. What would break first if this backend had to handle real production traffic?

**Answer:** The vector store and model are loaded in-process and shared across all requests within a single uvicorn worker — fine for a single-instance local deployment, but horizontal scaling would need the model artifact to be reproducibly loadable on each instance (already true, since it's loaded from a versioned file) and the vector store similarly. The bigger gap is the complete absence of auth, rate limiting, and request throttling — explicitly out of scope but the first things I'd add before any public exposure.

**Reasoning:** Shows awareness of the gap between "works locally" and "production-ready," and what the actual first steps would be.

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

### 48. Why does the Android app use neutral feature values instead of computing real ones?

**Answer:** Computing the real 42 engineered features (rolling form, Elo, head-to-head) requires the *full* historical match dataset and the same feature-engineering pipeline that runs in Python on the backend — replicating that logic in Kotlin on-device would duplicate a non-trivial pipeline and risk it drifting out of sync with the source of truth. `buildNeutralFeatures()` provides demo-appropriate average values so the prediction flow is fully exercisable, with the limitation explicitly documented.

**Reasoning:** A pragmatic, clearly-labelled trade-off rather than either skipping the feature or silently misrepresenting it as "real."

**Trade-off:** Predictions shown in the demo reflect an average-team scenario, not the selected teams' actual current form — explicitly called out in the UI's data flow and in documentation, not hidden.

---

### 49. How are your Android repository tests structured, and what do they verify?

**Answer:** MockK is used to mock `FootballApiService`, and each repository test verifies both the success path (service returns data, repository maps it to `NetworkResult.Success`) and the failure path (service throws or returns an error, repository maps it to `NetworkResult.Error`) — keeping the repository's mapping logic tested independent of real network calls.

**Reasoning:** Repository tests should verify the repository's own logic (response mapping, error translation), not re-test Ktor itself.

---

### 50. If you had another two weeks on this project, what would you build next?

**Answer:** Two things, in priority order: (1) replace `buildNeutralFeatures()` with a backend endpoint that computes real features for a selected team pairing as of "today," so predictions reflect actual current form rather than neutral averages — this directly improves the most user-visible limitation; (2) a structured RAG faithfulness evaluation harness with a small ground-truth Q&A set, so assistant quality becomes a measurable, trackable metric rather than something verified only by manual spot-checking.

**Reasoning:** Prioritises closing the most user-visible gap first, then the most measurement-visible gap — demonstrates the ability to triage scope under a time constraint rather than listing every possible improvement with equal weight.

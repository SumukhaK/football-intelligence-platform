# Interview Guide — Football Intelligence Platform

Updated for v2.6.0, 17 October 2026. These are suggested answers for a personal project, not claims of commercial production experience. Metrics below are dated recorded results, not fresh measurements.

Read in order:

- **Questions 1–28:** data, training and explainability, on this page.
- [Questions 29–50: assistant, API and Android](interview-guide-app-and-assistant.md).
- [Hosting from an Android developer's perspective](hosting-interview-guide.md): vocabulary, recorded deployment and local preparation.
- [Cloud setup and deployment commands](hosting-interview-cloud.md).
- [Smoke checks, Android, rollback and unfinished work](hosting-interview-operations.md).

The [execution tracker](../plans/hosting-execution-tracker.md) is the deployment-status record. Older reports can describe superseded models; attach every number to its model, dates and sample.

## Data and feature engineering

### 1. Why split by season instead of randomly?

**Answer:** Football predictions use the past to forecast later matches. I train the frozen reporting model on 2000/01–2021/22, validate on 2022/23, test on 2023/24, and reserve 2024/25–2025/26 for holdout evaluation. Random row splitting would let later seasons influence the model used to judge earlier matches.

**Trade-off:** One season can be unusual. Walk-forward checks and later-season evaluation give more context. The serving refit includes those old test/holdout seasons, so their metrics belong to the frozen model, not to an unseen test of the refit. [ADR 007](../adr/007-season-based-split-and-evaluation.md), [refit report](../reports/refit-all-seasons.md).

### 2. How do you prevent rolling-feature leakage?

**Answer:** Rolling aggregates exclude the current match, typically using a one-match shift. Stateful features such as Elo use the rating before updating it with that result. Serving builds features from matches strictly before the fixture cutoff.

**Why:** Saying every generator uses exactly the same shift implementation would be inaccurate. The invariant is that the current/future outcome cannot affect its pre-match features.

**Trade-off:** Sparse history creates missing values; the training pipeline fits the median imputer on training rows and reuses it for evaluation/serving. [Feature code](../../ai/feature_engineering/), [serving parity tests](../../ai/tests/inference/test_fixture_features.py).

### 3. Why 42 features?

**Answer:** Nine generator groups produce 42 pinned pre-match features: recent form, scoring/conceding, win rates, rest, head-to-head, table position, Elo and opponent strength. The training configuration fixes their names and order, preventing an added numeric data column from silently becoming a predictor.

**Trade-off:** Related features overlap. SHAP explains attribution under the fitted model's assumptions; correlation makes a causal interpretation unsafe. [Configuration](../../ai/training/configuration.py).

### 4. Why Kahn's algorithm in the feature pipeline?

**Answer:** Generators declare dependencies. The registry topologically sorts them, for example placing Elo before strength of schedule, and rejects missing dependencies/cycles.

**Why:** This makes execution order explicit rather than dependent on registration order. It is a small registry for nine groups, not a distributed workflow engine. [Registry](../../ai/feature_engineering/registry.py).

### 5. Why football-data.co.uk?

**Answer:** It supplies consistent historical match-result CSVs across the five scoped leagues. The completed historical dataset has 46,709 matches from 2000/01–2025/26. That gave a manageable, validated baseline before experimenting with richer sources.

**Trade-off:** FBref/Understat adapter code and parser tests do not prove complete live ingestion support. Experiments with Champions League rest, xG and FIFA ratings did not show a reliable improvement, and some inputs could not serve the current season. [ADR 005](../adr/005-top-five-leagues-multi-source-data.md), [extras report](../reports/kaggle-extras.md).

### 6. How is data quality validated?

**Answer:** Provider parsing, canonical Pydantic schemas, dataset rules and season-integrity checks cover different boundaries: dates/types, nonnegative scores, distinct teams, duplicates, score/result consistency and season structure. Backfill validates each season before assembling the combined data.

**Trade-off:** Some low-level normalization APIs report failed-row counts rather than raising themselves. The ingesting caller must enforce the loud-failure policy; validation is not automatic merely because a validator exists. [Validation](../../ai/validation/), [backfill](../../ai/scripts/backfill_football_data.py).

### 7. Where do CSV and Parquet each fit?

**Answer:** Canonical processed match results and fixtures are versioned **CSV files**. Feature engineering writes a **Parquet feature matrix**, read by training. Parquet is useful there for typed columns and repeated analytical reads; CSV keeps canonical data easy to inspect.

**Trade-off:** Neither format alone provides provenance or reproducibility. Metadata, schemas, immutable raw snapshots and explicit artifact versions do that. Generated datasets/models are generally ignored by Git; do not claim every output is committed. [Quick-start artifacts](../setup/quick-start.md#expected-artifacts), [storage](../../ai/ingestion/storage.py).

### 8. How did you extend to multiple seasons?

**Answer:** Backfill expanded to 26 seasons of five leagues. Elo carries across seasons within a league, regresses a third toward 1500 between seasons, and gives promoted teams the average rating of the teams they replace. Table/rest features respect season boundaries.

**Trade-off:** Elo pools are league-specific; I do not compare a Premier League rating directly with a Bundesliga rating. [Multi-league report](../reports/multi-league-retraining-comparison.md).

### 9. What changes at 100 times the data?

**Answer:** First measure reads, memory, feature generation and retrieval. Consider column projection/partitioned Parquet or Polars for data work and an approximate-nearest-neighbour index for much larger retrieval collections.

**Trade-off:** Those changes are proposals, not implemented infrastructure. Season splits, feature invariants and evaluation remain necessary regardless of the storage engine.

### 10. How are features tested?

**Answer:** Small deterministic fixtures test expected values, dependencies, season transitions and leakage. Separate serving-parity tests compare the fixture builder's output with the training feature pipeline, including missing values and promoted-team cases.

**Why:** A high predictive score can hide leakage. Tests need to assert the time boundary directly. Test definitions and old passing reports do not prove a new checkout currently passes. [Feature tests](../../ai/tests/feature_engineering/), [parity tests](../../ai/tests/inference/test_fixture_features.py).

## Model training and evaluation

### 11. Why XGBoost?

**Answer:** The input is a modest table of engineered features, not images or text. XGBoost trains on CPU, supports missing-value preprocessing and strong tabular baselines, and works with TreeSHAP. The frozen training split has 39,627 rows and 42 selected features.

**Trade-off:** I would compare models empirically; I would not claim trees always beat neural networks. This project has no need for a large neural model to learn representations from raw media. [ADR 001](../adr/001-use-xgboost-for-predictions.md).

### 12. Why multi:softprob?

**Answer:** Home win, draw and away win are mutually exclusive outcomes. One multiclass model returns a probability distribution across all three, rather than three independent binary scores needing reconciliation.

**Trade-off:** The argmax decision and the quality of the probability distribution are different things. A model can give useful draw probabilities while rarely selecting draw.

### 13. What accuracy can you honestly quote?

**Answer:** Frozen reporting model `20260928_123224` has approximately 52.45% accuracy and 0.9762 log loss on the 2023/24 test season. Serving model `20261007_154105` is a refit through 2025/26 with no held-out season of its own.

On the separate 250-match 2026/27 sample through 20 September, the frozen model scored 52.4% / 0.975 log loss, refit 52.0% / 0.976, and Bet365 51.6% / 0.981.

**Trade-off:** The refit-versus-frozen and refit-versus-bookmaker confidence intervals include zero. This is not evidence that the refit beats the market. Earlier comparison tables belong to older runs. [Refit evidence](../reports/refit-all-seasons.md), [quick-start model identity](../setup/quick-start.md#step-3--train-model).

### 14. Why early stopping?

**Answer:** The frozen training run monitors validation multiclass log loss and selects iteration 167, giving 168 trees. The serving refit reuses that fixed tree count while training on all completed seasons; it does not early-stop using an already-used test season.

**Trade-off:** That separates recipe selection from deployment fitting. The refit needs later, truly unseen results for evaluation. [ADR 017](../adr/017-refit-on-all-seasons-for-serving.md).

### 15. How does walk-forward validation work?

**Answer:** Each fold trains on earlier seasons and validates on later ones. Hyperparameter tuning uses only the training-season subset; the general training pipeline also produces CV over train plus validation. These are distinct procedures.

**Trade-off:** Each fold fits its own imputer. CV cannot make football seasons identically distributed, and its older reported numbers are not a new test of the serving refit. [Tuning](../../ai/training/tuning.py), [CV](../../ai/evaluation/cross_validation.py).

### 16. How are models versioned?

**Answer:** Timestamped run directories hold the model bundle, configuration, metrics and reports. The JSON registry records provenance and `latest/` is a copied serving directory, not a symlink. Promotion and refit promotion are explicit workflows.

**Trade-off:** Some recorded run paths are machine-specific. A registry entry and snapshot hash aid traceability but do not prove a promotion passed every evaluation gate. [Registry](../../ai/model_registry/registry.py), [snapshot builder](../../ai/scripts/build_snapshot.py).

### 17. Why joblib, and is it safe?

**Answer:** The Python serving stack can restore the model, imputer, encoder and feature order together using joblib. ONNX would be a separate portability choice needing conversion and parity checks.

**Risk:** joblib uses pickle semantics and can execute code while loading. It is **not safer than pickle for untrusted files**. Only load artifacts built through a trusted pipeline. SHA-256 detects changes relative to a trusted manifest; it does not authenticate who created that manifest. [ADR 002](../adr/002-joblib-model-serialization.md), [persistence](../../ai/training/persistence.py).

### 18. How would you detect production drift?

**Answer:** Staging exists, but an automated online quality/drift job is still pending. I would score later completed matches with the unchanged serving model, compare log loss/calibration against dated baselines and inspect league/sample differences before deciding on retraining.

**Trade-off:** A few bad matches are not proof of drift. Separate data freshness, feature/schema faults and statistical uncertainty from model deterioration. [Tracker steps 8 and 10](../plans/hosting-execution-tracker.md).

### 19. What did you tune?

**Answer:** A 27-setting depth/learning-rate/tree-count grid was compared by season walk-forward log loss on training seasons. The selected recipe uses depth 3, learning rate 0.03, up to 400 trees for frozen training, then the selected 168 trees for refitting.

**Trade-off:** Closely ranked settings are not a dramatic optimization victory. Data/temporal correctness and honest holdout reporting matter more. [Comparison report](../reports/multi-league-retraining-comparison.md).

### 20. How would you debug too many home-win predictions?

**Answer:** Compare class frequencies and probability distributions with the training baseline. Check feature order, missing values, team/league mapping and serving/training parity; then inspect SHAP for dominant signals and recheck temporal leakage.

**Trade-off:** Do not force equal class predictions to look balanced. Choose any decision-rule change using validation objectives, not the test outcomes.

## Explainability

### 21. Why TreeSHAP rather than LIME?

**Answer:** TreeSHAP uses the fitted tree structure to compute model attributions without fitting a new perturbed local surrogate for every explanation. LIME is more model-agnostic but introduces sampling/surrogate choices.

**Trade-off:** “Exact” refers to TreeSHAP's attribution calculation under its assumptions, not a causal explanation of football. [ADR 004](../adr/004-shap-for-explainability.md).

### 22. What does a SHAP value mean here?

**Answer:** It is a feature's contribution to the selected class's model output relative to a baseline. Positive pushes toward that class; negative pushes away.

**Important:** Current TreeExplainer attributions should not be called probability percentage-point changes. Tensor-shape normalization does not convert raw model-output units into probabilities. [Explainer](../../ai/explainability/explainer.py).

### 23. How does multiclass SHAP work?

**Answer:** The explainer normalizes library output to samples × features × classes. ExplanationService selects contributions for the predicted class and returns positive, negative and all features with model/data/feature metadata.

**Why:** Users need the reasons for the actual predicted outcome, not three unlabeled attribution arrays. [Explanation service](../../ai/explainability/services/explanation_service.py).

### 24. Why cache the explainer?

**Answer:** Constructing it repeatedly wastes work. A process-level cache reuses explainers for the supplied version key; the service currently derives that key from model-file modification time.

**Trade-off:** The cache is unbounded and lacks a construction lock/path-aware key. It suits the current small serving setup; it is not a complete concurrent model registry. [Cache](../../ai/explainability/cache.py).

### 25. What explanation latency is measured?

**Answer:** The older v1 Stage 12 report recorded about 7 ms core SHAP and under 30 ms end-to-end in that test environment. I would identify the model, hardware, cache state and included feature computation before quoting it.

**Trade-off:** Those are not measured current Cloud Run p95 figures. The tracker records one 19-second startup-to-ready observation, not a full cold-request distribution. [Stage 12](../reports/stage-12-summary.md), [hosting tracker](../plans/hosting-execution-tracker.md).

### 26. How would you explain a waterfall plot?

**Answer:** Start at the baseline model output, then add each feature's positive or negative contribution to reach this match's output. Bars explain how this prediction differs from the baseline.

**Trade-off:** Label the actual output units. Apply the model's probability transformation separately; do not draw raw attributions as additive probability percentages.

### 27. What SHAP limitations should a stakeholder know?

**Answer:** SHAP explains the model, not causal truth. Correlated features share information; changing model/data/background assumptions can change attribution. An explanation does not prove the prediction is accurate or the probabilities calibrated.

**Why:** Model-faithful explanation and a reliable forecast require separate evidence.

### 28. Why separate positive and negative factors?

**Answer:** “What supports this pick?” and “What counts against it?” are useful football questions. The Explain screen uses server-friendly names and Big/Medium/Small relative impact, initially showing five factors per direction.

**Trade-off:** The main prediction and explanation are separate endpoints/screens. My Team tolerates missing SHAP and omits reasons. Do not claim every displayed prediction is blocked until SHAP succeeds. [Android result](../../frontend/feature-prediction/src/commonMain/kotlin/com/footballintelligence/feature/prediction/PredictionResultScreen.kt).

Continue with [questions 29–50](interview-guide-app-and-assistant.md), or begin the [hosting walkthrough](hosting-interview-guide.md).

# Plan: Next Phase — Quality Gaps, Draws and Scoreline Predictions

**Status:** Done 2026-09-29; everything below shipped in v2.0.0.
**Date:** 2026-09-28
**Builds on:** PRs #24 → #25 → #26 → #27 (stacked; merged to main together at the end)
**Branch:** `feature/scoreline-predictions`

---

## 1. Where we are

| Area | State | Evidence |
|---|---|---|
| Data | 46,709 matches, top-5 leagues, 2000/01–2025/26, plus 2026/27 so far | ADR 005, [comparison report](../reports/multi-league-retraining-comparison.md) |
| Model | XGBoost `20260928_123224`; log loss 0.976 on 2023/24, 0.996 on the 2024/25–2025/26 holdout | Same report |
| Live check | 2026/27 so far: 131/250 correct (52.4%), bookmakers 51.6% | [in-season report](../reports/in-season-2026-27.md) |
| Serving | Server computes features from history; `/teams`; Premier League only | ADR 008, [docs/api.md](../api.md) |
| App | Sends team names only; teams from the API; 17 unit tests run | PR #27 |

Known weak spot: the model never picks a draw as the most likely result, while 25% of 2026/27 matches were draws.

---

## 2. Work queue and order

| # | Work | Why this order | Size |
|---|---|---|---|
| W1 | **End-to-end app test** on the emulator. **Done 2026-09-28** on a Pixel 6 Pro API 31: it found and fixed debug cleartext HTTP (PR #27); predict → result → explain now works | Nobody had tapped predict → result → explain | S |
| W2 | **CI green**: add detekt and spotless to Gradle, fix what they flag. **Done** (PR #30) | Frontend CI jobs fail on main; the final merge should be green | M |
| W3 | **Result screen foundations**: Compose resources for strings, previews, a three-way probability bar and a "Draw likely" tag. **Done** (PR #31, #34, ADR 010); the tag shipped as "Draw possible" | W4 and W5 both redesign this screen; doing strings and previews once avoids churn | M |
| W4 | **Draw handling**, phases A–B from the draw plan. **Analysis done 2026-09-28** ([report](../reports/draw-handling.md)): a third of draws costs 4–5 points of accuracy, and draw features gave no gain. **Done**: decided tag only (ADR 011, PR #33, #34) | Clearest accuracy gap; cheap | M |
| W5 | **Scoreline predictions** (section 3). **Done 2026-09-28**: model and evaluation ([report](../reports/goals-model.md)), `/insights` API and app sections | Main new feature; needs W3's screen and W4's draw work | L |
| W6 | Scheduled live refresh plus backend reload. **Done 2026-09-29**: daily in-process refresh and reload without restart (ADR 013) | Removes the manual refresh and restart | S |
| W7 | Kaggle extras (xG, FIFA ratings, Champions League rest days). **Tested 2026-09-29: none improves log loss, none kept** ([report](../reports/kaggle-extras.md)) | Small expected gain; licences unconfirmed | M |
| W8 | Other four leagues in the API and app. **Done 2026-09-29** (ADR 012, [plan](five-leagues-plan.md)) | API contract change; needs its own ADR | M |

W1 and W2 come first so the final merge is tested and green. W3–W5 share one screen and are sequenced to touch it once per concern.

### W4 draw handling, decisions carried over

- The draw rule's objective is still open (section 5, decision 1). Default: catch about a third of draws with at most one point of accuracy loss.
- The threshold is tuned on 2022/23 only, then reported on 2023/24, the holdout and 2026/27 so far.
- Draw features (recent draw rate, low-scoring tendency, rating closeness, league draw rate) are kept only if log loss improves (ADR 007 promotion rule).

---

## 3. Scoreline predictions (W5)

### 3.1 Goal

For any fixture the app can already predict, show:

- the five most likely scores with probabilities;
- expected goals for each side;
- chances of both teams scoring, over 1.5, 2.5 and 3.5 goals, and each clean sheet;
- plain-language reasons from team attack and defence strengths.

Non-goals: betting tips, odds comparison in the app, and live in-play updates.

### 3.2 Model: time-weighted Dixon-Coles, per league

- **Model.** Home goals ~ Poisson(λ) and away goals ~ Poisson(μ), with λ = exp(home advantage + attack(home) − defence(away)) and μ = exp(attack(away) − defence(home)). The Dixon-Coles correction ρ adjusts 0-0, 1-0, 0-1 and 1-1, which is where draws live.
- **Time weighting.** Each match is weighted by exp(−ξ·age in days), so recent form counts more. ξ is tuned on training seasons by rolling-origin log loss.
- **Regularisation.** A small L2 penalty pulls strengths toward the league average. Teams with few matches, such as promoted sides, start close to the mean of last season's weakest teams, consistent with the Elo rule in ADR 008.
- **Fitting.** Maximum likelihood with `scipy.optimize` (L-BFGS-B), one fit per league. About 40 teams and 80 parameters on a few thousand weighted matches take seconds.
- **Artifact.** A small JSON per league with strengths, home advantage, ρ, ξ, fit date and training window, stored alongside the XGBoost model and registered.
- **Scoring.** A 0–10 × 0–10 score grid per fixture. Every output above, plus the model's own H/D/A, is a sum over this grid in microseconds, with no feature pipeline run.

### 3.3 The architectural difference from XGBoost: freshness

XGBoost reads history through features computed at request time. A Dixon-Coles model is its parameters. To stay current it must be **refit whenever results are refreshed**. That is cheap, so W6's scheduled refresh refits it.

The evaluation must mirror that. Use a **rolling-origin backtest**: refit before each matchweek using only earlier matches, then predict that matchweek. A single fit on 2000–2022 predicting 2023/24 would understate how good the served model is, and would test a different system than the one we ship.

### 3.4 Evaluation

| Question | Metric | Baseline |
|---|---|---|
| Are score probabilities good? | Scoreline log loss; top-1 and top-3 exact-score hit rate | Independent Poisson (no ρ, no decay) |
| Are goal markets calibrated? | Brier score and reliability curve for BTTS and over 2.5 | Bookmaker over/under 2.5 odds (`Avg>2.5` and `B365>2.5` exist in the raw files) |
| Does it help H/D/A? | Log loss, RPS, draw recall | Current XGBoost; bookmaker 1X2 |
| Is it stable? | Per-league metrics; 2023/24, holdout and 2026/27 so far | — |

Using the over/under odds needs two optional columns in `ProcessedMatch`. That is a schema change, recorded in ADR 009.

**Headline pick.** The default is that XGBoost keeps the headline H/D/A and the goals model feeds the extras. A blend replaces it only if it beats XGBoost on log loss for the test and holdout seasons (section 5, decision 2).

**Honest expectations.** Top-1 exact-score hit rates of around 10–12% are typical. The value lies in the calibrated distribution, not in single guesses.

### 3.5 API

A new `POST /insights` endpoint with the same request as `/predict`. It lives in its own router and service, so predictions keep working if the goals model is missing, with a structured 503 as in `/teams`.

```json
{
  "home_team": "Arsenal", "away_team": "Man City", "model_version": "dc-20261001",
  "expected_goals": {"home": 1.42, "away": 1.31},
  "top_scores": [{"home": 1, "away": 1, "probability": 0.121}, "..."],
  "markets": {"btts": 0.54, "over_1_5": 0.74, "over_2_5": 0.49, "over_3_5": 0.27,
              "home_clean_sheet": 0.27, "away_clean_sheet": 0.24},
  "outcome": {"home": 0.41, "draw": 0.26, "away": 0.33},
  "strengths": {"home_attack": 1.38, "home_defence": 0.84, "away_attack": 1.52, "away_defence": 0.79},
  "reasons": ["Arsenal score 38% more than an average side at home", "..."]
}
```

`/predict` and `/explain` are unchanged. `/health` gains `insights_available`. `docs/api.md` is updated in the same PR.

### 3.6 App

- **Result screen sections:** a three-way probability bar with a "Draw likely" tag (from W3/W4), then Most likely scores, Expected goals, Goals and clean sheets, and Why.
- **State:** a new `InsightsUiState` (Loading, Success, Error) in `PredictionViewModel`. It is fetched in parallel with the prediction, and its failure never hides the prediction.
- **Plumbing:** `FootballApiService.getInsights`, `PredictionRepository.insights`, and new serializable models in `core-model`.
- **Standards:** every string in Compose resources, a preview for each new composable, and accessibility descriptions on bars and percentages (CLAUDE.md §7).

### 3.7 Impact analysis

| Area | Files | Change | Risk |
|---|---|---|---|
| Data schema | `ai/schemas/match.py`, `ai/providers/football_data.py` | Optional `over_2_5_odds` / `under_2_5_odds`; column map | Low; nullable fields, backfill re-run needed |
| New model | `ai/goals/` (new package: fit, predict, markets, reasons) | Dixon-Coles fit and score grid | Medium; numerical stability, handled by bounded optimisation and L2 |
| Evaluation | `ai/evaluation/` | Rolling-origin backtest, scoreline and market metrics | Medium; runtime of weekly refits (~1,700 per 26 seasons, capped to evaluation seasons) |
| Registry | `ai/model_registry/`, `ai/training/registry.py` | Register goals-model artifacts by kind | Low; additive field |
| Refresh | `ai/scripts/refresh_live_dataset.py` (W6) | Refit goals model after refresh | Low |
| Backend | `ai/backend/app/routers/insights.py`, `services/insights_service.py`, `schemas/insights.py`, `main.py`, `health.py` | New endpoint and service | Low; isolated, backwards compatible |
| API docs | `docs/api.md`, OpenAPI | New section | Low |
| App model and network | `core-model`, `core-network` | `InsightsResponse`, `getInsights` | Low |
| App feature | `feature-prediction` ViewModel, repository, result screen | New state and sections | Medium; the screen redesign is shared with W3/W4 |
| Assistant (optional) | `ai/assistant` knowledge base | Index the goals-model card so the assistant can explain it | Low; later |
| Unchanged | XGBoost training, features, `/predict`, `/explain`, SHAP | — | — |

Dependency: `scipy` is already installed through scikit-learn. It becomes an explicit dependency in `pyproject.toml`, noted in ADR 009 and the PR.

### 3.8 Testing

- **Model.** Unit tests on a synthetic league with known strengths recover parameters within tolerance. The score grid sums to 1. Markets equal grid sums. ρ affects only the four low scores. Time weighting reduces the influence of old matches.
- **Evaluation.** The rolling-origin backtest never uses a match on or after its prediction date. This is asserted in a test, the equivalent of ADR 008's parity test.
- **Backend.** Service and endpoint tests cover a known fixture, an unknown team (422), a missing model (503) and the health flag.
- **App.** ViewModel tests are written first: insights load alongside the prediction, and an insights error keeps the prediction. The repository gets a delegation test. Previews cover every new composable.
- **End to end.** Emulator run through predict, result with insights, then explain, repeating W1.

### 3.9 Delivery

| PR | Content | Done when |
|---|---|---|
| 1 | ADR 009 (goals model, schema columns, scipy) and this plan | ADR accepted |
| 2 | Schema columns, `ai/goals` model, rolling-origin evaluation and report | Beats independent Poisson on scoreline log loss; over 2.5 calibrated against bookmakers; report committed |
| 3 | `/insights` API, service, docs, refresh refit | Endpoint tests and integration test pass |
| 4 | App insights sections | ViewModel tests, previews, emulator run |

### 3.10 Risks

| Risk | Mitigation |
|---|---|
| Too few draws predicted, or overdispersion | ρ correction; compare against a bivariate or negative binomial variant only if calibration shows a gap |
| Promoted teams have little data | L2 shrinkage toward the promoted prior |
| Stale parameters in serving | Refit on every refresh; `/health` and `/insights` report the fit date |
| Users read it as betting advice | Copy says "likelihood, not a tip"; no odds shown; ethics section in the model card |
| Result screen becomes crowded | Collapsible sections; order by what fans ask first (score, then goals) |

---

## 4. Other items, briefly

- **W6 scheduled refresh.** A scheduled task runs `refresh_live_dataset`, refits the goals model, then signals the backend to reload. The reload is via a small admin endpoint or a restart, decided in W6.
- **W7 Kaggle extras.** Confirm licences first. Then run adapters, dedup (ADR 006) and ablations, keeping each extra only if log loss improves.
- **W8 more leagues.** ADR for the API contract (`competition` on requests and `/teams`), then backend and app. The model already covers them.

---

## 5. Decisions needed

1. **Draw rule objective.** **Decided 2026-09-28: tag only** ([ADR 011](../adr/011-draw-possible-tag.md)). The original default (a third of draws for at most one point) is not reachable with this model ([report](../reports/draw-handling.md)). Options: tag only **(recommended)**, a small rule catching about 10% of draws for about one point, or a third of draws for 4–5 points.
2. **Headline H/D/A pick.** **Decided 2026-09-28:** XGBoost keeps the headline pick; the goals model feeds the extras only.

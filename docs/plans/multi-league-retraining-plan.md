# Plan: Multi-League Retraining of the Match Outcome Model

**Status:** Decisions agreed (see §9); Phase 0 profile done (see §2). No code changed.
**Date:** 2026-09-28
**Branch:** `feature/multi-league-retraining`
**Scope:** Data hygiene and retraining of the XGBoost H/D/A classifier

---

## Goal

Retrain the match outcome model on clean, deduplicated, multi-season data from the top five
European leagues (Premier League, Bundesliga, La Liga, Serie A, Ligue 1), replacing today's single
2023/24 Premier League season. The new model must beat the current one on log loss for the same
2023/24 holdout, stay free of data leakage, and keep SHAP explanations working.

**Execution in short**

1. Record the scope change and data decisions as ADRs (§8, phase 1).
2. Backfill 2000/01–2025/26 for all five leagues from football-data.co.uk (phase 2).
3. Add Kaggle adapters, team-name canonicalisation, merge and dedup (phases 3–4).
4. Make features season- and league-aware (phase 5).
5. Retrain with season-based splits and compare against the current model and baselines (phase 6).
6. Test xG, FIFA ratings and Champions League fixtures one at a time (phase 7).

Each phase is its own PR and stops for review.

---

## 1. Where we are today

| Item | Current state | Evidence |
|---|---|---|
| Training data | One season: EPL 2023/24, 380 matches, football-data.co.uk | `datasets/features/feature_metadata.json` (`row_count: 380`) |
| Ingestion | One provider, one season, one division per run | `ai/scripts/ingest_football_data.py`, `ai/providers/football_data.py` |
| Canonical schema | `ProcessedMatch` (date, season, competition, teams, goals, result, stats, B365 odds) | `ai/schemas/match.py:96` |
| Features | 42 pre-match features (form, goals, rest, H2H, table, Elo, SoS) | `ai/feature_engineering/pipeline.py:43` |
| Leakage guard | Goals, shots, cards, corners, odds excluded from training | `ai/training/configuration.py:9` |
| Split | Chronological 70/15/15 by row | `ai/training/splitter.py`, ADR 003 |
| Current metrics | Test acc 0.561, log loss 0.949 (57 matches); CV acc 0.442, log loss 1.616 | `ai/models/latest/model_card.md` |

The large gap between test and CV scores, and a best iteration of 10, say the model is
data-starved. More seasons should help more than any tuning, which is the real case for this work.

A note on wording: XGBoost is not "fine-tuned" here. The plan is to **retrain from scratch** on a
larger, cleaner dataset and compare against the current model on the same holdout.

---

## 2. The four datasets

**Phase 0 profile, 2026-09-28.** Profiled from the zips in `D:\Anthropic\TestProjects\dataset`
(extracted to a scratch folder, not into the repo). The 3.2 GB enricocattaneo archive was only
partly extracted: match, FIFA team and standings files.

| # | Zip | Dataset | What it actually is | Coverage | Verdict |
|---|---|---|---|---|---|
| A | `archive(1).zip` | [saife245](https://www.kaggle.com/datasets/saife245/english-premier-league) | Raw football-data.co.uk season CSVs, plus `final_dataset.csv` with engineered columns | EPL 2000/01–2021/22, but **2018/19 has 160 of 380 rows and 2019/20 has 260** | Drop. It is a truncated copy of our existing source. The engineered file recodes results to `H`/`NH`, so it is unusable as a target |
| B | `archive.zip` | [armin2080](https://www.kaggle.com/datasets/armin2080/premier-league-matches-dataset-2021-to-2025) | FBref team-match logs: **one row per team per match** (3,800 rows = 1,900 matches). Has `xg`, `xga`, `poss`, shots, formations | EPL 2020/21–2024/25; `season` is the end year (2021 = 2020/21) | Keep as EPL cross-check and the only xG source |
| C | `archive(3).zip` | [enricocattaneo](https://www.kaggle.com/datasets/enricocattaneo/data-football-match-prediction) | Sportmonks fixtures and stats; FIFA team and player ratings; weather; standings | Top-5 leagues 2015/16–2021/22 (12,362 league matches), **2021/22 cut off at 15 Apr 2022**; 11,121 cup and European matches | Defer. FIFA ratings are the only unique signal |
| D | `archive(2).zip` | [adrianjuliusaluoch](https://www.kaggle.com/datasets/adrianjuliusaluoch/live-european-football-match-results) | football-data.org API dump, 57 columns | 10 competitions incl. top 5 and Champions League, 2023/24 to 2026/27 | Defer. Useful later for Champions League fixtures (rest days) |

**Data quality found**

- **D is 90% duplicates.** 149,261 rows but only 13,846 unique match ids, because it stores repeated
  snapshots. Of the unique matches, 10,680 are finished and the rest are scheduled, timed or postponed.
  About 1,600 rows have a kickoff timestamp in the `status` column, a column shift. Three matches are
  `AWARDED`, and 11 cup games went to extra time or penalties.
- **B needs pairing.** Each match appears twice, once from each side. The `team` and `opponent` columns
  use different spellings for the same club (`Manchester United` vs `Manchester Utd`,
  `Brighton And Hove Albion` vs `Brighton`, `Nottingham Forest` vs `Nott'ham Forest`). The two rows
  of each match must agree on score and xG, which is a useful self-check. `attendance` is 18% null
  (COVID season).
- **C quality.** All kickoff times are stored in `Europe/Rome`, not local time. There are 4 rows where
  `scores_ft_score` disagrees with the goal columns, and 1 duplicate league fixture. The FIFA team file
  has 82,338 rows but 53,119 duplicate (team, date) pairs and some unparseable dates. Its 424 club
  names are FIFA spellings, a third naming scheme to map.
- **Naming schemes to reconcile:** football-data (`Man United`), FBref (two variants),
  football-data.org (`Manchester United FC`), Sportmonks (`Manchester United`) and FIFA.

**What this means.** Every result in A, B, C and D is also in football-data.co.uk, which covers all
five leagues from 2000/01 to 2025/26. The Kaggle sets add three things football-data lacks: xG
(B, EPL only, 5 seasons), FIFA ratings (C, 7 seasons) and Champions League fixtures (C, D).
All three cover only part of the training window, so they are ablations after the baseline,
not part of it.

---

## 3. Target canonical model

Keep `ProcessedMatch` as the single downstream schema and add provenance fields
(schema change, so it needs an ADR):

| New field | Purpose |
|---|---|
| `source` | `football_data`, `kaggle_armin2080`, … |
| `source_version` | Kaggle dataset version or download timestamp |
| `source_row_id` | Row index or native id in the raw file, for traceability |
| `match_key` | Deterministic key, see §4.2 |
| `kickoff_time` | Optional; needed for deterministic same-day ordering |

Optional extension tables (not in `ProcessedMatch`, joined by `match_key`) for data only some
sources have: `match_advanced_stats` (xG, possession) and `team_ratings_asof` (FIFA ratings with
an `effective_from` date).

### 3.1 Column mapping (confirmed in Phase 0)

| Canonical | football-data | B (armin2080) | C (enricocattaneo `match_cleaned.csv`) | D (football-data.org) |
|---|---|---|---|---|
| `match_date` | `Date` (dd/mm/yy, some seasons dd/mm/yyyy) | `date` (ISO) + `time` | `time_starting_at_date_time` in Europe/Rome, convert to local | `utcDate` (UTC), convert to local |
| home / away | `HomeTeam` / `AwayTeam` | row with `venue == Home`: `team` / `opponent` | `home_name` / `away_name` | `homeTeam.name` / `awayTeam.name` (ids also available) |
| goals | `FTHG` / `FTAG` | home row `gf` / `ga` | `scores_home_score` / `scores_away_score` | `score.fullTime.home/away` |
| `result` | `FTR` | derive from goals | derive from goals | derive from goals |
| stats | `HS`, `HST`, `HC`, `HY`, `HR`… | `xg`, `xga`, `poss`, `sh`, `sot` | `home_shots_total`, `home_shots_ongoal`, … | half-time score only |
| odds | `B365H/D/A` and others | none | separate odds files | none |
| `competition` | division code (`E0`, `D1`, `SP1`, `I1`, `F1`) | constant Premier League | `league_name`, filter `league_type == domestic` | `competition.code`, filter `competition.type == LEAGUE` |
| `season` | from the download URL | `season` end year minus one | `season_name` | `source_season` = start year |
| status filter | none needed | none needed | none seen | keep `status == FINISHED` only |

Rule: every source gets its own adapter that emits canonical rows. No source-specific column ever
reaches the feature pipeline.

---

## 4. Data hygiene pipeline

```
raw (immutable, per source, checksummed)
  -> profile report            (Phase 0)
  -> source adapter            (rename, type, parse dates)
  -> row-level cleaning        (§4.1)
  -> team-name canonicalisation (§4.3)
  -> season integrity checks    (§4.4)
  -> cross-source merge + dedup (§4.2)
  -> datasets/processed/unified/match_results_v<ts>.csv + merge report
  -> feature pipeline -> training
```

### 4.1 Row-level cleaning

- Encoding: football-data files are latin-1; normalise everything to UTF-8 and NFC, strip whitespace.
- Dates: parse per source with an explicit format; never let pandas guess day/month order. Convert
  timestamps to the match's local date (UTC kickoffs after midnight shift the date otherwise).
- Drop fully empty rows (already done for football-data).
- Unplayed matches: rows with null scores, "Postponed", "Cancelled", "Abandoned" or future dates go
  to a quarantine file, not into training. Awarded or walkover results are flagged and excluded.
- Consistency: `result` must agree with goals; half-time goals ≤ full-time goals; shots on target ≤
  shots; no negative counts; odds > 1.0 and implied overround roughly 1.00–1.30.
- Types: goals and counts as integers; odds as floats.
- **Failures are loud.** The current `MatchNormalizer` silently skips and counts bad rows
  (`ai/schemas/match.py:218`). For multi-source data I propose a threshold: more than 0.5% failed
  rows in any source/season fails the run, and every skipped row is written to a rejects file with a reason.

### 4.2 Deduplication

Within one league season, each ordered (home, away) pair plays exactly once. That gives a natural key
that is immune to date disagreements between sources:

```
match_key = competition | season | home_team_canonical | away_team_canonical
```

Steps:
1. Exact duplicates within a source: drop and count.
2. Key duplicates within a source: error (it means a bad season label or a cup match leaking in).
3. Cross-source: group by `match_key`. Pick one row by source precedence
   (football-data > A > B > C > D). Compare the others field by field.
   - Goals or result disagree: quarantine the match and fail the run until resolved.
   - Dates differ by more than 1 day: warn (rescheduled fixture or timezone); keep the preferred source.
   - Stats disagree: keep preferred source, log the difference.
4. Emit a merge report: rows per source, matches contributed per source, overlaps, conflicts.

Cup and European fixtures (in C and D) do not fit this key. They are kept in a separate table used
only for rest-day and fatigue features, never as training rows for the league model.

**Dedup must happen before any train/test split**, otherwise the same match from two sources can
land in both train and test.

### 4.3 Team-name canonicalisation

- One versioned alias table, `datasets/schemas/team_aliases.csv`: `team_id, canonical_name, source, source_name`.
  Examples: `Man United` / `Manchester United` / `Manchester Utd`; `Nott'm Forest` /
  `Nottingham Forest`; `Wolves` / `Wolverhampton Wanderers`; `Spurs` / `Tottenham`.
- Any unmapped name fails the run and prints the name and source. No fuzzy matching at runtime;
  fuzzy matching is only a helper to propose new alias rows for human review.
- Canonical names match what football-data uses today, so the existing model, SHAP artefacts and
  API inputs keep working.

### 4.4 Season integrity checks (EPL)

Per season after merging: 20 teams, 380 matches, each team 19 home and 19 away, each ordered pair
once, all dates inside the season window. Promoted and relegated sets must be consistent with the
neighbouring seasons. Exception: 2019/20 has a COVID pause and late fixtures, which should be
whitelisted, not "fixed".

### 4.5 Schemas and validation

- Pydantic schema per source adapter output plus the canonical `ProcessedMatch`.
- Validation runs after every transformation step, per CLAUDE.md §6 and §12.
- Every processed file gets a metadata JSON: sources, versions, checksums, licence, row counts, rejects.

---

## 5. Leakage review

| Risk | Where | Mitigation |
|---|---|---|
| Post-match stats as features (shots, xG, possession, cards) | All sources | Already excluded; new stats only enter as lagged rolling features (`shift(1)`) |
| Betting odds | A, B, C | Keep excluded from features. Use implied probabilities only as a **benchmark** |
| Precomputed features in Kaggle files (form, points, standings) | A's combined file, C | Ignore them; recompute everything with our pipeline from raw results |
| FIFA ratings dated after the match | C | Join ratings with an `effective_from` ≤ match date; never use end-of-season ratings |
| End-of-season standings or table columns | B, C | Drop; the pipeline builds its own running table |
| Same match in train and test via two sources | All | Dedup before split (§4.2) |
| Imputation using future data | Training | Keep training-set-only medians (already the case) |
| Same-day ordering | Feature pipeline | Sort by date, then kickoff time, then `match_key` so reruns are deterministic |

### 5.1 Feature pipeline changes that multi-season data requires

These are existing assumptions that break with more than one season:

- `LeaguePositionFeature` never resets its points table (`ai/feature_engineering/features/league_position.py:50`).
  Across seasons, positions and points would accumulate. It must be keyed by (competition, season).
- `RestDaysFeature` will return ~90 days for the first match after a summer break
  (`rest_days.py:34`). Cap it, or reset at season start, and add a "first match of season" flag.
- `EloRatingFeature` carries ratings across seasons, which is good, but should regress towards the mean
  between seasons (for example one third) and give promoted teams a below-average start rather than 1500.
- Rolling form windows spanning two seasons are acceptable but should be a conscious choice; I'd keep
  them and add a season-start flag.
- Multi-league (only if C is adopted): Elo pools are not comparable across leagues; add league as a
  feature or train per league.

---

## 6. Splits and evaluation

- Replace the 70/15/15 row split with **season-based** splits (needs a new ADR superseding the
  "inapplicable" note in ADR 003):
  - Train: 2000/01 to 2021/22, all five leagues
  - Validation (early stopping): 2022/23
  - Test: 2023/24 (same season as today, so the EPL slice is directly comparable)
  - Out-of-time check: 2024/25 and 2025/26 held back until the very end
  - Metrics reported overall and per league
- Cross-validation: expanding-window by season (walk-forward), not `TimeSeriesSplit` over rows.
- Metrics: **log loss and ranked probability score are primary** (we serve probabilities); Brier,
  accuracy, weighted F1 and a calibration curve are secondary.
- Baselines on the same test rows: always-home, class priors, the current model, and bookmaker
  implied probabilities (the realistic ceiling).
- Comparison to the current model must use the same 57 end-of-season 2023/24 matches it was tested on,
  plus the full 2023/24 season. The current test set is small, so report bootstrap confidence intervals.
- Ablations: (1) more seasons only, (2) plus season-aware feature fixes, (3) plus new features (xG, ratings).
  This shows which change actually helped.
- Promotion rule: new model ships only if log loss improves on the 2023/24 test set and the 2024/25
  out-of-time season with non-overlapping confidence intervals, and SHAP output still works.

---

## 7. Licensing and data governance

| Source | Licence status | Action |
|---|---|---|
| football-data.co.uk | Free for non-commercial use (recorded in `providers/football_data.py`) | Keep; cite in model card |
| A saife245 | Kaggle licence TBC; underlying data is football-data.co.uk | Check page; prefer original source |
| B armin2080 | Kaggle licence TBC; upstream source TBC | Check page and upstream terms before use |
| C enricocattaneo | Kaggle licence TBC; built from Sportmonks API (commercial) and scraped FIFA ratings (EA content) | Highest risk; confirm terms before use |
| D live results | Kaggle licence TBC; likely scraped | Check terms; pin a version |

Regardless of licence: raw files stay out of git (as today), each metadata JSON records source URL,
licence and download date, and the model card lists every data source.

---

## 8. Phased delivery (one PR each, per CLAUDE.md)

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Profile | **Done 2026-09-28** (§2). Still to do: confirm each Kaggle page's licence, and copy the approved zips into `datasets/raw/kaggle/<slug>/` with checksums | Licences confirmed |
| 1. ADRs | **Done 2026-09-28.** ADR 005 top-five leagues and sources; ADR 006 team canonicalisation and dedup; ADR 007 season-based split (supersedes ADR 003's mechanism); CLAUDE.md non-goal amended | Accepted |
| 2. History backfill | **Done 2026-09-28.** 130 season files, 46,709 matches, all integrity checks pass. Extend the football-data provider to `E0, D1, SP1, I1, F1`; ingest 2000/01–2025/26; add multi-season, multi-league merge | Per-league season integrity checks pass |
| 3. Kaggle adapters | One adapter per approved source, with tests, alias table, rejects file | Cleaning and schema tests pass |
| 4. Merge and dedup | Unified processed dataset plus merge/conflict report | Zero unresolved conflicts |
| 5. Feature fixes | **Done 2026-09-28.** Season-aware league position (snapshotted per match day), per-season rest days, per-league Elo with season carryover, one-pass head-to-head, deterministic sort. Five-league matrix: 46,709 rows. Runs before phases 3–4, since the baseline needs only football-data.co.uk | Feature validation passes; 2023/24 output unchanged except league position (same-day fix) |
| 6. Retrain and evaluate | **Done 2026-09-28.** Tuned by season CV (depth 3, learning rate 0.03, 400 trees) and promoted as `20260928_120015`: log loss 0.808 vs 0.949 on the current model's test matches (interval −0.22 to −0.06); 0.975 on 2023/24 and 0.995 on the holdout; bookmaker about 0.02 better. See [comparison report](../reports/multi-league-retraining-comparison.md) | Promotion rule in §6 |
| 7. Optional new features | Rolling xG (if B has it), FIFA ratings as-of (if C is approved), European-fixture fatigue (C/D) | Each must improve log loss in ablation |

Each phase is one task and stops for review before the next.

---

## 9. Decisions (recorded 2026-09-28)

| # | Question | Decision |
|---|---|---|
| 1 | League scope | **Top-5 leagues**: Premier League, Bundesliga, La Liga, Serie A, Ligue 1 |
| 2 | History source | **football-data.co.uk directly**; saife245 mirror dropped |
| 3 | Odds | **Benchmark only**, never a feature |
| 4 | First retrain | Recommended path: football-data.co.uk top-5 history as the backbone, armin2080 as an EPL cross-check (and xG if it has it). enricocattaneo and the live dataset deferred to Phase 7 |
| 5 | Kaggle access | Zips supplied in `D:\Anthropic\TestProjects\dataset`; profiled in §2 |

### 9.1 Keep 2023/24 in the data

Retraining builds a new model from scratch; it does not add to the existing one. If 2023/24 were
left out, the new model would never learn from it, the Elo, form and head-to-head features for
2024/25 would have a one-season hole, and we would lose the only season we can use for a like-for-like
comparison with today's model. So 2023/24 stays in, as the test season.

### 9.2 What the top-5 decision changes

- **Governance.** CLAUDE.md lists "covering leagues beyond the initial scoped dataset" as a non-goal.
  ADR 005 should record the scope change, and the non-goal line should be updated in the same PR.
- **Ingestion.** football-data.co.uk already publishes all five leagues with the same columns
  (`E0`, `D1`, `SP1`, `I1`, `F1`) from 2000/01 onward. The provider only allows English divisions
  today (`ai/providers/football_data.py:53`) and `DIVISION_TO_COMPETITION` is English-only
  (`ai/schemas/match.py:20`). Both need the four extra codes. Around 30,000 matches in total.
- **Season integrity checks become per league.** Bundesliga has 18 teams and 306 matches;
  Ligue 1 dropped from 20 to 18 teams in 2023/24; Serie A and La Liga have 20.
  Expected team counts go in a small config table, not in code.
- **Team aliases** grow to roughly 200 clubs across five leagues. Same fail-loud rule.
- **Features.**
  - League position, points and matches played keyed by (competition, season).
  - Elo pools kept per league (no cross-league games in this data), so absolute Elo is not comparable
    across leagues. Add `competition` as a categorical feature and a per-league home-advantage rate.
  - Head-to-head is naturally per league apart from rare cross-league promotions; no change needed.
- **Evaluation.** Report every metric per league as well as overall. A single pooled model is the
  default; per-league models are an ablation, not the starting point.
- **Serving.** The prediction API and app assume EPL teams. Supporting other leagues there is a
  separate task after the model work; nothing in this plan changes the API contract.
- **Why armin2080 still matters.** With football-data covering results for all five leagues, its
  value is as an independent EPL check on scores and dates, and any extra stats (xG) for EPL.
  If Phase 0 shows it has nothing football-data lacks, we drop it.

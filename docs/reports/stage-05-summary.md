# Stage 05 — Real Dataset Ingestion & Canonical Schema: Summary

**Date:** 2026-06-30
**Branch:** `feature/ai-stage5-ingestion-pipeline`
**Commit:** `feat(ai): implement football-data ingestion pipeline`
**PR target:** `develop`

---

## Executive Summary

Stage 05 delivers an end-to-end ingestion pipeline for football-data.co.uk.
It downloads the 2023/24 English Premier League season (380 matches), validates
the data with composable rules, converts every row to a canonical
`ProcessedMatch` schema, and saves raw bytes, canonical CSV, and a metadata
sidecar. A CLI entry point (`python -m scripts.ingest_football_data`) runs
the full pipeline in under 2 seconds. All 142 unit tests pass. Ruff, Black,
and MyPy all report clean.

---

## Architecture Decisions

### 1. IngestionPipeline does not reuse DatasetDownloader

`DatasetDownloader` (Stage 04) saves the intermediate platform-column
DataFrame to `processed/`. `IngestionPipeline` (Stage 05) needs to save the
canonical `ProcessedMatch` DataFrame instead. Rather than extending or
modifying the downloader, the pipeline owns the full flow: download → parse →
validate → canonicalise → store. Both classes remain independently useful.

**Consequence:** No change to the Stage 04 `DatasetDownloader` API.

### 2. Separate RawMatch and ProcessedMatch schemas

`RawMatch` mirrors the provider's normalised column names (e.g.
`home_goals_ft`, `result_ft`). `ProcessedMatch` uses semantic canonical names
(e.g. `full_time_home_goals`, `result`) with a parsed `date` type and
competition metadata. This separation means the provider layer and the
modelling layer each have a schema that fits their vocabulary.

**Consequence:** Schema evolution at either layer does not force changes to
the other.

### 3. MatchNormalizer skips failing rows rather than aborting

Row-level failures (bad dates, invalid literals) are caught, counted as
`failed_rows`, and skipped. The pipeline only aborts if ALL rows fail. This
makes the pipeline resilient to sporadic bad data in otherwise valid downloads.

**Consequence:** Partial ingestion is possible. The caller knows the failure
count and can decide whether it is acceptable.

### 4. CLI imports are deferred inside main()

All domain imports in `scripts/ingest_football_data.py` are inside `main()`.
This keeps the module importable before dependencies are installed and makes
the `--help` flag respond instantly without loading the full dependency tree.

---

## Files Created

| File | Purpose |
|---|---|
| `ai/schemas/match.py` | `RawMatch`, `ProcessedMatch` schemas; `MatchNormalizer`; `parse_match_date`, `season_label` helpers |
| `ai/ingestion/pipeline.py` | `IngestionPipeline`, `PipelineResult`; full download → canonicalise flow |
| `ai/scripts/__init__.py` | Package marker (makes `python -m scripts.X` work) |
| `ai/scripts/ingest_football_data.py` | CLI entry point with argparse |
| `ai/tests/schemas/test_match.py` | 24 schema and normalizer tests |
| `ai/tests/ingestion/test_pipeline.py` | 12 pipeline unit tests + 1 integration test |
| `docs/reports/stage-05-summary.md` | This document |

### Updated files

| File | Change |
|---|---|
| `ai/schemas/__init__.py` | Exported all public names from `schemas.match` |
| `ai/pyproject.toml` | Added `scripts` to packages, mypy, isort, coverage; added `integration` pytest marker |

---

## Tests Added

| File | Tests | What is covered |
|---|---|---|
| `tests/schemas/test_match.py` | 24 | Date parsing, season labels, RawMatch/ProcessedMatch validation, MatchNormalizer row and DataFrame paths |
| `tests/ingestion/test_pipeline.py` | 12 (unit) + 1 (integration, skipped) | Successful runs, file creation, canonical output structure, validation failures, extra rules |
| **New total** | **35** | |

**Grand total: 142 passed, 1 integration test deselected.**

---

## Build Verification

```
uv run black --check .   → 46 files unchanged
uv run ruff check .      → All checks passed
uv run mypy .            → Success: no issues found in 46 source files
uv run pytest -m "not integration"  → 142 passed in 1.88s
uv run python -m scripts.ingest_football_data --season 2324 --division E0
  → 380 rows ingested, 0 failed, 3 files written in 1.9s
```

---

## CLI Output

```
Football Intelligence Platform — Data Ingestion
================================================
Provider:    football-data.co.uk
Competition: Premier League
Season:      2023/24
Output dir:  datasets

Downloading... Done (1.9s)

Rows ingested:  380

Raw dataset:    datasets/raw/football_data/match_results_v20260630_090657.csv
Processed:      datasets/processed/football_data/match_results_v20260630_090657.csv
Metadata:       datasets/raw/football_data/match_results_v20260630_090657_metadata.json
Version:        20260630_090657
Checksum:       b2e057b0...
```

---

## Processed Dataset Schema

The canonical `ProcessedMatch` CSV contains 25 columns:

| Column | Type | Source |
|---|---|---|
| `match_date` | `date` (YYYY-MM-DD) | Parsed from provider `date` |
| `season` | `str` | Derived from season_code parameter |
| `competition` | `str` | Mapped from division code |
| `home_team` | `str` | Provider `home_team` |
| `away_team` | `str` | Provider `away_team` |
| `full_time_home_goals` | `int` | Provider `home_goals_ft` |
| `full_time_away_goals` | `int` | Provider `away_goals_ft` |
| `result` | `"H"\|"D"\|"A"` | Provider `result_ft` |
| `half_time_home_goals` | `int?` | Provider `home_goals_ht` |
| `half_time_away_goals` | `int?` | Provider `away_goals_ht` |
| `home_shots` | `int?` | Provider `home_shots` |
| `away_shots` | `int?` | Provider `away_shots` |
| `home_shots_on_target` | `int?` | Provider `home_shots_on_target` |
| `away_shots_on_target` | `int?` | Provider `away_shots_on_target` |
| `home_fouls` | `int?` | Provider `home_fouls` |
| `away_fouls` | `int?` | Provider `away_fouls` |
| `home_corners` | `int?` | Provider `home_corners` |
| `away_corners` | `int?` | Provider `away_corners` |
| `home_yellow_cards` | `int?` | Provider `home_yellow_cards` |
| `away_yellow_cards` | `int?` | Provider `away_yellow_cards` |
| `home_red_cards` | `int?` | Provider `home_red_cards` |
| `away_red_cards` | `int?` | Provider `away_red_cards` |
| `home_odds` | `float?` | Provider `odds_b365_home` |
| `draw_odds` | `float?` | Provider `odds_b365_draw` |
| `away_odds` | `float?` | Provider `odds_b365_away` |

---

## Known Limitations

1. **Single competition only.** The CLI defaults to EPL (E0) 2023/24. Multi-
   season and multi-competition ingestion are not yet scripted.

2. **No deduplication across runs.** Running the CLI twice writes a second
   versioned dataset. Deduplication or version pinning is a future concern.

3. **Odds are Bet365 only.** The provider normalises B365 odds. Other
   bookmaker odds columns in the source CSV (Pinnacle, William Hill, etc.)
   are discarded. They can be added to `ProcessedMatch` when needed.

4. **`scripts/` package in wheel.** The `scripts` package is included in the
   wheel packages list so mypy and ruff can inspect it. CLI scripts are
   typically not distributed in wheels; if the package is ever published,
   `scripts` should be moved to a console_scripts entry point.

---

## Next Stage Recommendation

**Stage 6 — Preprocessing & Feature Engineering:** apply transforms to the
canonical `ProcessedMatch` dataset (rolling averages, form metrics, xG
proxies). Write the preprocessed dataset to `processed/{provider}/features/`.
All transforms must be reproducible scripts. Evaluation: schema validation
tests on the output dataset.

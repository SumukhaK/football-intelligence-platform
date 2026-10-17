# Data and Feature Commands

Run from `ai/` unless a section says otherwise. [CLI index](cli.md). Shell examples use POSIX syntax; on Windows set environment variables with `$env:NAME="value"` before running the command.

## Data Ingestion

### `python -m scripts.refresh_live_dataset`

Appends the played matches of the season in progress to the newest completed-season dataset and writes `processed/football_data/match_results_live_v<timestamp>.csv`, which the backend loads at startup (ADR 008). Dry run unless `--confirm` is given.

```sh
uv run python -m scripts.refresh_live_dataset --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--season CODE` | the season today falls in | Season in progress, e.g. `2627`. |
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Leagues to include. |
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--confirm` | off | Download and write. |

Raw snapshots are stored once per division per day under `raw/football_data/match_results_in_progress/`. On success it prints the matches played so far, the last match date and the written path; on failure it prints `FAILED: <reason>` and exits with code 1. Restart the backend afterwards.

When enabled (the local default), the backend runs the same refresh every day at `LIVE_REFRESH_HOUR` (default 6; `off` turns it off), so you only need this command when the daily refresh is off or has failed (ADR 013).

---

### `python -m scripts.refresh_fixtures`

Downloads the five leagues' upcoming fixtures from openfootball and writes `processed/openfootball/fixtures_v<timestamp>.csv`, which `/v2/fixtures` serves (ADR 015). Dry run unless `--confirm` is given.

```sh
uv run python -m scripts.refresh_fixtures --confirm
```

| Flag | Default | Description |
|---|---|---|
| `--base-dir DIR` | `../datasets` | Datasets base directory. |
| `--confirm` | off | Download and write. |

Prints the number of upcoming fixtures per league and the written path, or `FAILED: <reason>` with exit code 1. The daily refresh also updates fixtures. Restart the backend afterwards.

---

### `python -m scripts.build_team_crests`

Rebuilds `datasets/schemas/team_crests.csv` and `league_emblems.csv`, the crest URL per team and league that the crest redirects serve (ADR 020). Takes no options.

```sh
uv run python -m scripts.build_team_crests
```

Reads the newest `match_results_top5_v*.csv`, the newest fixtures file and the football-data.org snapshot at `../datasets/raw/kaggle/adrianjuliusaluoch_live_results/football_matches.parquet`. Teams are matched by the games they played, from 2022/23 on, not by spelling. Prints the number of crests and emblems written and the teams left without a crest; the app shows a placeholder for those.

---

### `python -m scripts.backfill_football_data`

Backfills many seasons for the top five leagues (ADR 005), checks every season's integrity (ADR 006), and writes one combined dataset. Runs as a dry run unless `--confirm` is given.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--divisions DIV ...` | `E0 D1 SP1 I1 F1` | Division codes to include. |
| `--first-season CODE` | `0001` | First season code, `0001` = 2000/01. |
| `--last-season CODE` | `2526` | Last season code, inclusive. |
| `--base-dir DIR` | `datasets/` (relative to `ai/`) | Override the datasets base directory. Pass `../datasets` to use the repository's `datasets/` folder, which the backend reads. |
| `--confirm` | off | Download missing files and build the dataset. Without it, only the plan is printed. |

**Examples:**
```sh
# See what would be downloaded
uv run python -m scripts.backfill_football_data --base-dir ../datasets

# Download and build all five leagues, 2000/01 to 2025/26
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
```

**Behaviour:**
- Season files already in `raw/football_data/match_results/` are reused, never re-downloaded or overwritten.
- Every season must pass the integrity checks: expected team count, each fixture played once, result consistent with goals, dates inside the season window. Ligue 1 2019/20 is whitelisted at 279 matches.
- More than 0.5% unparseable rows in any season fails the run.

**Outputs:**

| File | Location | Description |
|---|---|---|
| Raw CSVs | `datasets/raw/football_data/match_results/<DIV>_<season>.csv` | One immutable file per division season |
| Processed CSV | `datasets/processed/football_data/match_results_top5_v<ts>.csv` | All seasons, canonical `ProcessedMatch` schema, sorted by date |
| Report JSON | `datasets/processed/football_data/match_results_top5_v<ts>_report.json` | Per-season URL, checksum, row counts, errors and warnings. Written even when checks fail |

**Exit codes:** `0` on success or dry run, `1` on any failure. A failure prints `FAILED: <reason>`.

This is the first step of the served model's pipeline. See [Full Pipeline](cli.md#full-pipeline-end-to-end).

---

### `python -m scripts.ingest_football_data` (legacy, single season)

The original v0.1 ingestion: downloads one season of one league from football-data.co.uk, validates it against the `ProcessedMatch` schema, and writes a raw CSV, a processed CSV and a metadata JSON (`match_results_v<ts>`) under `raw/football_data/` and `processed/football_data/`. The served model does not use it; use `scripts.backfill_football_data` for the five-league dataset.

```sh
# Default: Premier League 2023/24
uv run python -m scripts.ingest_football_data --base-dir ../datasets

# Specify season and division explicitly
uv run python -m scripts.ingest_football_data --season 2324 --division E0
```

| Flag | Default | Description |
|---|---|---|
| `--season SEASON` | `2324` | Four-digit season code. `2324` = 2023/24 season. |
| `--division DIV` | `E0` | Division code. `E0` = Premier League. `E1` = Championship. |
| `--base-dir DIR` | `datasets/` (relative to `ai/`) | Override the datasets base directory. |

**Output:** a header (provider, competition, season, output dir), then `Downloading... Done (<seconds>s)`, the rows ingested (and `Rows skipped: N` if any rows failed normalisation), and the output paths with the dataset version and checksum. A Premier League season has 380 matches.

**Exit codes:** `0` on success, `1` on any failure (network error, validation failure, IO error). A download failure prints `Downloading... FAILED` followed by `Error: <reason>`.

---

## Feature Engineering

### `python -m feature_engineering.pipeline`

Loads the latest canonical `ProcessedMatch` CSV, executes 9 feature generators in dependency order, validates the output, and writes a Parquet feature matrix.

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--input PATH` | auto-detect latest | Path to a specific `ProcessedMatch` CSV. Without it, the pipeline picks the most recently modified `datasets/processed/football_data/match_results_v*.csv` relative to `ai/`, which only matches legacy single-season files. |
| `--output-dir DIR` | `datasets/features` | Directory to write output artifacts. |

**Examples:**
```sh
# Five-league dataset (served model)
uv run python -m feature_engineering.pipeline \
  --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv \
  --output-dir ../datasets/features/top5

# Legacy: latest single-season CSV under ai/datasets/
uv run python -m feature_engineering.pipeline
```

If no input is given and none is found, it prints `ERROR: No canonical CSV found matching '<pattern>' relative to '<dir>'.` and exits with code 1.

**Inputs:** The canonical `ProcessedMatch` CSV produced by `scripts.backfill_football_data` (or the legacy ingestion).

**Outputs:**

| File | Location | Description |
|---|---|---|
| Feature matrix | `<output-dir>/feature_matrix.parquet` | 42 pre-match engineered features (Parquet) |
| Feature metadata | `<output-dir>/feature_metadata.json` | Per-feature descriptions and generation report |
| Generation report | `<output-dir>/feature_generation_report.json` | Pipeline execution report with timing and row counts |

**Exit codes:** `0` on success and validation passing, `1` on any error or validation failure.

**Feature generators:** goal statistics, home advantage, away form, rolling form, rest days, head-to-head, league position, Elo ratings (K=32, starting at 1500) and strength of schedule (rolling opponent Elo), run in dependency order.

**Sample output:**
```
Input:      ../datasets/processed/football_data/match_results_top5_v<ts>.csv
Output dir: ../datasets/features/top5

Pipeline complete in <seconds>s
Rows: <N> in -> <N> out
Feature columns: <total columns>
Validation: PASSED

Outputs written to: ../datasets/features/top5
```

`Feature columns` counts every column in the matrix; 42 of them are model features.

---

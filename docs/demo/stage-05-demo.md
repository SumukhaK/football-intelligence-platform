# Demo: Stage 5 — Real Dataset Ingestion

Demonstrate live data ingestion from football-data.co.uk, schema validation, and versioned dataset storage.

**Approximate demo time:** 3 minutes

---

## Objective

Show that the platform can:
- Download real football data from an external provider.
- Validate it against a canonical schema with 9 quality rules.
- Persist it with full provenance: version, checksum, and metadata sidecar.
- Do all of this in under 2 seconds.

---

## Prerequisites

- `ai/` workspace set up: `uv sync --extra dev`
- Internet connection

---

## Commands

All commands run from the `ai/` directory.

### 1. Show the tests pass

```sh
uv run pytest tests/ingestion/ tests/schemas/ tests/providers/ -v
```

Expected: 104 tests pass. Point out that the test suite uses a `FakeTransport` — no real network calls during tests.

### 2. Run the ingestion pipeline

```sh
uv run python -m scripts.ingest_football_data
```

### 3. Show the output files

```sh
# macOS/Linux
ls -la ../datasets/raw/football_data/
ls -la ../datasets/processed/football_data/

# Windows PowerShell
Get-ChildItem ..\datasets\raw\football_data\
Get-ChildItem ..\datasets\processed\football_data\
```

### 4. Inspect the metadata

```sh
# macOS/Linux
cat ../datasets/raw/football_data/*_metadata.json

# Windows PowerShell
Get-Content ..\datasets\raw\football_data\*_metadata.json
```

### 5. Show the schema definition

```sh
# macOS/Linux
cat schemas/match.py | head -80

# Windows PowerShell
Get-Content schemas/match.py | Select-Object -First 80
```

---

## Expected Output

```
Football Intelligence Platform — Data Ingestion
================================================
Provider:    football-data.co.uk
Competition: Premier League
Season:      2023/24
Output dir:  datasets

Downloading... Done (1.9s)

Rows ingested:  380

Raw dataset:    datasets/raw/football_data/match_results_v<timestamp>.csv
Processed:      datasets/processed/football_data/match_results_v<timestamp>.csv
Metadata:       datasets/raw/football_data/match_results_v<timestamp>_metadata.json
Version:        <timestamp>
Checksum:       <sha256>
```

---

## Verification

After running, confirm:

- [ ] `datasets/raw/football_data/` contains a new versioned CSV
- [ ] `datasets/processed/football_data/` contains a canonical `ProcessedMatch` CSV with 25 columns
- [ ] A `_metadata.json` sidecar exists alongside the raw file
- [ ] The `Rows ingested` count is 380
- [ ] Exit code is 0 (`echo $?` on macOS/Linux; `$LASTEXITCODE` on Windows)

---

## What to Highlight

**Architecture points:**
- The `DatasetDownloader` class owns the download → parse → normalise → store flow.
- The `HttpTransport` protocol is injected, making the downloader fully testable offline.
- Raw files are immutable — every run writes a new versioned file. You can always re-derive processed data from any raw version.
- `DatasetMetadata` captures the checksum, row count, column names, and source URL alongside the data.
- Three provider implementations exist (football-data.co.uk, FBref, Understat). Adding a fourth requires only implementing `BaseProvider`.

**AI engineering points:**
- Schema validation (`DatasetValidator`) enforces 9 quality rules: no null dates, valid result codes, non-negative goals, etc.
- Failed rows are counted but do not abort the pipeline — resilience over rigidity.
- The `ProcessedMatch` schema separates provider vocabulary from domain vocabulary. Provider column names are normalised before writing.

---

## Troubleshooting

**Download fails:** Check your internet connection. The target is `https://www.football-data.co.uk/mmz4281/2324/E0.csv`.

**All rows fail validation:** The provider may have changed their CSV format. Open an issue.

**`ModuleNotFoundError`:** Run `uv sync --extra dev` first.

---

## Approximate Demo Time

| Step | Time |
|---|---|
| Run tests | 60 seconds |
| Run ingestion | 3 seconds |
| Show output files | 30 seconds |
| Explain architecture | 90 seconds |
| **Total** | **~3 minutes** |

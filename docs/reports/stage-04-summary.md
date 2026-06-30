# Stage 04 — Football Data Ingestion Framework: Summary

**Date:** 2026-06-30
**Branch:** `feature/ai-stage4-data-acquisition`
**Commit:** `feat(ai): implement extensible football data ingestion framework`
**PR target:** `develop`

---

## Executive Summary

Stage 04 delivers a production-quality, provider-agnostic data acquisition and
validation framework. No data is downloaded. The stage creates the reusable
infrastructure that every subsequent stage depends on: provider contracts for
three real data sources, composable validation rules, immutable metadata records,
and a clean storage abstraction. All 107 tests pass. Ruff, Black, and MyPy all
report clean.

---

## Architecture Decisions

### 1. Provider-transport separation

The `BaseProvider` does not perform HTTP requests. Transport is injected via the
`HttpTransport` protocol. This means provider tests require no network mocking —
they operate on fixture bytes. The production `HttpxTransport` is the only class
that calls an external URL.

**Consequence:** Every provider can be tested in isolation with no fixtures beyond
a bytes object.

### 2. Composition over inheritance in validation

`DatasetValidator` accepts a `list[ValidationRule]` (a structural Protocol), not
a base class hierarchy. New rules are added by implementing a single `apply(df) -> list[str]` method, with no registration or subclassing required.

**Consequence:** Rules are trivially composable and independently testable.

### 3. Immutable metadata records

`DatasetMetadata` uses `model_config = {"frozen": True}`. Records are constructed
once by `MetadataBuilder.build()` and never mutated. Integrity is verified by
`MetadataBuilder.verify_checksum()` before downstream use.

**Consequence:** Metadata can be safely cached, passed across boundaries, and
serialised/deserialised without risk of mutation side-effects.

### 4. Timestamp-derived dataset versions

Dataset versions use the format `YYYYMMDD_HHMMSS` derived from the UTC download
timestamp. This is sortable lexicographically and human-readable without a
version registry.

**Consequence:** Version ordering is trivial. No central version counter is
needed. Trade-off: two downloads in the same second would collide (acceptable for
this use case).

### 5. CSV format for storage

Raw files are stored as-received (bytes). Processed DataFrames are stored as CSV.
Parquet would be more efficient but requires `pyarrow`, adding a heavy dependency
before it is clearly needed. CSV can be inspected in any editor.

**Consequence:** Storage is human-reviewable. Migration to Parquet is a single
`DatasetStorage` change when scale demands it.

---

## Files Created

### New packages

| File | Purpose |
|---|---|
| `ai/config/__init__.py` | Package marker |
| `ai/config/paths.py` | `DataPaths` — all filesystem paths derived from a single base dir |
| `ai/config/settings.py` | `Settings` (pydantic-settings) — env-var configuration |
| `ai/shared/__init__.py` | Package marker |
| `ai/shared/constants.py` | Project-wide constants |
| `ai/shared/exceptions.py` | Exception hierarchy (`FootballAIError` and subclasses) |
| `ai/shared/types.py` | `NewType` aliases (`DatasetName`, `ProviderId`, etc.) |
| `ai/providers/__init__.py` | Public exports |
| `ai/providers/base.py` | `BaseProvider` ABC and `DatasetDescriptor` dataclass |
| `ai/providers/football_data.py` | football-data.co.uk CSV adapter |
| `ai/providers/fbref.py` | FBref CSV adapter |
| `ai/providers/understat.py` | Understat JSON adapter |
| `ai/providers/README.md` | Provider architecture and column convention docs |
| `ai/ingestion/downloader.py` | `DatasetDownloader`, `HttpTransport` protocol, `HttpxTransport` |
| `ai/ingestion/storage.py` | `DatasetStorage` — raw bytes, DataFrame, and metadata I/O |
| `ai/validation/dataset_validator.py` | `DatasetValidator`, `ValidationResult`, 4 rule classes |
| `ai/validation/schema_validator.py` | `SchemaValidator` — Pydantic-schema column checks |
| `ai/metadata/__init__.py` | Public exports |
| `ai/metadata/metadata.py` | `DatasetMetadata` model and `MetadataBuilder` |
| `ai/metadata/README.md` | Metadata lifecycle and field documentation |

### Updated files

| File | Change |
|---|---|
| `ai/pyproject.toml` | Added `pydantic-settings`, `httpx`; registered 5 new packages |
| `ai/README.md` | Full rewrite with provider and validation architecture |
| `ai/validation/README.md` | Updated with rule table and usage examples |

---

## Tests Added

| File | Tests | What is covered |
|---|---|---|
| `tests/conftest.py` | Fixtures | Shared DataPaths, storage, DataFrame, and bytes fixtures |
| `tests/providers/test_base.py` | 9 | `BaseProvider` contract via `_MinimalProvider` |
| `tests/providers/test_football_data.py` | 12 | URL building, CSV parsing, column normalisation |
| `tests/providers/test_fbref.py` | 9 | FBref URL, CSV parse, column normalisation |
| `tests/providers/test_understat.py` | 11 | JSON parse, flattening, normalisation, error cases |
| `tests/test_storage.py` | 7 | Raw bytes, DataFrame, version listing |
| `tests/validation/test_dataset_validator.py` | 18 | All 4 rule classes + validator orchestration |
| `tests/validation/test_schema_validator.py` | 5 | Required vs optional fields, strict mode |
| `tests/metadata/test_metadata.py` | 16 | Checksum, immutability, serialisation roundtrip |
| `tests/test_config.py` | 10 | `DataPaths`, `Settings`, env-var override |
| **Total new** | **97** | (10 bootstrap tests carried over from Stage 3) |

**Grand total: 107 tests, 107 passed.**

---

## Build Verification

```
uv sync --extra dev      → 52 packages resolved, 9 new installed
uv run black --check .   → 38 files unchanged
uv run ruff check .      → All checks passed
uv run mypy .            → Success: no issues found in 38 source files
uv run pytest            → 107 passed in 5.65s
```

---

## Documentation Updated

- `ai/README.md` — complete rewrite: provider architecture diagram, validation
  architecture table, metadata field table, getting-started commands.
- `ai/validation/README.md` — updated with rule table and usage example.
- `ai/providers/README.md` — new: provider table, adding-a-provider guide,
  column naming convention.
- `ai/metadata/README.md` — new: field table, sidecar storage convention,
  contracts.
- `docs/reports/stage-04-summary.md` — this document.

---

## Known Limitations

1. **No FBref HTML parsing.** FBref's CSV export format assumes the user has
   already navigated to the table export URL. The HTML-embedded format (used
   by scrapers) requires `beautifulsoup4` or `lxml`, which are not yet
   dependencies. The `parse()` method handles CSV correctly.

2. **Understat requires pre-extracted JSON.** Understat embeds match data as a
   JavaScript variable in HTML. The downloader would need an extraction step
   (regex or HTML parsing) before calling `provider.parse()`. This is noted
   in the module docstring.

3. **No retry logic.** `HttpxTransport.get()` does not implement retries.
   The `settings.http_max_retries` field is defined but not wired up.

4. **Single storage format.** DataFrames are stored as CSV. Large datasets would
   benefit from Parquet, but this is deferred until scale demands it.

---

## Technical Debt

- `HttpxTransport` retry logic is not implemented (setting exists, behaviour
  does not). Tracked as a known limitation.
- `DatasetDownloader.fetch()` does not call `DatasetValidator` after parse.
  Validation is a caller responsibility for now. A follow-up task should wire
  validation into the download cycle.

---

## Next Stage Recommendation

**Stage 5 — Dataset Ingestion:** implement real data downloads using the
`FootballDataProvider` and the `DatasetDownloader`. Define Pydantic schemas
for `RawMatch` and `ProcessedMatch` in `schemas/`. Run the ingestion pipeline
against at least one season of English Premier League data. Write preprocessing
transforms in `preprocessing/`. All schema and preprocessing code must pass
validation before the dataset is considered production-ready.

# AI

Data engineering, machine learning, explainability, and retrieval-augmented generation for the Football Intelligence Platform.

---

## Ownership

AI and data engineering implementation. Follows `.claude/CLAUDE.md` sections 5 and 6.

---

## Responsibilities

This directory owns:

- Raw data ingestion and schema validation.
- Feature engineering for model training.
- XGBoost model training and serialisation.
- SHAP explainability — every prediction includes a SHAP explanation.
- Retrieval-augmented generation pipeline using Ollama.
- Prompt templates and retrieval configuration.
- Evaluation scripts: prediction accuracy, assistant faithfulness, hallucination rate.

---

## Directory Structure

```
ai/
  config/               # Settings (pydantic-settings) and path layout
  shared/               # Common types, exceptions, and constants
  providers/            # Data provider adapters (football-data.co.uk, FBref, Understat)
  ingestion/            # Downloader (HTTP + storage orchestration) and storage layer
  validation/           # DataFrame-level rules and schema compatibility checks
  preprocessing/        # Cleans validated data into datasets/processed/
  feature_engineering/  # Computes model-ready features from preprocessed data
  schemas/              # Pydantic schema definitions for all datasets
  metadata/             # DatasetMetadata model and MetadataBuilder
  scripts/              # Operational CLI scripts (setup, pipeline triggers)
  tests/                # Unit tests mirroring source structure
  training/             # XGBoost training scripts (Stage 5)
  evaluation/           # Evaluation harness for model and assistant quality (Stage 6)
  inference/            # Inference wrappers used by the backend (Stage 5)
  rag/                  # Retrieval pipeline: indexing, search, context assembly (Stage 3)
  prompts/              # Prompt templates (source of truth is playbook/)
  datasets/             # Symlinks or references to datasets/processed/
  models/               # Serialised model artefacts (gitignored by default)
```

---

## Provider Architecture

The ingestion pipeline is built around a provider abstraction:

```
DatasetDownloader
  │
  ├─ provider.get_descriptor(dataset_name)   → DatasetDescriptor
  ├─ provider.build_url(dataset_name)        → str (download URL)
  ├─ transport.get(url)                      → bytes (raw content)
  ├─ provider.parse(content, dataset_name)   → DataFrame (native columns)
  ├─ provider.normalise_columns(df)          → DataFrame (platform columns)
  ├─ MetadataBuilder.build(...)              → DatasetMetadata
  ├─ DatasetStorage.save_raw(...)            → Path
  ├─ DatasetStorage.save_dataframe(...)      → Path
  └─ DatasetStorage.save_metadata(...)       → Path
```

The HTTP transport (`HttpTransport` protocol) is injected, so tests use a `FakeTransport` without network access.

**Supported providers:**

| Provider | ID | Datasets | Format |
|---|---|---|---|
| football-data.co.uk | `football_data` | `match_results` | CSV |
| FBref | `fbref` | `scores_and_fixtures`, `squad_standard_stats` | CSV |
| Understat | `understat` | `match_results` | JSON |

---

## Validation Architecture

```
DatasetValidator            — orchestrates rules against a DataFrame
  ├─ RequiredColumnsRule    — fails if any required column is absent
  ├─ NullConstraintRule     — fails if non-nullable columns contain nulls
  ├─ DuplicateRowRule       — fails if duplicate ratio exceeds threshold
  └─ RowCountRule           — fails if row count is below minimum

SchemaValidator             — validates column compatibility with a Pydantic schema
  ├─ validate()             — warns on extra columns, errors on missing required ones
  └─ validate_strict()      — extra columns are errors, not warnings
```

---

## Metadata Lifecycle

Every ingested dataset produces a `DatasetMetadata` record:

| Field | Description |
|---|---|
| `provider_id` | Provider that supplied the data |
| `dataset_name` | Dataset name as declared by the provider |
| `source_url` | Exact URL the content was fetched from |
| `downloaded_at` | UTC timestamp of the download |
| `checksum` | SHA-256 hex digest of raw bytes |
| `schema_version` | Data contract version at time of ingest |
| `dataset_version` | Timestamp-derived sortable version string |
| `license` | Data license from the provider |
| `row_count` | Rows in the normalised DataFrame |
| `column_count` | Columns in the normalised DataFrame |
| `columns` | Ordered list of column names |

Metadata is stored as a JSON sidecar alongside the raw file:
`datasets/raw/{provider_id}/{dataset_name}_v{version}_metadata.json`

---

## Getting Started

Requires Python 3.12. Managed with [uv](https://github.com/astral-sh/uv).

```sh
cd ai

# Install all dependencies (including dev tools)
uv sync --extra dev

# Run linting
uv run ruff check .

# Check formatting
uv run black --check .

# Run type checking
uv run mypy .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov --cov-report=term-missing
```

---

## AI Philosophy

- The assistant never invents facts. Every response is grounded in retrieved data or model output.
- SHAP values accompany every prediction.
- Prompt templates are version-controlled and tested.
- Model selection favours the smallest Ollama model that meets quality thresholds.
- Fine-tuning and LoRA are out of scope. Improve quality through better retrieval and better prompts.
- No model is merged without a passing evaluation run.

---

## Future Responsibilities

- Multi-league data support.
- Player-level prediction (not just match-level).
- Structured evaluation dashboard.
- Retrieval quality benchmarking against labelled question sets.

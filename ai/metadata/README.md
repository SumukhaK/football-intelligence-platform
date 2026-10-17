# metadata

Dataset provenance records for the ingestion pipeline.

## Responsibility

The generic downloader and legacy single-season pipeline produce an immutable `DatasetMetadata`
record. Multi-season backfill and live refresh use per-partition provenance/check report sidecars instead. This record is the audit trail: it captures where the data came from,
when it arrived, its integrity checksum, and its schema version at ingest time.

## Key Types

- `DatasetMetadata` — immutable Pydantic model (frozen). Stored as a JSON sidecar
  alongside the raw file in `datasets/raw/{provider_id}/`.
- `MetadataBuilder` — static factory methods for constructing, saving, loading,
  and checksum-verifying metadata records.

## Metadata Fields

| Field | Type | Description |
|---|---|---|
| `provider_id` | `ProviderId` | Source provider identifier |
| `dataset_name` | `DatasetName` | Dataset name from the provider |
| `source_url` | `str` | Exact download URL |
| `downloaded_at` | `datetime` | UTC download timestamp |
| `checksum` | `Checksum` | SHA-256 hex digest of raw bytes |
| `checksum_algorithm` | `str` | Algorithm name (always `"sha256"`) |
| `schema_version` | `SchemaVersion` | Data contract version |
| `dataset_version` | `DatasetVersion` | Timestamp-derived sortable version |
| `license` | `str` | Data license from provider |
| `row_count` | `int` | Rows in the normalised DataFrame |
| `column_count` | `int` | Columns in the normalised DataFrame |
| `columns` | `list[str]` | Ordered column names |

## Sidecar Storage Convention

```
datasets/raw/{provider_id}/
  {dataset_name}_v{version}.csv               ← raw bytes
  {dataset_name}_v{version}_metadata.json     ← metadata sidecar
```

## Contracts

- `DatasetMetadata` is frozen. Records are never mutated after creation.
- `MetadataBuilder.verify_checksum` is an available verification helper; callers must invoke it explicitly. It is not automatically applied by every downstream loader.
- A metadata record with a mismatched checksum must not be used.

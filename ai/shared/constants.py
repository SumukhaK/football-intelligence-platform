"""Project-wide constants for the football AI workspace."""

from typing import Final

from shared.types import SchemaVersion

# Data schema version — increment when any schema definition changes
CURRENT_SCHEMA_VERSION: Final[SchemaVersion] = SchemaVersion("1.0.0")

# File formats supported for raw and processed datasets
SUPPORTED_RAW_FORMATS: Final[frozenset[str]] = frozenset({"csv", "json"})
DEFAULT_RAW_FORMAT: Final[str] = "csv"

# Checksum algorithm applied to raw content on ingest
CHECKSUM_ALGORITHM: Final[str] = "sha256"

# Filename used for per-dataset metadata sidecars
METADATA_FILENAME: Final[str] = "metadata.json"

# Separator between dataset name and version in filenames
# e.g. "matches_v20240101_120000"
DATASET_VERSION_SEPARATOR: Final[str] = "_v"

# Fraction of duplicate rows above which validation raises an error
MAX_DUPLICATE_RATIO: Final[float] = 0.01

# HTTP timeout in seconds applied by the downloader transport
DEFAULT_HTTP_TIMEOUT: Final[int] = 30

# Maximum number of HTTP retries before raising IngestionError
DEFAULT_HTTP_MAX_RETRIES: Final[int] = 3

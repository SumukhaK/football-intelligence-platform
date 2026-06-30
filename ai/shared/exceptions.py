"""Custom exception hierarchy for the football AI workspace."""


class FootballAIError(Exception):
    """Base exception for all football AI errors."""


class ConfigurationError(FootballAIError):
    """Raised when configuration is invalid or missing."""


class ProviderError(FootballAIError):
    """Raised when a data provider fails."""

    def __init__(self, provider_id: str, message: str) -> None:
        super().__init__(f"[{provider_id}] {message}")
        self.provider_id = provider_id


class DatasetNotFoundError(ProviderError):
    """Raised when a requested dataset is not available from the provider."""


class IngestionError(FootballAIError):
    """Raised when dataset ingestion fails."""

    def __init__(self, dataset_name: str, message: str) -> None:
        super().__init__(f"[{dataset_name}] {message}")
        self.dataset_name = dataset_name


class ValidationError(FootballAIError):
    """Raised when data fails schema or constraint validation."""

    def __init__(self, context: str, message: str) -> None:
        super().__init__(f"[{context}] {message}")
        self.context = context


class StorageError(FootballAIError):
    """Raised when reading from or writing to the dataset store fails."""


class ChecksumError(StorageError):
    """Raised when a dataset's checksum does not match the recorded value."""

    def __init__(self, dataset_name: str, expected: str, actual: str) -> None:
        super().__init__(
            f"Checksum mismatch for '{dataset_name}': "
            f"expected {expected}, got {actual}"
        )
        self.expected = expected
        self.actual = actual

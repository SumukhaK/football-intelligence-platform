"""Bootstrap tests: verify all packages import and the runtime meets requirements."""

import sys


def test_python_version() -> None:
    """Python 3.12 or later is required."""
    assert sys.version_info >= (
        3,
        12,
    ), f"Python 3.12+ required, got {sys.version_info.major}.{sys.version_info.minor}"


def test_ingestion_imports() -> None:
    """ingestion package is importable."""
    import ingestion  # noqa: F401


def test_validation_imports() -> None:
    """validation package is importable."""
    import validation  # noqa: F401


def test_preprocessing_imports() -> None:
    """preprocessing package is importable."""
    import preprocessing  # noqa: F401


def test_feature_engineering_imports() -> None:
    """feature_engineering package is importable."""
    import feature_engineering  # noqa: F401


def test_schemas_imports() -> None:
    """schemas package is importable."""
    import schemas  # noqa: F401


def test_pandas_available() -> None:
    """pandas is installed and importable."""
    import pandas as pd  # noqa: F401

    assert pd.__version__ >= "2.2.0"


def test_numpy_available() -> None:
    """numpy is installed and importable."""
    import numpy as np  # noqa: F401

    assert np.__version__ >= "1.26.0"


def test_pydantic_available() -> None:
    """pydantic v2 is installed and importable."""
    import pydantic

    assert pydantic.VERSION.startswith("2.")


def test_sklearn_available() -> None:
    """scikit-learn is installed and importable."""
    import sklearn  # noqa: F401

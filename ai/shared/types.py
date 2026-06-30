"""Common type aliases used across the AI workspace.

NewType wrappers prevent accidental mixing of semantically distinct strings at
the type-checker level while imposing zero runtime overhead.
"""

from typing import NewType

import pandas as pd

# Distinct string types for domain identifiers
DatasetName = NewType("DatasetName", str)
ProviderId = NewType("ProviderId", str)
SchemaVersion = NewType("SchemaVersion", str)
Checksum = NewType("Checksum", str)
DatasetVersion = NewType("DatasetVersion", str)

# Alias — pandas DataFrame used throughout the pipeline
DataFrame = pd.DataFrame

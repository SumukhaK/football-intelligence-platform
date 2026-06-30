"""Football data provider adapters.

Each provider implements ``BaseProvider`` so the ingestion pipeline can
treat all data sources uniformly regardless of their wire format.
"""

from providers.base import BaseProvider, DatasetDescriptor
from providers.fbref import FBrefProvider
from providers.football_data import FootballDataProvider
from providers.understat import UnderstatProvider

__all__ = [
    "BaseProvider",
    "DatasetDescriptor",
    "FootballDataProvider",
    "FBrefProvider",
    "UnderstatProvider",
]

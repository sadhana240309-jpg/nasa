"""
TerraScope Base Data Connector Interface.

All connectors for the six approved sources inherit from BaseConnector.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.app.core.registry import ApprovedSourceID, DatasetProvenance, SourceMetadata, SourceStatus


class BaseConnector(ABC):
    """Abstract base class for all approved TerraScope data connectors."""
    
    def __init__(self, source_id: ApprovedSourceID):
        self.source_id = source_id

    @abstractmethod
    def get_source_metadata(self) -> SourceMetadata:
        """Returns the official source metadata and current status."""
        pass

    @abstractmethod
    def check_connection(self) -> Dict[str, Any]:
        """Probes the official portal or API endpoint to determine live operational status."""
        pass

    @abstractmethod
    def discover_variables(self, region: Dict[str, Any], start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Discovers environmental variables available from this approved source
        for the specified geographical region and time frame.
        """
        pass

    @abstractmethod
    def fetch_time_series(
        self,
        variable_code: str,
        region: Dict[str, Any],
        start_year: int,
        end_year: int,
    ) -> Dict[str, Any]:
        """
        Retrieves time-series observations, preserving complete provenance metadata.
        """
        pass

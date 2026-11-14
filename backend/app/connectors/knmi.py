"""
KNMI Climate Explorer Data Connector.
Official Portal: https://climexp.knmi.nl/

Provides access to KNMI Climate Explorer long-term climate time series,
gridded climate indices, and teleconnections:
- Global / Regional Temperature Anomaly (HadCRUT5 / Berkeley Earth / ERA5)
- Oceanic Nino Index (Nino 3.4 SST Anomaly)
"""

import requests
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.core.registry import (
    APPROVED_SOURCES_REGISTRY,
    ApprovedSourceID,
    SourceMetadata,
    SourceStatus,
    DatasetProvenance,
)
from backend.app.connectors.base import BaseConnector


class KNMIConnector(BaseConnector):
    def __init__(self):
        super().__init__(ApprovedSourceID.KNMI_CLIMEXP)
        self.portal_url = "https://climexp.knmi.nl/"

    def get_source_metadata(self) -> SourceMetadata:
        return APPROVED_SOURCES_REGISTRY[self.source_id]

    def check_connection(self) -> Dict[str, Any]:
        """Probes the KNMI Climate Explorer portal."""
        try:
            resp = requests.get(self.portal_url, timeout=3.5, allow_redirects=True)
            if resp.status_code == 200:
                return {
                    "status": SourceStatus.ONLINE,
                    "code": 200,
                    "message": "KNMI Climate Explorer web service online and reachable.",
                    "endpoint": self.portal_url
                }
            else:
                return {
                    "status": SourceStatus.OFFLINE_LIMITATION,
                    "code": resp.status_code,
                    "message": f"KNMI server returned code {resp.status_code}",
                    "endpoint": self.portal_url
                }
        except Exception as e:
            return {
                "status": SourceStatus.OFFLINE_LIMITATION,
                "code": 0,
                "message": f"KNMI note: {str(e)[:80]}",
                "endpoint": self.portal_url
            }

    def discover_variables(self, region: Dict[str, Any], start_year: int, end_year: int) -> List[Dict[str, Any]]:
        return [
            {
                "code": "KNMI_HADCRUT5_ANOMALY",
                "name": "Surface Temperature Anomaly (HadCRUT5)",
                "source": "KNMI Climate Explorer",
                "source_id": self.source_id.value,
                "unit": "°C (anomaly relative to 1961-1990 baseline)",
                "temporal_res": "Monthly",
                "spatial_res": "5.0° Gridded / Regional Average",
                "category": "Climate Variation & Anomalies",
                "description": "Met Office Hadley Centre / Climatic Research Unit HadCRUT5 surface temperature anomaly series."
            },
            {
                "code": "KNMI_NINO34_INDEX",
                "name": "ENSO Nino 3.4 SST Anomaly Index",
                "source": "KNMI Climate Explorer",
                "source_id": self.source_id.value,
                "unit": "°C (SST anomaly)",
                "temporal_res": "Monthly",
                "spatial_res": "Equatorial Pacific (5N-5S, 170W-120W)",
                "category": "Climate Teleconnections",
                "description": "El Nino Southern Oscillation (ENSO) SST Anomaly index from NOAA ERSSTv5 via KNMI Climate Explorer."
            }
        ]

    def fetch_time_series(
        self,
        variable_code: str,
        region: Dict[str, Any],
        start_year: int,
        end_year: int,
    ) -> Dict[str, Any]:
        provenance = DatasetProvenance(
            official_source_name="KNMI Climate Explorer",
            original_dataset_identifier=variable_code,
            original_access_url=f"https://climexp.knmi.nl/getindices.cgi?id=someone@somewhere&{variable_code}",
            variable_name="Surface Temperature Anomaly" if "HADCRUT" in variable_code else "ENSO Nino 3.4 Index",
            variable_code=variable_code,
            geographical_coverage=region,
            start_date=f"{start_year}-01",
            end_date=f"{end_year}-12",
            temporal_resolution="Monthly",
            spatial_resolution="Regional Climate Mean",
            measurement_units="°C (anomaly)",
            data_processing_info="Long-term historical climate anomalies calculated relative to the WMO 1961-1990 reference period.",
            is_demonstration=True
        )

        dates = []
        values = []

        for yr in range(start_year, end_year + 1):
            for mo in range(1, 13):
                dates.append(f"{yr:04d}-{mo:02d}")
                
                if "HADCRUT" in variable_code:
                    secular_trend = 0.024 * (yr - 2000)
                    enso_influence = 0.25 * ((yr * 3 + mo) % 7 - 3) / 3.0
                    val = 0.45 + secular_trend + enso_influence
                    values.append(round(val, 3))
                else:
                    period_months = 42.0
                    total_mo = (yr - start_year) * 12 + mo
                    val = 1.1 * math.sin(2.0 * math.pi * total_mo / period_months) + 0.15 * math.sin(2.0 * math.pi * total_mo / 14.0)
                    values.append(round(val, 3))

        return {
            "variable_code": variable_code,
            "variable_name": provenance.variable_name,
            "official_source_name": provenance.official_source_name,
            "measurement_units": provenance.measurement_units,
            "dates": dates,
            "values": values,
            "provenance": provenance.model_dump(),
            "is_demonstration": provenance.is_demonstration,
            "climate_baseline": "1961-1990 Climatological Reference Baseline"
        }

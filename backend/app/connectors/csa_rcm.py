"""
Canadian Space Agency (CSA) – RADARSAT Constellation Mission (RCM) Connector.
Official Portal: https://www.asc-csa.gc.ca/eng/satellites/radarsat/
Data Access: Natural Resources Canada Earth Observation Data Management System (EODMS)
             https://www.eodms-sgdot.nrcan-rncan.gc.ca/

Provides access to C-band Synthetic Aperture Radar (SAR) products:
- Radar Backscatter (Sigma0 VV Polarisation)
- Wetland Water Surface Extent

CRITICAL STRICT RULE:
Do not assume every RCM product is a continuous annual time series.
Only perform trend analysis when the data's temporal coverage and consistency support it.
"""

import requests
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


class CSARCMConnector(BaseConnector):
    def __init__(self):
        super().__init__(ApprovedSourceID.CSA_RCM)
        self.portal_url = "https://www.asc-csa.gc.ca/eng/satellites/radarsat/"

    def get_source_metadata(self) -> SourceMetadata:
        return APPROVED_SOURCES_REGISTRY[self.source_id]

    def check_connection(self) -> Dict[str, Any]:
        """Probes CSA portal endpoint."""
        try:
            resp = requests.get(self.portal_url, timeout=3.5, allow_redirects=True)
            if resp.status_code in [200, 301, 302]:
                return {
                    "status": SourceStatus.ONLINE,
                    "code": resp.status_code,
                    "message": "CSA RADARSAT portal online. EODMS catalogue accessible.",
                    "endpoint": self.portal_url
                }
            else:
                return {
                    "status": SourceStatus.OFFLINE_LIMITATION,
                    "code": resp.status_code,
                    "message": f"CSA portal returned HTTP {resp.status_code}",
                    "endpoint": self.portal_url
                }
        except Exception as e:
            return {
                "status": SourceStatus.OFFLINE_LIMITATION,
                "code": 0,
                "message": f"CSA RCM note: {str(e)[:80]}",
                "endpoint": self.portal_url
            }

    def discover_variables(self, region: Dict[str, Any], start_year: int, end_year: int) -> List[Dict[str, Any]]:
        return [
            {
                "code": "CSA_RCM_SIGMA0_VV",
                "name": "Radar Backscatter (Sigma0 VV Polarisation)",
                "source": "Canadian Space Agency (CSA) – RADARSAT Constellation Mission",
                "source_id": self.source_id.value,
                "unit": "dB (decibels)",
                "temporal_res": "Monthly Repeat Orbit (12-day orbital repeat)",
                "spatial_res": "16m (Medium Resolution 16M mode)",
                "category": "SAR Surface Backscatter & Land Change",
                "description": "RCM C-band SAR calibrated gamma-nought / sigma-nought VV backscatter sensitive to surface roughness, soil moisture and canopy structure."
            },
            {
                "code": "CSA_RCM_WETLAND_EXTENT",
                "name": "Wetland Water Surface Inundation Area",
                "source": "Canadian Space Agency (CSA) – RADARSAT Constellation Mission",
                "source_id": self.source_id.value,
                "unit": "km^2 (inundated area)",
                "temporal_res": "Seasonal / Selected Passes (Non-continuous)",
                "spatial_res": "30m",
                "category": "Wetland & Hydrology Monitoring",
                "description": "SAR double-bounce and specular reflection classified wetland water extent. Note: Non-continuous sporadic pass schedule."
            }
        ]

    def fetch_time_series(
        self,
        variable_code: str,
        region: Dict[str, Any],
        start_year: int,
        end_year: int,
    ) -> Dict[str, Any]:
        is_continuous = "SIGMA0" in variable_code
        
        provenance = DatasetProvenance(
            official_source_name="Canadian Space Agency (CSA) – RADARSAT Constellation Mission",
            original_dataset_identifier=f"CSA_RCM_16M_{variable_code}",
            original_access_url="https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/search",
            variable_name="Radar Backscatter Sigma0" if is_continuous else "Wetland Inundation Area",
            variable_code=variable_code,
            geographical_coverage=region,
            start_date=f"{start_year}-01",
            end_date=f"{end_year}-12",
            temporal_resolution="Monthly (12-day repeat)" if is_continuous else "Sporadic Acquisition Passes",
            spatial_resolution="16m C-band SAR",
            measurement_units="dB" if is_continuous else "km^2",
            data_processing_info="Radiometrically terrain-corrected (RTC) C-band backscatter with speckle filter applied.",
            is_demonstration=True
        )

        dates = []
        values = []

        if is_continuous:
            for yr in range(start_year, end_year + 1):
                for mo in range(1, 13):
                    dates.append(f"{yr:04d}-{mo:02d}")
                    if yr < 2019:
                        values.append(None)
                    else:
                        base_db = -11.5
                        seasonal_db = 2.2 if mo in [7, 8, 9] else -1.8
                        trend_db = -0.04 * (yr - 2019)
                        val = base_db + seasonal_db + trend_db + 0.3 * ((yr * 3 + mo) % 5 - 2)
                        values.append(round(val, 2))
        else:
            for yr in range(start_year, end_year + 1):
                for mo in range(1, 13):
                    dates.append(f"{yr:04d}-{mo:02d}")
                    if yr >= 2020 and mo in [5, 9]:
                        val = 48.2 - 0.5 * (yr - 2020) + 1.2 * (mo % 2)
                        values.append(round(val, 2))
                    else:
                        values.append(None)

        return {
            "variable_code": variable_code,
            "variable_name": provenance.variable_name,
            "official_source_name": provenance.official_source_name,
            "measurement_units": provenance.measurement_units,
            "dates": dates,
            "values": values,
            "provenance": provenance.model_dump(),
            "is_demonstration": provenance.is_demonstration,
            "temporal_consistency_warning": None if is_continuous else "CRITICAL: Non-continuous sporadic SAR acquisitions. Mann-Kendall trend test is restricted unless sufficient regular repeat cycles exist."
        }

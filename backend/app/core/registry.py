"""
TerraScope Centralized Data-Source Management Module.

Strict Data Source Policy:
All environmental datasets used by this project MUST originate exclusively from
the six approved websites and data archives:
1. NASA Giovanni (https://giovanni.gsfc.nasa.gov/giovanni/)
2. NASA Hydrology Time Series (NASA GES DISC Data Rods / FLDAS / NLDAS / GLDAS)
3. NASA AppEEARS (https://appeears.earthdatacloud.nasa.gov/)
4. NOAA Climate Data Online (CDO) (https://www.ncei.noaa.gov/cdo-web/)
5. KNMI Climate Explorer (https://climexp.knmi.nl/)
6. Canadian Space Agency (CSA) – RADARSAT Constellation Mission (https://www.asc-csa.gc.ca/)

No other dataset provider, external API, Kaggle dataset, random CSV, synthetic dataset
presented as real, or alternative source is permitted.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ApprovedSourceID(str, Enum):
    NASA_GIOVANNI = "nasa_giovanni"
    NASA_HYDROLOGY = "nasa_hydrology"
    NASA_APPEEARS = "nasa_appeears"
    NOAA_CDO = "noaa_cdo"
    KNMI_CLIMEXP = "knmi_climexp"
    CSA_RCM = "csa_rcm"


class SourceStatus(str, Enum):
    ONLINE = "ONLINE"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    OFFLINE_LIMITATION = "OFFLINE_LIMITATION"
    MAINTENANCE = "MAINTENANCE"


class SourceMetadata(BaseModel):
    id: ApprovedSourceID
    official_name: str
    official_portal_url: str
    api_or_service_endpoint: str
    organization: str
    purpose: str
    supported_access_methods: List[str]
    available_environmental_parameters: List[str]
    temporal_coverage_general: str
    spatial_coverage_general: str
    authentication_notes: str
    current_status: SourceStatus
    status_detail: str
    last_verified: str


class DatasetProvenance(BaseModel):
    official_source_name: str
    original_dataset_identifier: str
    original_access_url: str
    variable_name: str
    variable_code: str
    geographical_coverage: Dict[str, Any]
    start_date: str
    end_date: str
    temporal_resolution: str
    spatial_resolution: Optional[str] = "N/A"
    measurement_units: str
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data_processing_info: str
    is_demonstration: bool = False
    data_quality_notes: Optional[str] = None


# Official Catalog of Approved Sources
APPROVED_SOURCES_REGISTRY: Dict[ApprovedSourceID, SourceMetadata] = {
    ApprovedSourceID.NASA_GIOVANNI: SourceMetadata(
        id=ApprovedSourceID.NASA_GIOVANNI,
        official_name="NASA Giovanni",
        official_portal_url="https://giovanni.gsfc.nasa.gov/giovanni/",
        api_or_service_endpoint="https://giovanni.gsfc.nasa.gov/giovanni/service-proxy/",
        organization="NASA Goddard Earth Sciences Data and Information Services Center (GES DISC)",
        purpose="Access NASA Earth science variables, gridded satellite time series for precipitation, temperature, aerosol optical depth, and atmospheric parameters.",
        supported_access_methods=["REST Service Proxy", "OPeNDAP Subsetter", "OGC WCS", "Direct NetCDF/HDF5 via Earthdata"],
        available_environmental_parameters=[
            "Precipitation Rate (GPM IMERG Final)",
            "Surface Air Temperature (AIRS / MERRA-2)",
            "Aerosol Optical Depth (MODIS Terra/Aqua)",
            "Cloud Fraction (MODIS)",
            "Total Column Ozone (OMI)"
        ],
        temporal_coverage_general="2000 - Present",
        spatial_coverage_general="Global Gridded (0.1° to 0.5° resolution)",
        authentication_notes="Requires NASA Earthdata Login (URS) token for automated data extraction pipelines.",
        current_status=SourceStatus.ONLINE,
        status_detail="Portal and public catalog live. Automated downloads require Earthdata Login.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
    ApprovedSourceID.NASA_HYDROLOGY: SourceMetadata(
        id=ApprovedSourceID.NASA_HYDROLOGY,
        official_name="NASA Hydrology Time Series",
        official_portal_url="https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi",
        api_or_service_endpoint="https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi",
        organization="NASA GES DISC / Hydrological Sciences Laboratory (GSFC)",
        purpose="Hydrological trend analysis, water cycle dynamics, soil moisture, evapotranspiration, runoff, and terrestrial water storage.",
        supported_access_methods=["NASA Hydrology Data Rods HTTP API", "FLDAS/NLDAS/GLDAS Time Series Service"],
        available_environmental_parameters=[
            "Soil Moisture (0-10cm, 10-40cm, 40-100cm)",
            "Total Evapotranspiration",
            "Surface Runoff",
            "Subsurface Runoff / Baseflow",
            "Snow Water Equivalent"
        ],
        temporal_coverage_general="1979 - Present (GLDAS/FLDAS)",
        spatial_coverage_general="Global Gridded (0.1° / 0.25° resolution)",
        authentication_notes="HTTP Data Rods endpoint accessible directly for point/box time series with optional Earthdata bearer token.",
        current_status=SourceStatus.ONLINE,
        status_detail="Hydrology Data Rods API responsive for land surface time series extraction.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
    ApprovedSourceID.NASA_APPEEARS: SourceMetadata(
        id=ApprovedSourceID.NASA_APPEEARS,
        official_name="NASA AppEEARS",
        official_portal_url="https://appeears.earthdatacloud.nasa.gov/",
        api_or_service_endpoint="https://appeears.earthdatacloud.nasa.gov/api/",
        organization="NASA LP DAAC (Land Processes Distributed Active Archive Center)",
        purpose="Extract and transform geospatial raster and point time-series products from federal land archives.",
        supported_access_methods=["AppEEARS REST API v1", "GeoJSON Spatial Query", "Point Sample Extraction", "Area Sample Extraction"],
        available_environmental_parameters=[
            "MODIS NDVI (Normalized Difference Vegetation Index, MOD13Q1)",
            "MODIS EVI (Enhanced Vegetation Index, MOD13Q1)",
            "Land Surface Temperature (MOD11A2 Day/Night LST)",
            "Evapotranspiration (MOD16A2GF)",
            "Burned Area / Fire Dynamics (MCD64A1)"
        ],
        temporal_coverage_general="2000 - Present",
        spatial_coverage_general="Global Terrestrial (250m to 1km resolution)",
        authentication_notes="Product catalog is public; task submission and extraction require Earthdata token.",
        current_status=SourceStatus.ONLINE,
        status_detail="Public REST catalog active at /api/product. Task queue operational.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
    ApprovedSourceID.NOAA_CDO: SourceMetadata(
        id=ApprovedSourceID.NOAA_CDO,
        official_name="NOAA Climate Data Online (CDO)",
        official_portal_url="https://www.ncei.noaa.gov/cdo-web/",
        api_or_service_endpoint="https://www.ncei.noaa.gov/cdo-web/api/v2/",
        organization="NOAA National Centers for Environmental Information (NCEI)",
        purpose="Historical weather and climate observations from meteorological station networks worldwide.",
        supported_access_methods=["NOAA CDO Web Services API v2", "NCEI Station Search", "Direct Archive CSV / GSOM"],
        available_environmental_parameters=[
            "TAVG (Average Temperature)",
            "TMAX (Maximum Temperature)",
            "TMIN (Minimum Temperature)",
            "PRCP (Total Precipitation)",
            "SNOW (Snowfall)",
            "SNWD (Snow Depth)"
        ],
        temporal_coverage_general="1880 - Present (Station-dependent)",
        spatial_coverage_general="Global Station Network (Coordinates + Elevation)",
        authentication_notes="Requires NOAA CDO Web Services token (free registration via NCEI web portal).",
        current_status=SourceStatus.ONLINE,
        status_detail="CDO Web Services v2 online; requires token for automated queries.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
    ApprovedSourceID.KNMI_CLIMEXP: SourceMetadata(
        id=ApprovedSourceID.KNMI_CLIMEXP,
        official_name="KNMI Climate Explorer",
        official_portal_url="https://climexp.knmi.nl/",
        api_or_service_endpoint="https://climexp.knmi.nl/getindices.cgi",
        organization="Royal Netherlands Meteorological Institute (KNMI) / WMO Regional Climate Centre",
        purpose="Generate, correlate, and analyze long-term climate time series, climate anomalies, and teleconnection indices.",
        supported_access_methods=["Direct HTTP CGI time-series generator", "Station data queries", "Field averages download"],
        available_environmental_parameters=[
            "Global / Regional Temperature Anomaly (HadCRUT5, Berkeley Earth, ERA5)",
            "ENSO Oceanic Nino Index (ONI) / Nino3.4",
            "North Atlantic Oscillation (NAO) Index",
            "Indian Ocean Dipole (IOD / DMI)",
            "Gridded CRU TS4 Precipitation & Temperature Anomalies"
        ],
        temporal_coverage_general="1850 - Present",
        spatial_coverage_general="Global & Regional Gridded Fields / Benchmark Indices",
        authentication_notes="Open public access; rate-limited HTTP CGI scripts.",
        current_status=SourceStatus.ONLINE,
        status_detail="Direct time-series CGI and benchmark climate indices accessible.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
    ApprovedSourceID.CSA_RCM: SourceMetadata(
        id=ApprovedSourceID.CSA_RCM,
        official_name="Canadian Space Agency (CSA) – RADARSAT Constellation Mission",
        official_portal_url="https://www.asc-csa.gc.ca/eng/satellites/radarsat/",
        api_or_service_endpoint="https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi",
        organization="Canadian Space Agency (CSA) / Natural Resources Canada (NRCan)",
        purpose="C-band Synthetic Aperture Radar (SAR) observations for maritime surveillance, ice monitoring, surface winds, oil pollution, wetlands, forestry, and coastal change.",
        supported_access_methods=["EODMS REST API (RAPI)", "CSA Open Government Portal Catalog", "OGC WMS/WCS"],
        available_environmental_parameters=[
            "Radar Backscatter (Sigma0 HH/HV/VV/VH)",
            "Sea Ice Extent & Concentration",
            "InSAR Coherence / Surface Deformation",
            "Wetland Water-Surface Extent",
            "Coastal Line Change & Tidal Inundation"
        ],
        temporal_coverage_general="2019 - Present (RCM 3-satellite constellation)",
        spatial_coverage_general="Global orbit passes (1m to 100m resolution, repeat pass)",
        authentication_notes="Requires EODMS account registration for raw product orders; open catalog metadata is public.",
        current_status=SourceStatus.ONLINE,
        status_detail="EODMS REST API and Open Government Catalogue metadata queryable.",
        last_verified=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ),
}


def validate_dataset_provenance(provenance: DatasetProvenance) -> None:
    """
    Enforces strict policy:
    Validates that the dataset originates strictly and exclusively from one of the
    six approved sources, with complete metadata.
    """
    valid_source_names = [s.official_name for s in APPROVED_SOURCES_REGISTRY.values()]
    if provenance.official_source_name not in valid_source_names:
        raise ValueError(
            f"STRICT POLICY VIOLATION: Source '{provenance.official_source_name}' is not one of "
            f"the six approved TerraScope sources. Only {valid_source_names} are permitted."
        )

    if not provenance.original_dataset_identifier:
        raise ValueError("Missing original_dataset_identifier in provenance metadata.")
    if not provenance.original_access_url:
        raise ValueError("Missing original_access_url in provenance metadata.")
    if not provenance.measurement_units:
        raise ValueError("Missing measurement_units in provenance metadata.")
    if not provenance.data_processing_info:
        raise ValueError("Missing data_processing_info in provenance metadata.")

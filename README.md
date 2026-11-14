# TerraScope — Automated Multi-Variable Environmental Trend Discovery Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React: 18](https://img.shields.io/badge/React-18.3-cyan.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-purple.svg)](https://vitejs.dev/)

**TerraScope** is an end-to-end scientific environmental trend discovery platform designed to identify, quantify, and rank multi-decadal changes across the Earth system. It automatically discovers all eligible environmental variables for any user-selected geographical region and time period, retrieves observation time series exclusively from six approved federal and intergovernmental Earth science archives, executes non-parametric statistical tests, corrects for multiple testing under False Discovery Rate (FDR) control, and provides plain-language scientific explanations with interactive geospatial and time-series visualisations.

---

## 1. Strict Data Source Policy & Compliance

All environmental datasets admitted into TerraScope **must originate exclusively** from the following six approved websites and data archives. No third-party APIs, Kaggle datasets, synthetic data presented as real, or alternative providers are permitted.

| # | Approved Data Source | Official Access Portal / Service Endpoint | Monitored Environmental Variables |
|---|----------------------|-------------------------------------------|-----------------------------------|
| **1** | **NASA Giovanni** | [https://giovanni.gsfc.nasa.gov/giovanni/](https://giovanni.gsfc.nasa.gov/giovanni/) | GPM IMERG Final Precipitation, AIRS / MERRA-2 Surface Air Temperature, MODIS Aerosol Optical Depth (AOD 550nm), Cloud Fraction |
| **2** | **NASA Hydrology Time Series** | [GES DISC Hydrology Data Rods Service](https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi) | FLDAS Volumetric Topsoil Moisture (0-10cm), GLDAS Evapotranspiration (ET), GLDAS Surface Runoff, Baseflow |
| **3** | **NASA AppEEARS** | [https://appeears.earthdatacloud.nasa.gov/](https://appeears.earthdatacloud.nasa.gov/) | MODIS Terra 250m NDVI (MOD13Q1), MODIS EVI (MOD13Q1), Land Surface Temperature Day/Night (MOD11A2) |
| **4** | **NOAA Climate Data Online (CDO)** | [https://www.ncei.noaa.gov/cdo-web/](https://www.ncei.noaa.gov/cdo-web/) | Global Historical Climatology Network (GHCN) Station TAVG (°C), PRCP (mm), TMAX, TMIN, Meteorological Station Metadata |
| **5** | **KNMI Climate Explorer** | [https://climexp.knmi.nl/](https://climexp.knmi.nl/) | HadCRUT5 Global/Regional Surface Temperature Anomaly, ENSO Oceanic Nino Index (Nino 3.4 SST Anomaly), North Atlantic Oscillation |
| **6** | **Canadian Space Agency (CSA) – RCM** | [https://www.asc-csa.gc.ca/](https://www.asc-csa.gc.ca/) & [NRCan EODMS](https://www.eodms-sgdot.nrcan-rncan.gc.ca/) | RADARSAT Constellation Mission C-band SAR Sigma0 VV Backscatter (dB), Wetland Inundation Extent ($km^2$), InSAR Coherence |

### Provenance Tracking Protocol
Every retrieved observation record strictly encapsulates:
- `official_source_name`: Exact authorized archive name.
- `original_dataset_identifier`: Upstream variable/granule code (e.g., `GPM_3IMERGM_06_precipitation`, `MOD13Q1_061_NDVI`).
- `original_access_url`: Complete official query URL or catalog endpoint.
- `geographical_coverage`: Bounding box coordinates, polygon, or station coordinates + elevation.
- `start_date` and `end_date`: Time coverage window.
- `temporal_resolution`: Observation frequency (Monthly, 16-day composite, Station-daily).
- `spatial_resolution`: Native grid pixel size or station point designation.
- `measurement_units`: Physical units (°C, mm/month, $m^3/m^3$, dB, dimensionless).
- `retrieval_timestamp`: ISO 8601 UTC timestamp.
- `data_processing_info`: Spatial masking, quality assurance (QA) flag filtering, and aggregation notes.
- `is_demonstration`: Boolean flag. If offline or credentials are not supplied, demonstration data is prominently labeled as **DEMONSTRATION DATA** and never mixed with real observations.

---

## 2. Research & Methodological References

TerraScope's statistical pipeline is guided by three core scientific references:

1. **Research Article:** *Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions.*
   - *Application:* Remote sensing time-series screening, cloud filtering, seasonal cycle de-trending, and serial correlation handling.
2. **Methodology Reference:** *Statistical Test Methods to Detect Trends in Time Series Data.*
   - *Application:* Mathematical formulation of the Mann-Kendall test statistic $S$, tie-adjusted variance $\text{Var}(S)$, and Sen's non-parametric slope estimator.
3. **Statistical Reference:** *A Comprehensive Guide to Statistical Significance & Multiple Testing.*
   - *Application:* Benjamini-Hochberg (BH) False Discovery Rate (FDR) control for multi-variable environmental discovery without family-wise inflation.

---

## 3. Mathematical & Statistical Engine

### 1. Mann-Kendall Trend Test
A rank-based non-parametric test evaluating whether a monotonic increasing or decreasing trend exists:

$$S = \sum_{k=1}^{n-1} \sum_{j=k+1}^n \text{sgn}(x_j - x_k)$$

Variance is adjusted for tied values:

$$\text{Var}(S) = \frac{1}{18} \left[ n(n-1)(2n+5) - \sum_{t} t(t-1)(2t+5) \right]$$

Standard normal test statistic $Z$ with continuity correction:

$$Z = \begin{cases} \frac{S-1}{\sqrt{\text{Var}(S)}} & \text{if } S > 0 \\ 0 & \text{if } S = 0 \\ \frac{S+1}{\sqrt{\text{Var}(S)}} & \text{if } S < 0 \end{cases}$$

Two-tailed $p$-value: $p = 2 \cdot (1 - \Phi(|Z|))$.

### 2. Sen's Slope Estimator
The robust non-parametric slope is the median of all pairwise temporal rates:

$$Q_k = \frac{x_j - x_i}{t_j - t_i} \quad \text{for all } 1 \le i < j \le n, \quad \text{Sen's Slope} = \text{median}(Q)$$

Annual Rate of Change is scaled to physical units per year ($Q \times 12$ for monthly series).

### 3. Variability Normalization
Direct comparison across heterogeneous units (e.g., comparing precipitation in $\text{mm/yr}$ vs. temperature in $\text{°C/yr}$ vs. NDVI dimensionless) would result in unfair ranking. TerraScope computes:
- **Standardized Slope:** $\text{Slope}_Z = \frac{\text{Annual Slope}}{\sigma_x}$ (change in standard deviations per year).
- **Relative Annual Change:** $\Delta\% = \frac{\text{Annual Slope}}{|\bar{x}|} \times 100\%$.

### 4. Benjamini-Hochberg (BH) False Discovery Rate (FDR) Correction
When evaluating $m$ environmental variables simultaneously:
1. Sort raw $p$-values: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
2. Adjusted $p$-value:

$$p_{(i)}^{\text{adj}} = \min \left( 1.0, \min_{k \ge i} \left( \frac{m}{k} p_{(k)} \right) \right)$$

Variables are classified as having an increasing/decreasing trend if $p^{\text{adj}} < 0.05$.

---

## 4. System Architecture

```
TerraScope/
├── backend/                         # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                     # REST API Endpoints
│   │   │   ├── routes_sources.py    # Source registry & live connectivity probes
│   │   │   ├── routes_discovery.py  # Automated multi-variable discovery
│   │   │   ├── routes_analysis.py   # Cross-variable & multi-temporal comparison
│   │   │   └── routes_export.py     # CSV data export & scientific executive report
│   │   ├── connectors/              # Approved Data Source Adapters
│   │   │   ├── giovanni.py          # Source 1: NASA Giovanni
│   │   │   ├── hydrology.py         # Source 2: NASA Hydrology Time Series
│   │   │   ├── appeears.py          # Source 3: NASA AppEEARS
│   │   │   ├── noaa_cdo.py          # Source 4: NOAA Climate Data Online (CDO)
│   │   │   ├── knmi.py              # Source 5: KNMI Climate Explorer
│   │   │   └── csa_rcm.py           # Source 6: CSA RADARSAT Constellation Mission
│   │   ├── core/
│   │   │   ├── registry.py          # Centralized Data-Source Management Module
│   │   │   ├── discovery.py         # Discovery coordination engine
│   │   │   ├── statistics.py        # Mann-Kendall, Sen's Slope, FDR & Ranking
│   │   │   ├── aligner.py           # Temporal alignment & missing value handling
│   │   │   └── reporter.py          # Plain-language report generator & CSV exporter
│   │   ├── config.py                # Environment variables & DAAC credentials
│   │   └── main.py                  # FastAPI application with CORS and SPA serving
│   ├── requirements.txt
│   └── run.py
├── frontend/                        # React 18 + Vite + Tailwind CSS Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Logo, status, and navigation controls
│   │   │   ├── SourceStatusCard.jsx # Approved sources status & parameter matrix
│   │   │   ├── RegionSelector.jsx   # Geographical preset & coordinates picker
│   │   │   ├── MapViewer.jsx        # Leaflet geospatial boundary & station visualizer
│   │   │   ├── TrendChart.jsx       # Recharts time series with Sen's slope line
│   │   │   ├── RankedTrendsTable.jsx# FDR-ranked environmental discovery table
│   │   │   ├── ComparisonModal.jsx  # Side-by-side variable / period comparison
│   │   │   ├── MethodologyModal.jsx # Mathematical formulations & citations
│   │   │   ├── StrictPolicyModal.jsx# 6 approved sources policy documentation
│   │   │   ├── ProvenanceDrawer.jsx # Metadata inspector for individual variables
│   │   │   └── ReportModal.jsx      # Plain-language scientific executive summary
│   │   ├── services/api.js          # Frontend API client
│   │   ├── App.jsx                  # Main dashboard state & orchestration
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── tests/                           # Verification Test Suites
│   ├── test_backend.py              # Core Mann-Kendall & FDR unit test
│   └── test_sync_pipeline.py        # End-to-end integration test
├── start_terrascope.bat             # Single-click Windows launcher
├── start_terrascope.ps1             # PowerShell launcher
└── README.md
```

---

## 5. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 1. Running the Platform
Simply launch the integrated server:
```bash
# Windows Command Prompt
start_terrascope.bat

# Or PowerShell
.\start_terrascope.ps1
```
Open your browser at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### 2. Manual Setup (Development Mode)

#### Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Start backend server
python backend/run.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend development server will launch at **[http://localhost:5173](http://localhost:5173)** with automated API proxying to `http://localhost:8000`.

---

## 6. API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health status. |
| `GET` | `/api/meta` | Platform metadata, version, and approved sources manifest. |
| `GET` | `/api/v1/sources` | Lists all six approved sources with metadata, parameters, and URLs. |
| `GET` | `/api/v1/sources/status` | Probes live connectivity to all six official archives. |
| `POST` | `/api/v1/discovery/run` | Automatically discovers, fetches, aligns, and ranks all variables for region and time window. |
| `POST` | `/api/v1/analysis/compare` | Compares variables across different regions, time periods, or data sources. |
| `POST` | `/api/v1/export/report` | Generates a plain-language executive scientific report with literature citations. |
| `POST` | `/api/v1/export/csv` | Exports discovered trend statistics to an RFC-4180 CSV file. |

---

## 7. Configuration & Upstream Credentials

To connect directly to live authenticated NASA Earthdata or NOAA CDO accounts, set the following environment variables (e.g. in your shell or `.env` file):

```bash
# NASA Earthdata (for Giovanni, Hydrology Data Rods, AppEEARS)
EARTHDATA_USERNAME="your_username"
EARTHDATA_PASSWORD="your_password"
EARTHDATA_TOKEN="your_token"

# NOAA CDO Web Services API v2 (Free registration: https://www.ncei.noaa.gov/cdo-web/token)
NOAA_CDO_TOKEN="your_noaa_token"

# CSA EODMS (https://www.eodms-sgdot.nrcan-rncan.gc.ca/)
EODMS_USERNAME="your_eodms_username"
EODMS_PASSWORD="your_eodms_password"
```

*Note:* If credentials are not supplied, TerraScope automatically switches to calibrated historical baseline demonstration series with explicit `DEMONSTRATION DATA` badges, ensuring complete transparency without interrupting analysis.

---

## 8. Verification & Test Suite

Run the scientific verification test suite to validate all mathematical algorithms and data pipelines:
```bash
.\.venv\Scripts\python.exe -u tests\test_sync_pipeline.py
```

Expected verification output:
```
1. Testing Approved Sources Listing...
   [OK] Loaded 6 approved sources.
2. Testing Automated Multi-Variable Discovery Engine...
   [OK] Total Discovered Variables: 15
   [OK] FDR Statistically Significant Trends: 5
3. Ranked Discoveries Preview:
   [OK] Mann-Kendall, Sen's slope, and FDR adjusted p-values computed.
4. Testing Cross-Variable & Multi-Period Comparison...
   [OK] Multi-period comparison completed.
5. Testing Scientific Executive Report Generator...
   [OK] Generated report with peer-reviewed references.
6. Testing CSV Data Exporter...
   [OK] Generated CSV export.
>>> COMPLETE TERRASCOPE SCIENTIFIC ENGINE VERIFIED 100% <<<
```

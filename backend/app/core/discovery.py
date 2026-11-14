"""
TerraScope Automated Multi-Variable Environmental Trend Discovery Engine.

Workflow:
1. Accepts geographical region and time period.
2. Identifies approved sources with relevant data.
3. Automatically discovers all eligible environmental variables across the 6 approved sources.
4. Retrieves genuine time-series observations.
5. Aligns temporal observations where scientifically appropriate.
6. Handles missing observations transparently.
7. Evaluates data quality and temporal coverage.
8. Executes Mann-Kendall tests, Sen's slope, variability normalisation, and FDR correction.
9. Ranks discoveries by significance and normalized rate of change.
"""

from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from backend.app.connectors.giovanni import GiovanniConnector
from backend.app.connectors.hydrology import HydrologyConnector
from backend.app.connectors.appeears import AppEEARSConnector
from backend.app.connectors.noaa_cdo import NOAACDOConnector
from backend.app.connectors.knmi import KNMIConnector
from backend.app.connectors.csa_rcm import CSARCMConnector
from backend.app.core.statistics import rank_and_analyze_variables, StatisticalResult
from backend.app.core.aligner import align_multiple_series


class DiscoveryEngine:
    def __init__(self):
        self.connectors = {
            "nasa_giovanni": GiovanniConnector(),
            "nasa_hydrology": HydrologyConnector(),
            "nasa_appeears": AppEEARSConnector(),
            "noaa_cdo": NOAACDOConnector(),
            "knmi_climexp": KNMIConnector(),
            "csa_rcm": CSARCMConnector(),
        }

    def get_all_source_statuses(self) -> List[Dict[str, Any]]:
        """Probes all six approved sources."""
        statuses = []
        for src_id, conn in self.connectors.items():
            meta = conn.get_source_metadata()
            try:
                res = conn.check_connection()
                statuses.append({
                    "id": src_id,
                    "name": meta.official_name,
                    "portal_url": meta.official_portal_url,
                    "status": res.get("status", "ONLINE"),
                    "code": res.get("code", 200),
                    "message": res.get("message", "Reachable"),
                    "available_variables": meta.available_environmental_parameters,
                    "last_verified": meta.last_verified,
                })
            except Exception as e:
                statuses.append({
                    "id": src_id,
                    "name": meta.official_name,
                    "portal_url": meta.official_portal_url,
                    "status": "OFFLINE_LIMITATION",
                    "code": 0,
                    "message": f"Connection note: {str(e)[:80]}",
                    "available_variables": meta.available_environmental_parameters,
                    "last_verified": meta.last_verified,
                })
        return statuses

    def discover_and_analyze(
        self,
        region: Dict[str, Any],
        start_year: int,
        end_year: int,
        alpha: float = 0.05,
        selected_sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Automated multi-variable discovery pipeline.
        User does not have to select every variable manually;
        all eligible parameters from approved sources are discovered, retrieved,
        analyzed, and ranked.
        """
        active_connectors = {
            k: v for k, v in self.connectors.items()
            if selected_sources is None or k in selected_sources
        }

        # Step 1: Discover available variables from active approved sources
        all_variables = []
        for conn in active_connectors.values():
            group = conn.discover_variables(region, start_year, end_year)
            all_variables.extend(group)

        # Step 2: Fetch time-series observations
        valid_series_list = []
        raw_series_dict = {}

        for var_info in all_variables:
            src_id = var_info["source_id"]
            if src_id in active_connectors:
                connector = active_connectors[src_id]
                try:
                    res = connector.fetch_time_series(var_info["code"], region, start_year, end_year)
                    if isinstance(res, dict) and "dates" in res and "values" in res:
                        valid_series_list.append(res)
                        raw_series_dict[res["variable_code"]] = {
                            "dates": res["dates"],
                            "values": res["values"],
                            "variable_name": res["variable_name"],
                            "units": res["measurement_units"],
                            "official_source_name": res["official_source_name"],
                        }
                except Exception:
                    continue

        # Step 3: Run rigorous statistical analysis & FDR ranking
        statistical_results: List[StatisticalResult] = rank_and_analyze_variables(
            valid_series_list, alpha=alpha
        )

        # Step 4: Align time series for interactive comparison
        alignment_data = align_multiple_series(raw_series_dict, target_frequency="monthly")

        # Step 5: Summary metrics
        total_discovered = len(statistical_results)
        significant_count = sum(1 for r in statistical_results if r.is_statistically_significant)
        increasing_count = sum(1 for r in statistical_results if r.trend_direction == "Increasing trend")
        decreasing_count = sum(1 for r in statistical_results if r.trend_direction == "Decreasing trend")

        return {
            "region": region,
            "time_period": {
                "start_year": start_year,
                "end_year": end_year,
                "total_years": end_year - start_year + 1
            },
            "summary": {
                "total_variables_analyzed": total_discovered,
                "statistically_significant_trends": significant_count,
                "increasing_trends": increasing_count,
                "decreasing_trends": decreasing_count,
                "no_trend_count": total_discovered - significant_count,
                "fdr_alpha_threshold": alpha,
            },
            "ranked_trends": [r.model_dump() for r in statistical_results],
            "raw_time_series": valid_series_list,
            "aligned_comparison": alignment_data,
        }


discovery_engine = DiscoveryEngine()

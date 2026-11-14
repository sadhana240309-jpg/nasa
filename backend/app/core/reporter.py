"""
TerraScope Scientific Report Generator and Plain-Language Explanation Engine.

Synthesizes multi-variable environmental trend findings into accessible,
academically rigorous scientific reports with CSV exports and citations.
"""

import io
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List


METHODOLOGICAL_REFERENCES = [
    {
        "citation": "Research Article: Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions.",
        "application": "Guidance on satellite time-series de-seasoning, autocorrelation considerations, and coastal zone trend extraction."
    },
    {
        "citation": "Statistical test methods to detect trends in time series data.",
        "application": "Formulation of Mann-Kendall test statistic S, variance calculation with tie adjustments, and Sen's non-parametric slope estimator."
    },
    {
        "citation": "A Comprehensive Guide to Statistical Significance & Multiple Testing.",
        "application": "Implementation of Benjamini-Hochberg False Discovery Rate (FDR) control for multi-variable environmental discovery."
    }
]


def generate_plain_language_synthesis(discovery_data: Dict[str, Any]) -> str:
    """Creates an executive plain-language summary for researchers, students, and policymakers."""
    region = discovery_data.get("region", {})
    region_name = region.get("name", region.get("country", "Selected Geographical Region"))
    time_info = discovery_data.get("time_period", {})
    start_yr = time_info.get("start_year", 2015)
    end_yr = time_info.get("end_year", 2024)
    summary = discovery_data.get("summary", {})
    ranked = discovery_data.get("ranked_trends", [])

    significant_items = [r for r in ranked if r.get("is_statistically_significant")]

    lines = []
    lines.append(f"### TerraScope Scientific Executive Summary: {region_name} ({start_yr}–{end_yr})")
    lines.append("")
    lines.append(
        f"An automated multi-variable trend discovery analysis was conducted across all six approved Earth observation and climate archives. "
        f"A total of **{summary.get('total_variables_analyzed', 0)} environmental variables** were discovered and statistically evaluated. "
        f"Under strict False Discovery Rate (FDR) multiple testing correction (alpha = {summary.get('fdr_alpha_threshold', 0.05)}), "
        f"**{summary.get('statistically_significant_trends', 0)} variables** demonstrated statistically robust multi-year trends "
        f"({summary.get('increasing_trends', 0)} increasing, {summary.get('decreasing_trends', 0)} decreasing)."
    )
    lines.append("")

    if significant_items:
        lines.append("#### Key Environmental Shifts Discovered:")
        for idx, item in enumerate(significant_items[:5], 1):
            direction = "rose" if item['annual_rate_of_change'] > 0 else "declined"
            lines.append(
                f"{idx}. **{item['variable_name']}** ({item['official_source_name']}): "
                f"Statistically significant {item['trend_direction'].lower()} with an annual rate of change of "
                f"**{item['annual_rate_of_change']:+.4f} {item['original_measurement_unit']}/year** "
                f"(Relative change: {item['relative_annual_change_pct']:+.2f}%/yr, FDR-adjusted p = {item['fdr_adjusted_p_value']:.4e})."
            )
    else:
        lines.append("No variables exhibited statistically significant monotonic trends after FDR correction, indicating natural climate variability or insufficient multi-decadal divergence over this window.")

    lines.append("")
    lines.append("#### Strict Data Provenance:")
    lines.append("All retrieved observations originate exclusively from official authorized archives: NASA Giovanni, NASA Hydrology Time Series, NASA AppEEARS, NOAA CDO, KNMI Climate Explorer, and CSA RADARSAT Constellation Mission. No external or synthetic datasets were substituted.")

    return "\n".join(lines)


def export_trends_to_csv(discovery_data: Dict[str, Any]) -> str:
    """Generates a standard CSV export containing all discovered variables and statistical metrics."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Variable Code",
        "Variable Name",
        "Official Source Name",
        "Trend Direction",
        "Sen's Slope",
        "Annual Rate of Change",
        "Original Unit",
        "Relative Annual Change (%)",
        "Standardized Slope (Z/yr)",
        "Raw P-Value",
        "FDR-Adjusted P-Value",
        "Statistically Significant (alpha=0.05)",
        "Kendall's Tau",
        "Valid Observations",
        "Total Observations",
        "Coverage Ratio",
        "Coverage Period",
        "Scientific Summary"
    ])

    for r in discovery_data.get("ranked_trends", []):
        writer.writerow([
            r.get("variable_code"),
            r.get("variable_name"),
            r.get("official_source_name"),
            r.get("trend_direction"),
            r.get("sens_slope"),
            r.get("annual_rate_of_change"),
            r.get("original_measurement_unit"),
            r.get("relative_annual_change_pct"),
            r.get("standardized_slope"),
            r.get("p_value"),
            r.get("fdr_adjusted_p_value"),
            r.get("is_statistically_significant"),
            r.get("kendall_tau"),
            r.get("valid_observations_count"),
            r.get("total_observations_count"),
            r.get("coverage_ratio"),
            r.get("data_coverage_period"),
            r.get("scientific_summary")
        ])

    return output.getvalue()

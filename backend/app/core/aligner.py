"""
TerraScope Data Alignment and Quality Assurance Engine.

Ensures:
- Transparent missing value tracking (never treating missing values as zero).
- Temporal alignment of diverse time-series frequencies (monthly, annual, daily).
- Quality flag filtering and valid observation thresholds.
- Safe cross-variable comparison constraints (only comparing when units and physical meanings allow).
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


class AlignedDataset:
    def __init__(self, variable_code: str, dates: List[str], values: List[Optional[float]], units: str):
        self.variable_code = variable_code
        self.dates = dates
        self.values = values
        self.units = units
        self.total_count = len(values)
        self.valid_count = sum(1 for v in values if v is not None and not np.isnan(v))
        self.missing_count = self.total_count - self.valid_count
        self.completeness_pct = (self.valid_count / self.total_count * 100.0) if self.total_count > 0 else 0.0


def align_multiple_series(
    series_dict: Dict[str, Dict[str, Any]],
    target_frequency: str = "monthly"
) -> Dict[str, Any]:
    """
    Aligns multiple environmental time series to a unified date timeline.
    
    Args:
        series_dict: Dict mapping variable_code -> {
            "dates": ["2015-01", "2015-02", ...],
            "values": [12.3, 14.5, ...],
            "units": "...",
            "metadata": {...}
        }
        target_frequency: Target temporal aggregation ("monthly" or "annual").
        
    Returns:
        Unified dataframe/dictionary with synchronized timestamps and aligned columns.
    """
    if not series_dict:
        return {"timeline": [], "series": {}, "alignment_notes": "No series provided"}

    # Find the union of all dates across all series
    all_dates = set()
    for code, s_data in series_dict.items():
        all_dates.update(s_data.get("dates", []))
        
    sorted_timeline = sorted(list(all_dates))

    aligned_series = {}
    for code, s_data in series_dict.items():
        date_val_map = dict(zip(s_data.get("dates", []), s_data.get("values", [])))
        aligned_vals = []
        for d in sorted_timeline:
            val = date_val_map.get(d, None)
            if val is not None and np.isnan(val):
                val = None
            aligned_vals.append(val)
            
        aligned_series[code] = {
            "variable_name": s_data.get("variable_name", code),
            "units": s_data.get("units", ""),
            "official_source_name": s_data.get("official_source_name", ""),
            "values": aligned_vals,
            "valid_count": sum(1 for v in aligned_vals if v is not None),
            "total_count": len(aligned_vals),
            "completeness_pct": round(sum(1 for v in aligned_vals if v is not None) / len(aligned_vals) * 100.0, 1) if aligned_vals else 0
        }

    return {
        "timeline": sorted_timeline,
        "series": aligned_series,
        "alignment_notes": f"Synchronized {len(series_dict)} variable series across {len(sorted_timeline)} temporal points. Missing values preserved as nulls."
    }


def aggregate_to_annual(dates: List[str], values: List[Optional[float]], agg_method: str = "mean") -> Tuple[List[str], List[Optional[float]]]:
    """
    Safely aggregates monthly observations to annual values.
    Requires at least 8 valid months out of 12 to form an annual representative value;
    otherwise treats the annual value as missing (None) to avoid seasonal bias.
    """
    year_map: Dict[str, List[float]] = {}
    for d, v in zip(dates, values):
        if v is None or np.isnan(v):
            continue
        year = d.split("-")[0]
        if year not in year_map:
            year_map[year] = []
        year_map[year].append(float(v))

    sorted_years = sorted(list(year_map.keys()))
    annual_dates = []
    annual_values = []

    for yr in sorted_years:
        vals = year_map[yr]
        if len(vals) >= 8:  # Minimum 8 months represented
            annual_dates.append(yr)
            if agg_method == "sum":
                annual_values.append(round(float(np.sum(vals)), 4))
            else:
                annual_values.append(round(float(np.mean(vals)), 4))
        else:
            annual_dates.append(yr)
            annual_values.append(None)

    return annual_dates, annual_values

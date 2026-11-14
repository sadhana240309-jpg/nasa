"""
Routes for Statistical Trend Analysis & Cross-Variable Comparison.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from backend.app.core.statistics import compute_mann_kendall, rank_and_analyze_variables
from backend.app.core.discovery import discovery_engine

router = APIRouter(prefix="/analysis", tags=["Scientific Analysis & Comparison"])


class CompareRequest(BaseModel):
    region_a: Dict[str, Any]
    region_b: Optional[Dict[str, Any]] = None
    time_window_a: Dict[str, int]
    time_window_b: Optional[Dict[str, int]] = None
    variable_codes: List[str]


@router.post("/compare")
def compare_environmental_trends(payload: CompareRequest):
    """
    Compares trends across different:
    - Variables
    - Approved data sources
    - Time periods (e.g. 2010-2017 vs 2017-2024)
    - Geographical regions (Region A vs Region B)
    """
    results_a = discovery_engine.discover_and_analyze(
        region=payload.region_a,
        start_year=payload.time_window_a["start_year"],
        end_year=payload.time_window_a["end_year"],
    )

    results_b = None
    if payload.region_b or payload.time_window_b:
        reg_b = payload.region_b or payload.region_a
        win_b = payload.time_window_b or payload.time_window_a
        results_b = discovery_engine.discover_and_analyze(
            region=reg_b,
            start_year=win_b["start_year"],
            end_year=win_b["end_year"],
        )

    return {
        "condition_a": {
            "region": payload.region_a,
            "time_window": payload.time_window_a,
            "results": results_a
        },
        "condition_b": {
            "region": payload.region_b or payload.region_a,
            "time_window": payload.time_window_b or payload.time_window_a,
            "results": results_b
        } if results_b else None,
        "comparability_notes": "Comparisons are normalized by standardized slope (Z-score change / year) to ensure fairness across heterogeneous units."
    }

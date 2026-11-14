"""
Routes for Automated Multi-Variable Discovery.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from backend.app.core.discovery import discovery_engine

router = APIRouter(prefix="/discovery", tags=["Automated Discovery"])


class DiscoveryRequest(BaseModel):
    region: Dict[str, Any] = Field(
        default={
            "country": "India",
            "state": "Maharashtra",
            "district": "Pune",
            "name": "Pune, Maharashtra, India",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "bbox": [73.5, 18.2, 74.2, 18.8]
        }
    )
    start_year: int = Field(default=2015, ge=1980, le=2026)
    end_year: int = Field(default=2024, ge=1980, le=2026)
    alpha: float = Field(default=0.05, gt=0.0, le=0.5)
    selected_sources: Optional[List[str]] = None


@router.post("/run", response_model=Dict[str, Any])
def run_automated_discovery(payload: DiscoveryRequest):
    """
    Executes automated environmental trend discovery across the approved sources.
    Automatically discovers and tests all eligible variables for the selected region and time window.
    """
    if payload.start_year > payload.end_year:
        raise HTTPException(status_code=400, detail="Start year cannot be greater than end year.")
    
    if (payload.end_year - payload.start_year) < 3:
        raise HTTPException(
            status_code=400,
            detail="A minimum time span of at least 3 years is required for meaningful multi-annual environmental trend discovery."
        )

    try:
        results = discovery_engine.discover_and_analyze(
            region=payload.region,
            start_year=payload.start_year,
            end_year=payload.end_year,
            alpha=payload.alpha,
            selected_sources=payload.selected_sources
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery execution error: {str(e)}")

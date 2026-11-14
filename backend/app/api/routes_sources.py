"""
Routes for Approved Data Sources Management & Status Monitoring.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from backend.app.core.registry import APPROVED_SOURCES_REGISTRY
from backend.app.core.discovery import discovery_engine

router = APIRouter(prefix="/sources", tags=["Approved Data Sources"])


@router.get("", response_model=List[Dict[str, Any]])
def list_approved_sources():
    """Lists all six official approved data sources with metadata and capabilities."""
    sources = []
    for s in APPROVED_SOURCES_REGISTRY.values():
        sources.append(s.model_dump())
    return sources


@router.get("/status", response_model=List[Dict[str, Any]])
def check_source_connectivity():
    """Probes all six approved sources to evaluate availability and connection status."""
    return discovery_engine.get_all_source_statuses()

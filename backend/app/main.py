"""
TerraScope Backend Application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

from backend.app.config import settings
from backend.app.api.routes_sources import router as sources_router
from backend.app.api.routes_discovery import router as discovery_router
from backend.app.api.routes_analysis import router as analysis_router
from backend.app.api.routes_export import router as export_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated Multi-Variable Environmental Trend Discovery Platform connecting to official Earth science data archives."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(discovery_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(export_router, prefix=settings.API_V1_STR)


@app.get("/health")
def healthcheck():
    return {"status": "healthy", "service": "TerraScope API"}


@app.get("/api/meta")
def meta():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "approved_sources": [
            "NASA Giovanni",
            "NASA Hydrology Time Series",
            "NASA AppEEARS",
            "NOAA Climate Data Online (CDO)",
            "KNMI Climate Explorer",
            "Canadian Space Agency (CSA) – RADARSAT Constellation Mission"
        ],
        "strict_policy": "No external APIs or synthetic datasets permitted."
    }


# Mount compiled frontend dist if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API paths
        if full_path.startswith("api"):
            return None
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

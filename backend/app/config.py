import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
DEMO_DIR = DATA_DIR / "demonstration"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
DEMO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "TerraScope"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # NASA Earthdata credentials (for Giovanni, Hydrology Data Rods, AppEEARS)
    EARTHDATA_USERNAME: str = os.getenv("EARTHDATA_USERNAME", "")
    EARTHDATA_PASSWORD: str = os.getenv("EARTHDATA_PASSWORD", "")
    EARTHDATA_TOKEN: str = os.getenv("EARTHDATA_TOKEN", "")
    
    # NOAA CDO token (free token from https://www.ncei.noaa.gov/cdo-web/token)
    NOAA_CDO_TOKEN: str = os.getenv("NOAA_CDO_TOKEN", "")
    
    # CSA EODMS credentials (https://www.eodms-sgdot.nrcan-rncan.gc.ca/)
    EODMS_USERNAME: str = os.getenv("EODMS_USERNAME", "")
    EODMS_PASSWORD: str = os.getenv("EODMS_PASSWORD", "")
    
    # Demonstration fallback configuration
    ALLOW_DEMO_DATA: bool = True
    
    # Host & Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000

settings = Settings()

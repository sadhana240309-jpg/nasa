import time
import asyncio
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.core.discovery import discovery_engine

async def run():
    print("Testing Discovery Engine Performance...", flush=True)
    t0 = time.time()
    res = await discovery_engine.discover_and_analyze(
        region={
            "country": "India",
            "state": "Maharashtra",
            "district": "Pune",
            "name": "Pune, Maharashtra, India",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "bbox": [73.5, 18.2, 74.2, 18.8]
        },
        start_year=2015,
        end_year=2024,
        alpha=0.05
    )
    t1 = time.time()
    print(f"Elapsed: {t1 - t0:.3f} seconds!", flush=True)
    print(f"Total Variables: {res['summary']['total_variables_analyzed']}", flush=True)
    print(f"Significant Trends: {res['summary']['statistically_significant_trends']}", flush=True)
    print(f"Increasing Trends: {res['summary']['increasing_trends']}", flush=True)
    print(f"Decreasing Trends: {res['summary']['decreasing_trends']}", flush=True)

if __name__ == "__main__":
    asyncio.run(run())

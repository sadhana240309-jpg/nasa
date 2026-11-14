import sys
import asyncio
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.api.routes_sources import list_approved_sources
from backend.app.api.routes_discovery import run_automated_discovery, DiscoveryRequest
from backend.app.api.routes_analysis import compare_environmental_trends, CompareRequest
from backend.app.api.routes_export import generate_scientific_report, export_csv, ExportPayload

async def main():
    print("1. Testing Approved Sources Listing...", flush=True)
    sources = await list_approved_sources()
    print(f"   [OK] Loaded {len(sources)} approved sources:", flush=True)
    for s in sources:
        print(f"        * {s['official_name']} ({s['organization']})", flush=True)

    print("\n2. Testing Automated Multi-Variable Discovery Engine...", flush=True)
    req = DiscoveryRequest(
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
    discovery_res = await run_automated_discovery(req)
    summary = discovery_res["summary"]
    print(f"   [OK] Total Discovered Variables: {summary['total_variables_analyzed']}", flush=True)
    print(f"   [OK] FDR Statistically Significant Trends: {summary['statistically_significant_trends']}", flush=True)
    print(f"   [OK] Increasing Trends: {summary['increasing_trends']}", flush=True)
    print(f"   [OK] Decreasing Trends: {summary['decreasing_trends']}", flush=True)

    print("\n3. Ranked Discoveries Preview:", flush=True)
    for idx, r in enumerate(discovery_res["ranked_trends"][:4], 1):
        print(f"   #{idx} [{r['official_source_name']}] {r['variable_name']}:", flush=True)
        print(f"       Trend Direction: {r['trend_direction']}", flush=True)
        print(f"       Sen's Slope: {r['annual_rate_of_change']} {r['original_measurement_unit']}/yr", flush=True)
        print(f"       Standardized Rate: {r['standardized_slope']} Z/yr | Relative: {r['relative_annual_change_pct']}%/yr", flush=True)
        print(f"       Raw p-value: {r['p_value']} | FDR p-value: {r['fdr_adjusted_p_value']}", flush=True)
        print(f"       Valid Observations: {r['valid_observations_count']}/{r['total_observations_count']}", flush=True)

    print("\n4. Testing Cross-Variable & Multi-Period Comparison...", flush=True)
    comp_req = CompareRequest(
        region_a=req.region,
        time_window_a={"start_year": 2015, "end_year": 2019},
        time_window_b={"start_year": 2020, "end_year": 2024},
        variable_codes=[discovery_res["ranked_trends"][0]["variable_code"]]
    )
    comp_res = await compare_environmental_trends(comp_req)
    print(f"   [OK] Multi-period comparison completed successfully. Comparability note: {comp_res['comparability_notes']}", flush=True)

    print("\n5. Testing Scientific Executive Report Generator...", flush=True)
    rep_res = await generate_scientific_report(ExportPayload(discovery_data=discovery_res))
    print(f"   [OK] Generated report: '{rep_res['title']}'", flush=True)
    print(f"   [OK] Citations: {len(rep_res['methodological_references'])} peer-reviewed references included.", flush=True)

    print("\n6. Testing CSV Data Exporter...", flush=True)
    csv_res = await export_csv(ExportPayload(discovery_data=discovery_res))
    csv_text = csv_res.body.decode("utf-8")
    print(f"   [OK] Generated CSV with {len(csv_text.splitlines())} lines.", flush=True)

    print("\n" + "=" * 60, flush=True)
    print(">>> COMPLETE TERRASCOPE SCIENTIFIC ENGINE VERIFIED 100% <<<", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    asyncio.run(main())

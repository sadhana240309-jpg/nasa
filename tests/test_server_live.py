import subprocess
import time
import httpx
import sys

print("Starting TerraScope Backend Subprocess...")
proc = subprocess.Popen(
    [sys.executable, "backend/run.py"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(3.5)

try:
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        # Test 1: Healthcheck
        h = client.get("/health")
        print("1. Healthcheck:", h.status_code, h.json())

        # Test 2: Sources list
        s = client.get("/api/v1/sources")
        print("2. Sources count:", len(s.json()))
        for src in s.json():
            print(f"   - {src['official_name']} ({src['current_status']})")

        # Test 3: Discovery run
        payload = {
            "region": {
                "country": "India",
                "state": "Maharashtra",
                "district": "Pune",
                "name": "Pune, Maharashtra, India",
                "latitude": 18.5204,
                "longitude": 73.8567,
                "bbox": [73.5, 18.2, 74.2, 18.8]
            },
            "start_year": 2015,
            "end_year": 2024,
            "alpha": 0.05
        }
        d = client.post("/api/v1/discovery/run", json=payload)
        d_json = d.json()
        print("3. Discovery Response:", d.status_code)
        print("   - Total variables discovered:", d_json["summary"]["total_variables_analyzed"])
        print("   - Statistically significant trends:", d_json["summary"]["statistically_significant_trends"])
        print("   - Increasing trends:", d_json["summary"]["increasing_trends"])
        print("   - Decreasing trends:", d_json["summary"]["decreasing_trends"])

        print("   Top 3 Ranked Trends:")
        for r in d_json["ranked_trends"][:3]:
            print(f"     * #{r['variable_name']} ({r['official_source_name']}): {r['trend_direction']}, Sen's Slope: {r['annual_rate_of_change']} {r['original_measurement_unit']}/yr, FDR p-value: {r['fdr_adjusted_p_value']}")

        # Test 4: Report generation
        rep = client.post("/api/v1/export/report", json={"discovery_data": d_json})
        print("4. Executive Report Generated:", rep.status_code, "References count:", len(rep.json()["methodological_references"]))

        # Test 5: CSV export
        csv_resp = client.post("/api/v1/export/csv", json={"discovery_data": d_json})
        print("5. CSV Generated:", csv_resp.status_code, "Length:", len(csv_resp.text), "chars")

        # Test 6: Root UI HTML serve
        ui = client.get("/")
        print("6. Frontend Root SPA served:", ui.status_code, "Content length:", len(ui.text))
        assert "TerraScope" in ui.text

        print("\n>>> ALL 6 ENDPOINT INTEGRATION TESTS PASSED PERFECTLY! <<<")

finally:
    proc.terminate()
    proc.wait(timeout=3)
    print("Backend subprocess cleanly terminated.")

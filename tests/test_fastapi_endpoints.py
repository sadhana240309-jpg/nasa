import sys
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("--- Testing TerraScope Endpoints via ASGI in-memory TestClient ---")

# 1. Test healthcheck
h = client.get("/health")
print("1. Healthcheck:", h.status_code, h.json())
assert h.status_code == 200

# 2. Test metadata
meta = client.get("/api/meta")
print("2. Platform Meta:", meta.status_code, meta.json()["platform"])
assert meta.status_code == 200

# 3. Test sources list
s = client.get("/api/v1/sources")
print("3. Approved Sources:", s.status_code, f"Count = {len(s.json())}")
assert s.status_code == 200
assert len(s.json()) == 6
for src in s.json():
    print(f"   - {src['official_name']} [{src['id']}] -> {src['current_status']}")

# 4. Test automated discovery execution
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
print("4. Discovery Execution:", d.status_code)
assert d.status_code == 200
d_json = d.json()
print("   - Total variables discovered:", d_json["summary"]["total_variables_analyzed"])
print("   - Statistically significant trends:", d_json["summary"]["statistically_significant_trends"])
print("   - Increasing trends:", d_json["summary"]["increasing_trends"])
print("   - Decreasing trends:", d_json["summary"]["decreasing_trends"])

print("\n   Discovered Variables Summary:")
for r in d_json["ranked_trends"][:5]:
    print(f"   [{r['official_source_name']}] {r['variable_name']}: {r['trend_direction']} | Slope: {r['annual_rate_of_change']} {r['original_measurement_unit']}/yr | FDR p-value: {r['fdr_adjusted_p_value']}")

# 5. Test Comparison Endpoint
comp_payload = {
    "region_a": payload["region"],
    "time_window_a": {"start_year": 2015, "end_year": 2019},
    "time_window_b": {"start_year": 2020, "end_year": 2024},
    "variable_codes": [d_json["ranked_trends"][0]["variable_code"]]
}
c = client.post("/api/v1/analysis/compare", json=comp_payload)
print("\n5. Comparison Analysis:", c.status_code)
assert c.status_code == 200

# 6. Test Scientific Report generation
rep = client.post("/api/v1/export/report", json={"discovery_data": d_json})
print("6. Scientific Executive Report:", rep.status_code)
assert rep.status_code == 200
print("   Citations count:", len(rep.json()["methodological_references"]))

# 7. Test CSV Export
csv_resp = client.post("/api/v1/export/csv", json={"discovery_data": d_json})
print("7. CSV Export:", csv_resp.status_code, "Length:", len(csv_resp.text), "chars")
assert csv_resp.status_code == 200
assert "Variable Code,Variable Name" in csv_resp.text

# 8. Test Frontend SPA HTML root
ui = client.get("/")
print("8. Frontend UI Root:", ui.status_code, "HTML Length:", len(ui.text))
assert ui.status_code == 200
assert "TerraScope" in ui.text

print("\n========================================================")
print(">>> ALL 8 SCIENTIFIC & API PIPELINE TESTS PASSED 100% <<<")
print("========================================================")

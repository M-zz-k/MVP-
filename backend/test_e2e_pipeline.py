import sys
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    print("PASS: /health endpoint")

def test_home():
    res = client.get("/")
    assert res.status_code == 200
    print("PASS: / (home) endpoint")

def test_weather_endpoint():
    res = client.get("/weather?latitude=12.97&longitude=77.59&start_date=2024-01-01&end_date=2024-01-05&daily_variables=temperature_2m_max,temperature_2m_min&analysis=true")
    assert res.status_code == 200
    data = res.json()
    assert "weather" in data
    assert "trend_analysis" in data
    print("PASS: /weather direct analysis endpoint")

def test_stac_search_endpoint():
    res = client.get("/search?latitude=12.97&longitude=77.59&start_date=2024-05-01&end_date=2024-05-31&max_cloud_cover=20")
    assert res.status_code == 200
    data = res.json()
    assert "scenes" in data
    print(f"PASS: /search STAC endpoint (found {data['total_scenes_found']} scenes)")

def test_query_pipeline():
    payload = {"text": "What were the weather trends in Paris between 2024-06-01 and 2024-06-05?"}
    res = client.post("/query", json=payload)
    print(f"Status: {res.status_code}")
    data = res.json()
    print("Query Response Summary:")
    print(f"  Original: {data.get('query', {}).get('original')}")
    print(f"  Interpreted As: {data.get('query', {}).get('interpreted_as')}")
    print(f"  Resolved Location: {data.get('resolved_location', {}).get('name')}")
    print(f"  Query Plan Bands: {data.get('query_plan', {}).get('bands')}")
    print(f"  Answer: {data.get('answer')}")
    assert res.status_code == 200
    print("PASS: End-to-end /query pipeline")

if __name__ == "__main__":
    test_health()
    test_home()
    test_weather_endpoint()
    test_stac_search_endpoint()
    test_query_pipeline()

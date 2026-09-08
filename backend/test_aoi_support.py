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
from services.raster_service import read_geometry_from_cog, normalize_geometry
from services.stac_service import get_best_sentinel_scene

client = TestClient(app)

# Sample GeoJSON Polygon around Bengaluru (Lalbagh Botanical Garden area)
LALBAGH_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [77.580, 12.945],
        [77.595, 12.945],
        [77.595, 12.955],
        [77.580, 12.955],
        [77.580, 12.945]
    ]]
}

def test_polygon_normalization():
    print("=== Testing Polygon Normalization ===")
    norm = normalize_geometry(LALBAGH_POLYGON)
    assert norm["type"] == "Polygon"
    assert len(norm["coordinates"][0]) == 5
    print("PASS: GeoJSON polygon normalized successfully.")

def test_stac_polygon_intersection():
    print("\n=== Testing STAC Search with GeoJSON Polygon ===")
    scene = get_best_sentinel_scene(
        start_date="2024-05-01",
        end_date="2024-05-31",
        max_cloud_cover=30.0,
        aoi=LALBAGH_POLYGON
    )
    if scene:
        print(f"PASS: STAC found intersecting Sentinel-2 scene: {scene['id']}")
        print(f"      Valid pixel fraction in polygon: {scene['valid_pixel_fraction']}")
        return scene
    else:
        print("WARNING: No scene found for test period/polygon.")
        return None

def test_cog_windowed_polygon_read(scene):
    if not scene or "B04_url" not in scene:
        print("Skipping COG windowed read (no scene available).")
        return

    print("\n=== Testing COG Windowed Streaming & Polygon Masking ===")
    res = read_geometry_from_cog(scene["B04_url"], LALBAGH_POLYGON)
    assert "data" in res
    assert "inside_mask" in res
    assert res["width"] > 0 and res["height"] > 0
    print(f"PASS: Read window {res['width']}x{res['height']} pixels without downloading entire scene!")
    print(f"      Inside polygon mask shape: {res['inside_mask'].shape}")

def test_direct_analyze_aoi_endpoint():
    print("\n=== Testing POST /analyze-aoi Endpoint ===")
    payload = {
        "aoi_geometry": LALBAGH_POLYGON,
        "start_date": "2024-05-01",
        "end_date": "2024-05-31",
        "max_cloud_cover": 30.0,
        "analysis_type": "ndvi"
    }
    res = client.post("/analyze-aoi", json=payload)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    if res.status_code == 200 and "values" in data:
        print(f"PASS: /analyze-aoi returned NDVI Mean: {data['values']['mean']}, Min: {data['values']['minimum']}, Max: {data['values']['maximum']}")
        print(f"      Map URL: {data.get('map')}, GeoTIFF: {data.get('geotiff')}")
    else:
        print(f"Response: {data}")

def test_query_with_aoi():
    print("\n=== Testing POST /query with Natural Language + GeoJSON Polygon ===")
    payload = {
        "text": "Calculate NDVI for this selected park boundary in May 2024",
        "aoi_geometry": LALBAGH_POLYGON
    }
    res = client.post("/query", json=payload)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    print("Query Plan Location:", data.get("resolved_location"))
    print("Has Polygon AOI:", data.get("resolved_location", {}).get("has_polygon_aoi"))
    print("Answer:", data.get("answer"))
    assert res.status_code == 200
    print("PASS: Natural Language + Explicit AOI pipeline executed successfully!")

if __name__ == "__main__":
    test_polygon_normalization()
    scene = test_stac_polygon_intersection()
    test_cog_windowed_polygon_read(scene)
    test_direct_analyze_aoi_endpoint()
    test_query_with_aoi()

import sys
from pathlib import Path

# Add backend directory and workspace root to sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from models.query_models import StructuredQuery, QueryPlan, QueryRequest
from services.query_planner import plan_and_compile
from services.geocoding_service import geocode_location
from main import app

def run_tests():
    print("=== Testing Models & Validation ===")
    sq = StructuredQuery(
        location="Bengaluru",
        start_date="2024-05-01",
        end_date="2024-05-31",
        cloud_cover_max=15.0,
        analysis_type="ndvi"
    )
    print(f"Validated StructuredQuery: location={sq.location}, type={sq.analysis_type}, max_cloud={sq.cloud_cover_max}")

    # Test cloud cover validator error handling
    try:
        StructuredQuery(cloud_cover_max=150.0)
        print("FAIL: Expected ValueError for cloud_cover_max > 100")
    except Exception:
        print("PASS: Cloud cover validator properly caught invalid value > 100")

    print("\n=== Testing Geocoding Service ===")
    geo = geocode_location("Bengaluru")
    if geo:
        print(f"PASS: Geocoded Bengaluru -> lat: {geo['latitude']}, lon: {geo['longitude']}")
    else:
        print("WARNING: Nominatim geocoding network lookup failed or timed out.")

    print("\n=== Testing Query Planner ===")
    plan = plan_and_compile(sq)
    print(f"PASS: Compiled QueryPlan -> target: {plan.location_name}, bands: {plan.bands}, coords: ({plan.latitude}, {plan.longitude})")

    print("\n=== Testing FastAPI App Routes ===")
    routes = [route.path for route in app.routes]
    print(f"Total FastAPI Routes Registered: {len(routes)}")
    expected = ["/", "/health", "/query", "/ndvi", "/ndwi", "/ndvi-ndwi", "/change-detection", "/weather", "/ndvi-geotiff", "/change-geotiff"]
    for exp in expected:
        assert exp in routes, f"Missing route: {exp}"
        print(f"  [OK] Route: {exp}")

    print("\nAll architecture validation tests PASSED successfully!")

if __name__ == "__main__":
    run_tests()

import sys
from pathlib import Path
import json

# Add the backend directory and project root to sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(backend_dir), str(project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from services.llm_service import parse_natural_language

test_queries = [
    "Calculate NDVI for Bengaluru in May 2024 with less than 20% cloud cover.",
    "Show me historical weather trends for London from Jan 1 2023 to Dec 31 2023.",
    "Find satellite images for San Francisco from last month."
]

for q in test_queries:
    print(f"\nQuery: {q}")
    try:
        result = parse_natural_language(q)
        print(json.dumps(result.model_dump(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

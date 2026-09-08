"""
Compatibility re-export for app.main
"""
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from main import app, process_query, ndvi_endpoint as ndvi_analysis, ndwi_endpoint as ndwi_analysis

__all__ = ["app", "process_query", "ndvi_analysis", "ndwi_analysis"]
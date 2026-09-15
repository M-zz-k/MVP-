import os
import sys
import time
from pathlib import Path
from typing import Optional, List

# Add backend directory and workspace root to sys.path
_backend_dir = Path(__file__).resolve().parent
_project_root = _backend_dir.parent
for _p in [str(_backend_dir), str(_project_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from utils.config import MAPS_DIR, GRAPHS_DIR
from models.query_models import QueryRequest, DirectAOIAnalysisRequest, QueryPlan
from services.llm_service import parse_natural_language, generate_explanation
from services.query_planner import plan_and_compile
from services.stac_service import search_sentinel_scenes, get_best_sentinel_scene
from services.raster_service import read_geometry_from_cog
from services.analysis_service import (
    run_ndvi_analysis,
    run_ndwi_analysis,
    run_ndvi_ndwi_analysis,
    execute_query_analysis
)
from services.weather_service import run_weather_analysis
from services.change_detection_service import run_change_detection

app = FastAPI(
    title="GeoQuery AI",
    description="Natural Language & AOI Gateway for Earth Observation & Geospatial Intelligence",
    version="0.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# General & Health Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "title": "GeoQuery AI API",
        "status": "operational",
        "version": "0.4.0",
        "endpoints": {
            "query": "/query (POST)",
            "analyze_aoi": "/analyze-aoi (POST)",
            "ndvi": "/ndvi (GET)",
            "ndwi": "/ndwi (GET)",
            "change_detection": "/change-detection (GET)",
            "weather": "/weather (GET)",
            "search": "/search (GET)"
        }
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Natural Language + Explicit AOI Query Pipeline
# ---------------------------------------------------------------------------

@app.post("/query")
def process_query(request: QueryRequest):
    """
    End-to-End GeoQuery Pipeline:
    Natural Language -> Gemini Extraction -> Pydantic Validation -> Query Planner (with AOI priority) -> Execution Engine -> Explanation
    """
    start_total = time.time()
    
    # DEMO MODE - allows frontend testing without using Gemini quota
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

    if DEMO_MODE:
        text = request.text.lower()

        # Default demo location
        location = "Bengaluru"
        latitude = 12.9716
        longitude = 77.5946

        # ---------------------------------------------------------
        # WATER BODIES / NDWI
        # ---------------------------------------------------------
        if "water" in text or "ndwi" in text:
            location = "Karnataka"
            latitude = 15.3173
            longitude = 75.7139

            return {
                "query": {
                    "original": request.text,
                    "interpreted_as": "ndwi"
                },
                "structured_query": {
                    "analysis_type": "ndwi",
                    "location": location,
                    "start_date": "2026-08-01",
                    "end_date": "2026-09-30",
                    "max_cloud_cover": 100
                },
                "resolved_location": {
                    "name": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "bbox": None,
                    "has_polygon_aoi": False
                },
                "query_plan": {
                    "analysis_type": "ndwi",
                    "location_name": location,
                    "latitude": latitude,
                    "longitude": longitude
                },
                "performance_metrics": {
                    "nlp_parsing_time_sec": 0.01,
                    "planning_geocoding_time_sec": 0.01,
                    "data_access_analysis_time_sec": 0.05,
                    "llm_explanation_time_sec": 0.00,
                    "total_time_sec": 0.07,
                    "traditional_download_estimate_sec": 300
                },
                "analysis": {
                    "mean_ndwi": 0.31,
                    "min_ndwi": -0.42,
                    "max_ndwi": 0.82,
                    "water_coverage_percent": 18.7,
                    "valid_count": 333931,
                    "cloud_cover": 28.4,
                    "satellite": "Sentinel-2",
                    "date": "2026-08-10",
                    "scene": {
                        "id": "DEMO_SENTINEL_2_WATER_SCENE",
                        "datetime": "2026-08-10",
                        "cloud_cover": 28.4
                    }
                },
                "answer": (
                    "Demo water-body analysis completed successfully. "
                    "The result represents sample NDWI data for Karnataka "
                    "and is provided for testing the GeoQuery AI interface "
                    "without using the Gemini API."
                )
            }

        # ---------------------------------------------------------
        # LAND COVER / CHANGE DETECTION
        # ---------------------------------------------------------
        if "land cover" in text or "urban" in text or "change" in text:
            location = "Karnataka"
            latitude = 15.3173
            longitude = 75.7139

            return {
                "query": {
                    "original": request.text,
                    "interpreted_as": "change_detection"
                },
                "structured_query": {
                    "analysis_type": "change_detection",
                    "location": location,
                    "start_date": "2018-01-01",
                    "end_date": "2024-12-31",
                    "max_cloud_cover": 100
                },
                "resolved_location": {
                    "name": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "bbox": None,
                    "has_polygon_aoi": False
                },
                "query_plan": {
                    "analysis_type": "change_detection",
                    "location_name": location,
                    "latitude": latitude,
                    "longitude": longitude
                },
                "performance_metrics": {
                    "nlp_parsing_time_sec": 0.01,
                    "planning_geocoding_time_sec": 0.01,
                    "data_access_analysis_time_sec": 0.05,
                    "llm_explanation_time_sec": 0.00,
                    "total_time_sec": 0.07,
                    "traditional_download_estimate_sec": 300
                },
                "analysis": {
                    "changed_area_percent": 14.8,
                    "urban_expansion_percent": 9.6,
                    "vegetation_change_percent": -4.2,
                    "water_change_percent": 1.7,
                    "cloud_cover": 24.6,
                    "satellite": "Sentinel-2",
                    "date": "2024-12-31",
                    "scene": {
                        "id": "DEMO_SENTINEL_2_CHANGE_SCENE",
                        "datetime": "2024-12-31",
                        "cloud_cover": 24.6
                    }
                },
                "answer": (
                    "Demo land-cover change analysis completed successfully. "
                    "The result represents sample satellite change data for "
                    "Karnataka and is provided for testing the GeoQuery AI "
                    "interface without using the Gemini API."
                )
            }

        # ---------------------------------------------------------
        # DEFAULT / VEGETATION / NDVI
        # ---------------------------------------------------------
        return {
            "query": {
                "original": request.text,
                "interpreted_as": "ndvi"
            },
            "structured_query": {
                "analysis_type": "ndvi",
                "location": "Bengaluru",
                "start_date": "2026-08-01",
                "end_date": "2026-09-30",
                "max_cloud_cover": 100
            },
            "resolved_location": {
                "name": "Bengaluru",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "bbox": None,
                "has_polygon_aoi": False
            },
            "query_plan": {
                "analysis_type": "ndvi",
                "location_name": "Bengaluru",
                "latitude": 12.9716,
                "longitude": 77.5946
            },
            "performance_metrics": {
                "nlp_parsing_time_sec": 0.01,
                "planning_geocoding_time_sec": 0.01,
                "data_access_analysis_time_sec": 0.05,
                "llm_explanation_time_sec": 0.00,
                "total_time_sec": 0.07,
                "traditional_download_estimate_sec": 300
            },
            "analysis": {
                "mean_ndvi": 0.247,
                "min_ndvi": -0.129,
                "max_ndvi": 0.687,
                "std_ndvi": 0.139,
                "vegetation_coverage_percent": 62.4,
                "valid_count": 333931,
                "cloud_cover": 32.9,
                "satellite": "Sentinel-2",
                "date": "2026-08-10",
                "scene": {
                    "id": "DEMO_SENTINEL_2_SCENE",
                    "datetime": "2026-08-10",
                    "cloud_cover": 32.9
                }
            },
            "answer": (
                "Demo vegetation analysis completed successfully. "
                "This is sample NDVI data for Bengaluru generated for "
                "testing the GeoQuery AI interface without using the Gemini API."
            )
        }

    # Step 1: LLM Extraction
    nlp_start = time.time()
    try:
        structured_query = parse_natural_language(request.text)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI Extraction Error: {str(e)}")
    nlp_time = time.time() - nlp_start

    # Step 2: Query Planning & Geocoding / AOI Validation
    planner_start = time.time()
    try:
        plan = plan_and_compile(
            query=structured_query,
            explicit_aoi=request.aoi_geometry,
            explicit_bbox=request.bbox
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query Planning Error: {str(e)}")
    planner_time = time.time() - planner_start

    # Step 3: Execution Layer (STAC / COG Windowing / Index / ML Analysis)
    execution_start = time.time()
    try:
        analysis_result = execute_query_analysis(plan)
    except Exception as e:
        analysis_result = {"error": str(e)}
    execution_time = time.time() - execution_start

    # Step 4: Final Narrative Explanation
    explanation_start = time.time()
    explanation = "No analysis result generated."
    if "error" not in analysis_result:
        try:
            explanation = generate_explanation(request.text, analysis_result)
        except Exception:
            explanation = f"Analysis completed successfully for {plan.location_name}."
    else:
        explanation = f"Could not complete analysis: {analysis_result.get('error')}"
    explanation_time = time.time() - explanation_start

    total_time = time.time() - start_total

    return {
        "query": {
            "original": request.text,
            "interpreted_as": plan.analysis_type
        },
        "structured_query": structured_query.model_dump(),
        "resolved_location": {
            "name": plan.location_name,
            "latitude": plan.latitude,
            "longitude": plan.longitude,
            "bbox": plan.bbox.model_dump() if plan.bbox else None,
            "has_polygon_aoi": plan.has_polygon_aoi
        },
        "query_plan": plan.model_dump(),
        "performance_metrics": {
            "nlp_parsing_time_sec": round(nlp_time, 2),
            "planning_geocoding_time_sec": round(planner_time, 2),
            "data_access_analysis_time_sec": round(execution_time, 2),
            "llm_explanation_time_sec": round(explanation_time, 2),
            "total_time_sec": round(total_time, 2),
            "traditional_download_estimate_sec": 300
        },
        "analysis": analysis_result,
        "answer": explanation
    }


# ---------------------------------------------------------------------------
# Direct AOI Analysis (for Frontend Polygon / Bounding Box drawing tools)
# ---------------------------------------------------------------------------

@app.post("/analyze-aoi")
def analyze_aoi(payload: DirectAOIAnalysisRequest):
    """
    Directly execute analysis over a user-drawn GeoJSON Polygon or bounding box.
    """
    target_aoi = payload.aoi_geometry or payload.bbox
    if not target_aoi:
        raise HTTPException(status_code=400, detail="Either 'aoi_geometry' or 'bbox' must be provided.")

    if payload.analysis_type == "ndvi":
        return run_ndvi_analysis(
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            cloud_mask=payload.cloud_mask,
            aoi=target_aoi
        )
    elif payload.analysis_type == "ndwi":
        return run_ndwi_analysis(
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            cloud_mask=payload.cloud_mask,
            aoi=target_aoi
        )
    elif payload.analysis_type == "ndvi-ndwi":
        return run_ndvi_ndwi_analysis(
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            cloud_mask=payload.cloud_mask,
            aoi=target_aoi
        )
    elif payload.analysis_type == "change_detection":
        return run_change_detection(
            start_date_t1=payload.start_date,
            end_date_t1=payload.end_date,
            start_date_t2=payload.comparison_start_date or payload.start_date,
            end_date_t2=payload.comparison_end_date or payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            aoi=target_aoi
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {payload.analysis_type}")


# ---------------------------------------------------------------------------
# Direct Analysis Endpoints
# ---------------------------------------------------------------------------

@app.get("/search")
def search_satellite_data(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None
):
    aoi = None
    if all(v is not None for v in [min_lon, min_lat, max_lon, max_lat]):
        aoi = [min_lon, min_lat, max_lon, max_lat]

    return search_sentinel_scenes(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        aoi=aoi
    )


@app.get("/test-aoi")
def test_aoi(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100.0
):
    buffer = 0.005
    target_aoi = [longitude - buffer, latitude - buffer, longitude + buffer, latitude + buffer]
    scene = get_best_sentinel_scene(latitude, longitude, start_date, end_date, max_cloud_cover, True, aoi=target_aoi)
    if scene is None:
        return {"error": "No satellite scenes found"}

    result = read_geometry_from_cog(scene["B04_url"], target_aoi)
    return {
        "scene": {"id": scene["id"], "datetime": scene["datetime"], "cloud_cover": scene["cloud_cover"]},
        "aoi": {"bbox": target_aoi},
        "retrieved_data": {
            "width_pixels": result["width"],
            "height_pixels": result["height"],
            "crs": result["crs_str"],
            "window": result["window"]
        }
    }


@app.get("/ndvi")
def ndvi_endpoint(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True
):
    return run_ndvi_analysis(latitude, longitude, start_date, end_date, max_cloud_cover, cloud_mask)


@app.get("/ndwi")
def ndwi_endpoint(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True
):
    return run_ndwi_analysis(latitude, longitude, start_date, end_date, max_cloud_cover, cloud_mask)


@app.get("/ndvi-ndwi")
def ndvi_ndwi_endpoint(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True
):
    return run_ndvi_ndwi_analysis(latitude, longitude, start_date, end_date, max_cloud_cover, cloud_mask)


@app.get("/change-detection")
def change_detection_endpoint(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date_t1: str = "",
    end_date_t1: str = "",
    start_date_t2: str = "",
    end_date_t2: str = "",
    max_cloud_cover: float = 100.0
):
    return run_change_detection(
        latitude=latitude,
        longitude=longitude,
        start_date_t1=start_date_t1,
        end_date_t1=end_date_t1,
        start_date_t2=start_date_t2,
        end_date_t2=end_date_t2,
        max_cloud_cover=max_cloud_cover
    )


@app.get("/weather")
def weather_endpoint(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_variables: str = Query(None),
    hourly_variables: str = Query(None),
    analysis: bool = False,
    graph_variables: str = Query(None),
    graph_mode: str = "separate"
):
    return run_weather_analysis(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        daily_variables=daily_variables,
        hourly_variables=hourly_variables,
        analysis=analysis,
        graph_variables=graph_variables,
        graph_mode=graph_mode
    )


# ---------------------------------------------------------------------------
# Visual Map & GeoTIFF Export Endpoints
# ---------------------------------------------------------------------------

@app.get("/ndvi-map")
def get_ndvi_map():
    ndvi_path = MAPS_DIR / "ndvi_map.png"
    if not ndvi_path.exists():
        raise HTTPException(status_code=404, detail="NDVI map has not been generated yet. Run an NDVI analysis first.")
    return FileResponse(str(ndvi_path), media_type="image/png")


@app.get("/ndvi-geotiff")
@app.get("/download/ndvi-geotiff")
def get_ndvi_geotiff():
    ndvi_tif = MAPS_DIR / "ndvi_aoi.tif"
    if not ndvi_tif.exists():
        raise HTTPException(status_code=404, detail="NDVI GeoTIFF has not been generated yet. Run an NDVI analysis first.")
    return FileResponse(str(ndvi_tif), media_type="image/tiff", filename="ndvi_aoi.tif")


@app.get("/ndwi-map")
def get_ndwi_map():
    ndwi_path = MAPS_DIR / "ndwi_map.png"
    if not ndwi_path.exists():
        raise HTTPException(status_code=404, detail="NDWI map has not been generated yet. Run an NDWI analysis first.")
    return FileResponse(str(ndwi_path), media_type="image/png")


@app.get("/ndwi-geotiff")
@app.get("/download/ndwi-geotiff")
def get_ndwi_geotiff():
    ndwi_tif = MAPS_DIR / "ndwi_aoi.tif"
    if not ndwi_tif.exists():
        raise HTTPException(status_code=404, detail="NDWI GeoTIFF has not been generated yet. Run an NDWI analysis first.")
    return FileResponse(str(ndwi_tif), media_type="image/tiff", filename="ndwi_aoi.tif")


@app.get("/change-map")
def get_change_map():
    map_path = MAPS_DIR / "change_detection_map.png"
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Change detection map has not been generated yet.")
    return FileResponse(str(map_path), media_type="image/png")


@app.get("/change-geotiff")
@app.get("/download/change-geotiff")
def get_change_geotiff():
    tif_path = MAPS_DIR / "change_detection_aoi.tif"
    if not tif_path.exists():
        raise HTTPException(status_code=404, detail="Change detection GeoTIFF has not been generated yet.")
    return FileResponse(str(tif_path), media_type="image/tiff", filename="change_detection_aoi.tif")


@app.get("/weather-graph/combined")
def get_combined_weather_graph():
    graph_path = GRAPHS_DIR / "combined_weather_graph.png"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Combined weather graph has not been generated yet.")
    return FileResponse(str(graph_path), media_type="image/png")


@app.get("/weather-graph/{variable}")
def get_weather_graph(variable: str):
    graph_path = GRAPHS_DIR / f"{variable}.png"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail=f"Weather graph for '{variable}' has not been generated yet.")
    return FileResponse(str(graph_path), media_type="image/png")

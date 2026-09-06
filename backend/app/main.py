import sys
from pathlib import Path

# Add backend directory and workspace root to sys.path
_backend_dir = Path(__file__).resolve().parent.parent
_project_root = _backend_dir.parent
for _p in [str(_backend_dir), str(_project_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.services.stac_service import (
    search_sentinel_scenes,
    get_best_sentinel_scene
)

from app.services.ndvi_service import (
    calculate_ndvi,
    save_ndvi_image,
    save_ndvi_geotiff
)

from app.services.ndwi_service import (
    calculate_ndwi,
    save_ndwi_image,
    save_ndwi_geotiff
)

from app.services.raster_service import (
    read_aoi_from_cog
)

from app.services.weather_service import (
    get_historical_weather
)

from app.services.weather_analysis_service import (
    analyze_weather_trend
)

from app.services.weather_graph_service import (
    save_weather_graphs
)

import time
from app.services.nlp_service import (
    parse_natural_language,
    generate_explanation
)
from app.services.query_compiler import (
    compile_query
)
from pydantic import BaseModel

class QueryRequest(BaseModel):
    text: str


BASE_DIR = Path(__file__).resolve().parents[2]

MAPS_DIR = BASE_DIR / "maps"
MAPS_DIR.mkdir(exist_ok=True)

GRAPHS_DIR = BASE_DIR / "graphs"
GRAPHS_DIR.mkdir(exist_ok=True)


app = FastAPI(
    title="GeoQuery AI",
    description="Natural Language Gateway for Earth Observation Data",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "GeoQuery AI Backend is Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/query")
def process_query(request: QueryRequest):
    """
    Complete GeoQuery AI Workflow:
    NLP -> Query Compiler -> Execution -> Response
    """
    start_total = time.time()
    
    # Step 1 & 2: NLP and Validation
    nlp_start = time.time()
    try:
        structured_query = parse_natural_language(request.text)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI Service Error: {str(e)}")
    nlp_time = time.time() - nlp_start
    
    # Step 3 & 4: Query Compiler (Geocoding + defaults)
    compiler_start = time.time()
    compiled = compile_query(structured_query)
    compiler_time = time.time() - compiler_start
    
    # Step 5 & 6: Execution Layer (Smart Data Access is inside these functions)
    execution_start = time.time()
    analysis_result = {}

    
    try:
        if compiled.analysis_type == "ndvi":
            analysis_result = ndvi_analysis(
                latitude=compiled.latitude,
                longitude=compiled.longitude,
                start_date=compiled.start_date,
                end_date=compiled.end_date,
                max_cloud_cover=compiled.cloud_cover_max,
                cloud_mask=True
            )
        elif compiled.analysis_type == "ndwi":
            analysis_result = ndwi_analysis(
                latitude=compiled.latitude,
                longitude=compiled.longitude,
                start_date=compiled.start_date,
                end_date=compiled.end_date,
                max_cloud_cover=compiled.cloud_cover_max,
                cloud_mask=True
            )
        elif compiled.analysis_type == "ndvi-ndwi":
            analysis_result = ndvi_ndwi_analysis(
                latitude=compiled.latitude,
                longitude=compiled.longitude,
                start_date=compiled.start_date,
                end_date=compiled.end_date,
                max_cloud_cover=compiled.cloud_cover_max,
                cloud_mask=True
            )
        elif compiled.analysis_type == "weather":
            analysis_result = weather_analysis(
                latitude=compiled.latitude,
                longitude=compiled.longitude,
                start_date=compiled.start_date,
                end_date=compiled.end_date,
                daily_variables="temperature_2m_max,temperature_2m_min,precipitation_sum",
                analysis=True,
                graph_variables="temperature_2m_max,temperature_2m_min",
                graph_mode="combined"
            )
        elif compiled.analysis_type == "search" or compiled.query_type == "data_search":
            analysis_result = search_satellite_data(
                latitude=compiled.latitude,
                longitude=compiled.longitude,
                start_date=compiled.start_date,
                end_date=compiled.end_date,
                max_cloud_cover=compiled.cloud_cover_max
            )
        else:
            analysis_result = {
                "message": f"Query processed for {compiled.location_name}",
                "analysis_type": compiled.analysis_type
            }
    except Exception as e:
        analysis_result = {"error": str(e)}

    execution_time = time.time() - execution_start

    # Step 7: Final Explanation
    explanation_start = time.time()
    explanation = "No analysis result generated to explain."
    if "error" not in analysis_result:
        try:
            explanation = generate_explanation(request.text, analysis_result)
        except Exception:
            explanation = f"Analysis completed successfully for {compiled.location_name}."
    else:
        explanation = f"Could not complete analysis: {analysis_result.get('error')}"
    explanation_time = time.time() - explanation_start

    total_time = time.time() - start_total

    performance_metrics = {
        "nlp_parsing_time_sec": round(nlp_time, 2),
        "geocoding_compiling_time_sec": round(compiler_time, 2),
        "smart_data_access_analysis_time_sec": round(execution_time, 2),
        "llm_explanation_time_sec": round(explanation_time, 2),
        "total_time_sec": round(total_time, 2),
        "traditional_download_estimate_sec": 300 # Estimated 5 mins for full scene download + manual crop
    }

    # Transparent all-in-one response format
    return {
        "query": {
            "original": request.text,
            "interpreted_as": compiled.analysis_type
        },
        "structured_query": structured_query.model_dump(),
        "resolved_location": {
            "name": compiled.location_name,
            "latitude": compiled.latitude,
            "longitude": compiled.longitude
        },
        "compiled_query": compiled.model_dump(),
        "performance_metrics": performance_metrics,
        "analysis": analysis_result,
        "answer": explanation
    }






@app.get("/search")
def search_satellite_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100
):

    return search_sentinel_scenes(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover
    )


@app.get("/test-aoi")
def test_aoi(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100
):
    

    scene = get_best_sentinel_scene(
        latitude,
        longitude,
        start_date,
        end_date,
        max_cloud_cover,
        True
    )

    if scene is None:
        return {
            "error": "No satellite scenes found"
        }
    

    buffer = 0.005

    min_lon = longitude - buffer
    min_lat = latitude - buffer
    max_lon = longitude + buffer
    max_lat = latitude + buffer


    result = read_aoi_from_cog(
        scene["B04_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )
    

    return {
        "scene": {
            "id": scene["id"],
            "datetime": scene["datetime"],
            "cloud_cover": scene["cloud_cover"]
        },

        "aoi": {
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat
        },

        "retrieved_data": {
            "width_pixels": result["width"],
            "height_pixels": result["height"],
            "crs": result["crs"],
            "window": result["window"]
        }
    }

@app.get("/ndvi")
def ndvi_analysis(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100,
    cloud_mask: bool = True
):
    
    scene = get_best_sentinel_scene(
        latitude,
        longitude,
        start_date,
        end_date,
        max_cloud_cover,
        cloud_mask
    )

    if scene is None:
        return {
            "error": "No satellite scenes found"
        }

    buffer = 0.005

    min_lon = longitude - buffer
    min_lat = latitude - buffer
    max_lon = longitude + buffer
    max_lat = latitude + buffer

    result = calculate_ndvi(
        scene["B04_url"],
        scene["B08_url"],
        scene["SCL_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        cloud_mask=cloud_mask
    )

    if "error" in result:
        return result

    ndvi_path = MAPS_DIR / "ndvi_map.png"
    ndvi_tif_path = MAPS_DIR / "ndvi_aoi.tif"

    save_ndvi_image(
        result["ndvi"],
        str(ndvi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    if result.get("transform") is not None and result.get("crs") is not None:
        save_ndvi_geotiff(
            result["ndvi"],
            result["transform"],
            result["crs"],
            str(ndvi_tif_path)
        )

    return {
        "index": "NDVI",

        "scene": {
            "id": scene["id"],
            "datetime": scene["datetime"],
            "cloud_cover": scene["cloud_cover"]
        },

        "cloud_mask": cloud_mask,

        "values": {
            "mean": result["mean"],
            "minimum": result["min"],
            "maximum": result["max"]
        },

        "pixels": {
            "width": result["width"],
            "height": result["height"]
        },

        "map": "/ndvi-map",
        "geotiff": "/ndvi-geotiff",
        "download_geotiff": "/download/ndvi-geotiff"
    }

@app.get("/ndvi-map")
def get_ndvi_map():

    ndvi_path = MAPS_DIR / "ndvi_map.png"
    if not ndvi_path.exists():
        raise HTTPException(status_code=404, detail="NDVI map has not been generated yet. Run an NDVI analysis first.")

    return FileResponse(
        str(ndvi_path),
        media_type="image/png"
    )

@app.get("/ndvi-geotiff")
def get_ndvi_geotiff():

    ndvi_tif = MAPS_DIR / "ndvi_aoi.tif"
    if not ndvi_tif.exists():
        raise HTTPException(status_code=404, detail="NDVI GeoTIFF has not been generated yet. Run an NDVI analysis first.")

    return FileResponse(
        str(ndvi_tif),
        media_type="image/tiff",
        filename="ndvi_aoi.tif"
    )

@app.get("/download/ndvi-geotiff")
def download_ndvi_geotiff():
    return get_ndvi_geotiff()

@app.get("/ndwi")
def ndwi_analysis(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100,
    cloud_mask: bool = True
):

    scene = get_best_sentinel_scene(
        latitude,
        longitude,
        start_date,
        end_date,
        max_cloud_cover,
        cloud_mask
    )

    if scene is None:
        return {
            "error": "No satellite scenes found"
        }

    buffer = 0.005

    min_lon = longitude - buffer
    min_lat = latitude - buffer
    max_lon = longitude + buffer
    max_lat = latitude + buffer

    result = calculate_ndwi(
        scene["B03_url"],
        scene["B08_url"],
        scene["SCL_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        cloud_mask=cloud_mask
    )

    if "error" in result:
        return result

    ndwi_path = MAPS_DIR / "ndwi_map.png"
    ndwi_tif_path = MAPS_DIR / "ndwi_aoi.tif"

    save_ndwi_image(
        result["ndwi"],
        str(ndwi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    if result.get("transform") is not None and result.get("crs") is not None:
        save_ndwi_geotiff(
            result["ndwi"],
            result["transform"],
            result["crs"],
            str(ndwi_tif_path)
        )

    return {
        "index": "NDWI",

        "scene": {
            "id": scene["id"],
            "datetime": scene["datetime"],
            "cloud_cover": scene["cloud_cover"]
        },

        "cloud_mask": cloud_mask,

        "values": {
            "mean": result["mean"],
            "minimum": result["min"],
            "maximum": result["max"]
        },

        "pixels": {
            "width": result["width"],
            "height": result["height"]
        },

        "map": "/ndwi-map",
        "geotiff": "/ndwi-geotiff",
        "download_geotiff": "/download/ndwi-geotiff"
    }

@app.get("/ndwi-map")
def get_ndwi_map():

    ndwi_path = MAPS_DIR / "ndwi_map.png"
    if not ndwi_path.exists():
        raise HTTPException(status_code=404, detail="NDWI map has not been generated yet. Run an NDWI analysis first.")

    return FileResponse(
        str(ndwi_path),
        media_type="image/png"
    )

@app.get("/ndwi-geotiff")
def get_ndwi_geotiff():

    ndwi_tif = MAPS_DIR / "ndwi_aoi.tif"
    if not ndwi_tif.exists():
        raise HTTPException(status_code=404, detail="NDWI GeoTIFF has not been generated yet. Run an NDWI analysis first.")

    return FileResponse(
        str(ndwi_tif),
        media_type="image/tiff",
        filename="ndwi_aoi.tif"
    )

@app.get("/download/ndwi-geotiff")
def download_ndwi_geotiff():
    return get_ndwi_geotiff()

@app.get("/ndvi-ndwi")
def ndvi_ndwi_analysis(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 100,
    cloud_mask: bool = True
):

    scene = get_best_sentinel_scene(
        latitude,
        longitude,
        start_date,
        end_date,
        max_cloud_cover,
        cloud_mask
    )

    if scene is None:
        return {
            "error": "No satellite scenes found"
        }

    buffer = 0.005

    min_lon = longitude - buffer
    min_lat = latitude - buffer
    max_lon = longitude + buffer
    max_lat = latitude + buffer

    ndvi_result = calculate_ndvi(
        scene["B04_url"],
        scene["B08_url"],
        scene["SCL_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        cloud_mask=cloud_mask
    )

    if "error" in ndvi_result:
        return ndvi_result

    ndvi_path = MAPS_DIR / "ndvi_map.png"
    ndvi_tif_path = MAPS_DIR / "ndvi_aoi.tif"

    save_ndvi_image(
        ndvi_result["ndvi"],
        str(ndvi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    if ndvi_result.get("transform") is not None and ndvi_result.get("crs") is not None:
        save_ndvi_geotiff(
            ndvi_result["ndvi"],
            ndvi_result["transform"],
            ndvi_result["crs"],
            str(ndvi_tif_path)
        )

    ndwi_result = calculate_ndwi(
        scene["B03_url"],
        scene["B08_url"],
        scene["SCL_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        cloud_mask=cloud_mask
    )

    if "error" in ndwi_result:
        return ndwi_result

    ndwi_path = MAPS_DIR / "ndwi_map.png"
    ndwi_tif_path = MAPS_DIR / "ndwi_aoi.tif"

    save_ndwi_image(
        ndwi_result["ndwi"],
        str(ndwi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    if ndwi_result.get("transform") is not None and ndwi_result.get("crs") is not None:
        save_ndwi_geotiff(
            ndwi_result["ndwi"],
            ndwi_result["transform"],
            ndwi_result["crs"],
            str(ndwi_tif_path)
        )

    return {

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "period": {
            "start": start_date,
            "end": end_date
        },

        "scene": {
            "id": scene["id"],
            "datetime": scene["datetime"],
            "cloud_cover": scene["cloud_cover"]
        },

        "cloud_mask": cloud_mask,

        "ndvi": {
            "mean": ndvi_result["mean"],
            "minimum": ndvi_result["min"],
            "maximum": ndvi_result["max"],

            "pixels": {
                "width": ndvi_result["width"],
                "height": ndvi_result["height"]
            },

            "map": "/ndvi-map",
            "geotiff": "/ndvi-geotiff",
            "download_geotiff": "/download/ndvi-geotiff"
        },

        "ndwi": {
            "mean": ndwi_result["mean"],
            "minimum": ndwi_result["min"],
            "maximum": ndwi_result["max"],

            "pixels": {
                "width": ndwi_result["width"],
                "height": ndwi_result["height"]
            },

            "map": "/ndwi-map",
            "geotiff": "/ndwi-geotiff",
            "download_geotiff": "/download/ndwi-geotiff"
        }
    }

@app.get("/weather")
def weather_analysis(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_variables: str = None,
    hourly_variables: str = None,
    analysis: bool = False,
    graph_variables: str = None,
    graph_mode: str = "separate"
):

    daily_vars = None
    hourly_vars = None

    if daily_variables:

        daily_vars = [
            variable.strip()
            for variable in daily_variables.split(",")
        ]

    if hourly_variables:

        hourly_vars = [
            variable.strip()
            for variable in hourly_variables.split(",")
        ]

    weather_data = get_historical_weather(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        daily_variables=daily_vars,
        hourly_variables=hourly_vars
    )

    response = {

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "period": {
            "start": start_date,
            "end": end_date
        },

        "weather": weather_data
    }

    if analysis:

        response["trend_analysis"] = analyze_weather_trend(
            weather_data
        )

    if graph_variables:

        variables = [
            variable.strip()
            for variable in graph_variables.split(",")
        ]

        graph_result = save_weather_graphs(
            weather_data,
            variables,
            GRAPHS_DIR,
            graph_mode
        )

        response["graphs"] = graph_result


    return response

@app.get("/weather-graph/combined")
def get_combined_weather_graph():

    graph_path = GRAPHS_DIR / "combined_weather_graph.png"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Combined weather graph has not been generated yet.")

    return FileResponse(
        str(graph_path),
        media_type="image/png"
    )

@app.get("/weather-graph/{variable}")
def get_weather_graph(variable: str):

    graph_path = GRAPHS_DIR / f"{variable}.png"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail=f"Weather graph for '{variable}' has not been generated yet.")

    return FileResponse(
        str(graph_path),
        media_type="image/png"
    )
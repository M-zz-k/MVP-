from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

from backend.app.services.stac_service import (
    search_sentinel_scenes,
    get_best_sentinel_scene
)

from backend.app.services.ndvi_service import (
    calculate_ndvi,
    save_ndvi_image
)

from backend.app.services.ndwi_service import (
    calculate_ndwi,
    save_ndwi_image
)

from backend.app.services.raster_service import (
    read_aoi_from_cog
)

from backend.app.services.weather_service import (
    get_historical_weather
)

from backend.app.services.weather_analysis_service import (
    analyze_weather_trend
)

from backend.app.services.weather_graph_service import (
    save_weather_graphs
)

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

    save_ndvi_image(
        result["ndvi"],
        str(ndvi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
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

        "map": "/ndvi-map"
    }

@app.get("/ndvi-map")
def get_ndvi_map():

    ndvi_path = MAPS_DIR / "ndvi_map.png"

    return FileResponse(
        str(ndvi_path),
        media_type="image/png"
    )

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

    save_ndwi_image(
        result["ndwi"],
        str(ndwi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
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

        "map": "/ndwi-map"
    }

@app.get("/ndwi-map")
def get_ndwi_map():

    ndwi_path = MAPS_DIR / "ndwi_map.png"

    return FileResponse(
        str(ndwi_path),
        media_type="image/png"
    )

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

    save_ndvi_image(
        ndvi_result["ndvi"],
        str(ndvi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
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

    save_ndwi_image(
        ndwi_result["ndwi"],
        str(ndwi_path),
        min_lon,
        min_lat,
        max_lon,
        max_lat
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

            "map": "/ndvi-map"
        },

        "ndwi": {
            "mean": ndwi_result["mean"],
            "minimum": ndwi_result["min"],
            "maximum": ndwi_result["max"],

            "pixels": {
                "width": ndwi_result["width"],
                "height": ndwi_result["height"]
            },

            "map": "/ndwi-map"
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

    return FileResponse(
        str(graph_path),
        media_type="image/png"
    )

@app.get("/weather-graph/{variable}")
def get_weather_graph(variable: str):

    graph_path = GRAPHS_DIR / f"{variable}.png"

    return FileResponse(
        str(graph_path),
        media_type="image/png"
    )
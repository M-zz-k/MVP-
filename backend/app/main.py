from fastapi import FastAPI
from backend.app.services.stac_service import search_sentinel_scenes

from backend.app.services.stac_service import (
    search_sentinel_scenes,
    get_best_sentinel_scene
)

from backend.app.services.raster_service import (
    read_aoi_from_cog
)
app = FastAPI(
    title="GeoQuery AI",
    description="Natural Language Gateway for Earth Observation Data",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "message": "GeoQuery AI Backend is Running 🚀"
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
    max_cloud_cover: float = 20
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
    max_cloud_cover: float = 20
):

    # Step 1: Find best satellite scene
    scene = get_best_sentinel_scene(
        latitude,
        longitude,
        start_date,
        end_date,
        max_cloud_cover
    )

    if scene is None:
        return {
            "error": "No satellite scenes found"
        }

    # Step 2: Create a small AOI around the point
    buffer = 0.005

    min_lon = longitude - buffer
    min_lat = latitude - buffer
    max_lon = longitude + buffer
    max_lat = latitude + buffer

    # Step 3: Read B04 from the remote COG
    result = read_aoi_from_cog(
        scene["B04_url"],
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    # Don't return the actual raster array!
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
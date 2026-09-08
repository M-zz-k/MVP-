import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, Optional, Union, List
from shapely.geometry import shape

from utils.config import MAPS_DIR
from services.raster_service import read_geometry_from_cog, save_geotiff, normalize_geometry
from services.stac_service import get_best_sentinel_scene, search_sentinel_scenes, INVALID_SCL_CLASSES
from services.weather_service import run_weather_analysis
from models.query_models import QueryPlan


# ---------------------------------------------------------------------------
# Pre-Processing & Masking
# ---------------------------------------------------------------------------

def create_cloud_mask(
    scl_url: str,
    aoi: Union[Dict[str, Any], List[float]],
    target_shape=None
) -> np.ndarray:
    """
    Create a boolean valid-pixel mask using Sentinel-2 Scene Classification Layer (SCL).
    True represents clear valid land/water; False represents clouds, shadows, or defective pixels.
    """
    scl = read_geometry_from_cog(
        scl_url,
        aoi,
        output_shape=target_shape
    )
    return ~np.isin(scl["data"], list(INVALID_SCL_CLASSES))


# ---------------------------------------------------------------------------
# Index Calculations (NDVI / NDWI)
# ---------------------------------------------------------------------------

def calculate_ndvi(
    red_url: str,
    nir_url: str,
    scl_url: Optional[str],
    aoi: Union[Dict[str, Any], List[float]],
    cloud_mask: bool = True
) -> Dict[str, Any]:
    """
    Compute Normalized Difference Vegetation Index (NDVI) from Sentinel-2 Band 4 (Red) & Band 8 (NIR).
    Applies both SCL cloud screening and polygon boundary masking.
    Formula: NDVI = (NIR - Red) / (NIR + Red)
    """
    red_result = read_geometry_from_cog(red_url, aoi)
    red = red_result["data"].astype(float)

    nir_result = read_geometry_from_cog(nir_url, aoi)
    nir = nir_result["data"].astype(float)

    inside_mask = red_result.get("inside_mask", np.ones(red.shape, dtype=bool))

    denominator = nir + red
    ndvi = np.full_like(denominator, np.nan, dtype=float)
    valid = denominator != 0
    ndvi[valid] = (nir[valid] - red[valid]) / denominator[valid]

    # Mask pixels outside user-drawn polygon
    ndvi[~inside_mask] = np.nan

    # Mask cloud/shadow pixels via SCL
    if cloud_mask and scl_url:
        scl_mask = create_cloud_mask(
            scl_url, aoi, target_shape=red.shape
        )
        ndvi[~scl_mask] = np.nan

    valid_pixels = ndvi[np.isfinite(ndvi)]
    if valid_pixels.size == 0:
        return {"error": "No valid cloud-free pixels found in the requested AOI."}

    return {
        "ndvi": ndvi,
        "transform": red_result.get("transform"),
        "crs": red_result.get("crs"),
        "mean": round(float(np.mean(valid_pixels)), 4),
        "min": round(float(np.min(valid_pixels)), 4),
        "max": round(float(np.max(valid_pixels)), 4),
        "std": round(float(np.std(valid_pixels)), 4),
        "valid_pixel_count": int(valid_pixels.size),
        "width": int(ndvi.shape[1]),
        "height": int(ndvi.shape[0]),
        "bounds": red_result.get("bounds")
    }


def save_ndvi_image(ndvi: np.ndarray, output_path: str, bounds: List[float]) -> None:
    min_x, min_y, max_x, max_y = bounds
    plt.figure(figsize=(10, 8))
    masked_ndvi = np.ma.masked_invalid(ndvi)
    plt.imshow(
        masked_ndvi,
        vmin=-1,
        vmax=1,
        extent=[min_x, max_x, min_y, max_y],
        origin="upper",
        interpolation="bilinear",
        cmap="RdYlGn"
    )
    plt.colorbar(label="NDVI (Vegetation Index)")
    plt.title("Sentinel-2 NDVI Vegetation Map", fontsize=14, fontweight="bold")
    plt.xlabel("Coordinate X / Longitude", fontsize=11)
    plt.ylabel("Coordinate Y / Latitude", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def save_ndvi_geotiff(ndvi: np.ndarray, transform: Any, crs: Any, output_path: str) -> None:
    save_geotiff(data=ndvi, transform=transform, crs=crs, output_path=output_path, nodata=-9999.0)


def calculate_ndwi(
    green_url: str,
    nir_url: str,
    scl_url: Optional[str],
    aoi: Union[Dict[str, Any], List[float]],
    cloud_mask: bool = True
) -> Dict[str, Any]:
    """
    Compute Normalized Difference Water Index (NDWI) from Sentinel-2 Band 3 (Green) & Band 8 (NIR).
    Formula: NDWI = (Green - NIR) / (Green + NIR)
    """
    green_result = read_geometry_from_cog(green_url, aoi)
    green = green_result["data"].astype(float)

    nir_result = read_geometry_from_cog(nir_url, aoi)
    nir = nir_result["data"].astype(float)

    inside_mask = green_result.get("inside_mask", np.ones(green.shape, dtype=bool))

    denominator = green + nir
    ndwi = np.full_like(denominator, np.nan, dtype=float)
    valid = denominator != 0
    ndwi[valid] = (green[valid] - nir[valid]) / denominator[valid]

    # Mask pixels outside user-drawn polygon
    ndwi[~inside_mask] = np.nan

    # Mask cloud/shadow pixels via SCL
    if cloud_mask and scl_url:
        scl_mask = create_cloud_mask(
            scl_url, aoi, target_shape=green.shape
        )
        ndwi[~scl_mask] = np.nan

    valid_pixels = ndwi[np.isfinite(ndwi)]
    if valid_pixels.size == 0:
        return {"error": "No valid cloud-free pixels found in the requested AOI."}

    return {
        "ndwi": ndwi,
        "transform": green_result.get("transform"),
        "crs": green_result.get("crs"),
        "mean": round(float(np.mean(valid_pixels)), 4),
        "min": round(float(np.min(valid_pixels)), 4),
        "max": round(float(np.max(valid_pixels)), 4),
        "std": round(float(np.std(valid_pixels)), 4),
        "valid_pixel_count": int(valid_pixels.size),
        "width": int(ndwi.shape[1]),
        "height": int(ndwi.shape[0]),
        "bounds": green_result.get("bounds")
    }


def save_ndwi_image(ndwi: np.ndarray, output_path: str, bounds: List[float]) -> None:
    min_x, min_y, max_x, max_y = bounds
    plt.figure(figsize=(10, 8))
    masked_ndwi = np.ma.masked_invalid(ndwi)
    plt.imshow(
        masked_ndwi,
        vmin=-1,
        vmax=1,
        extent=[min_x, max_x, min_y, max_y],
        origin="upper",
        interpolation="bilinear",
        cmap="Blues"
    )
    plt.colorbar(label="NDWI (Water Index)")
    plt.title("Sentinel-2 NDWI Water Body Map", fontsize=14, fontweight="bold")
    plt.xlabel("Coordinate X / Longitude", fontsize=11)
    plt.ylabel("Coordinate Y / Latitude", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def save_ndwi_geotiff(ndwi: np.ndarray, transform: Any, crs: Any, output_path: str) -> None:
    save_geotiff(data=ndwi, transform=transform, crs=crs, output_path=output_path, nodata=-9999.0)


# ---------------------------------------------------------------------------
# High-Level Geo Pipeline Runners
# ---------------------------------------------------------------------------

def resolve_target_aoi(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    aoi: Optional[Union[Dict[str, Any], List[float]]] = None,
    buffer: float = 0.005
) -> Union[Dict[str, Any], List[float]]:
    if aoi is not None:
        return aoi
    if latitude is not None and longitude is not None:
        return [longitude - buffer, latitude - buffer, longitude + buffer, latitude + buffer]
    raise ValueError("Either 'aoi' or ('latitude', 'longitude') is required.")


def run_ndvi_analysis(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True,
    aoi: Optional[Union[Dict[str, Any], List[float]]] = None
) -> Dict[str, Any]:
    target_aoi = resolve_target_aoi(latitude, longitude, aoi)
    scene = get_best_sentinel_scene(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        cloud_mask=cloud_mask,
        aoi=target_aoi
    )
    if scene is None:
        return {"error": "No suitable cloud-screened satellite scenes found for the requested period/AOI."}

    result = calculate_ndvi(
        scene["B04_url"], scene["B08_url"], scene.get("SCL_url"),
        aoi=target_aoi, cloud_mask=cloud_mask
    )
    if "error" in result:
        return result

    ndvi_path = MAPS_DIR / "ndvi_map.png"
    ndvi_tif_path = MAPS_DIR / "ndvi_aoi.tif"

    bounds = result.get("bounds", [0, 0, 1, 1])
    save_ndvi_image(result["ndvi"], str(ndvi_path), bounds)

    if result.get("transform") is not None and result.get("crs") is not None:
        save_ndvi_geotiff(result["ndvi"], result["transform"], result["crs"], str(ndvi_tif_path))

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
            "maximum": result["max"],
            "std": result.get("std")
        },
        "pixels": {
            "width": result["width"],
            "height": result["height"],
            "valid_count": result.get("valid_pixel_count")
        },
        "map": "/ndvi-map",
        "geotiff": "/ndvi-geotiff",
        "download_geotiff": "/download/ndvi-geotiff"
    }


def run_ndwi_analysis(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True,
    aoi: Optional[Union[Dict[str, Any], List[float]]] = None
) -> Dict[str, Any]:
    target_aoi = resolve_target_aoi(latitude, longitude, aoi)
    scene = get_best_sentinel_scene(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        cloud_mask=cloud_mask,
        aoi=target_aoi
    )
    if scene is None:
        return {"error": "No suitable cloud-screened satellite scenes found for the requested period/AOI."}

    result = calculate_ndwi(
        scene["B03_url"], scene["B08_url"], scene.get("SCL_url"),
        aoi=target_aoi, cloud_mask=cloud_mask
    )
    if "error" in result:
        return result

    ndwi_path = MAPS_DIR / "ndwi_map.png"
    ndwi_tif_path = MAPS_DIR / "ndwi_aoi.tif"

    bounds = result.get("bounds", [0, 0, 1, 1])
    save_ndwi_image(result["ndwi"], str(ndwi_path), bounds)

    if result.get("transform") is not None and result.get("crs") is not None:
        save_ndwi_geotiff(result["ndwi"], result["transform"], result["crs"], str(ndwi_tif_path))

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
            "maximum": result["max"],
            "std": result.get("std")
        },
        "pixels": {
            "width": result["width"],
            "height": result["height"],
            "valid_count": result.get("valid_pixel_count")
        },
        "map": "/ndwi-map",
        "geotiff": "/ndwi-geotiff",
        "download_geotiff": "/download/ndwi-geotiff"
    }


def run_ndvi_ndwi_analysis(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date: str = "",
    end_date: str = "",
    max_cloud_cover: float = 100.0,
    cloud_mask: bool = True,
    aoi: Optional[Union[Dict[str, Any], List[float]]] = None
) -> Dict[str, Any]:
    target_aoi = resolve_target_aoi(latitude, longitude, aoi)
    scene = get_best_sentinel_scene(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        cloud_mask=cloud_mask,
        aoi=target_aoi
    )
    if scene is None:
        return {"error": "No suitable cloud-screened satellite scenes found for the requested period/AOI."}

    ndvi_result = calculate_ndvi(
        scene["B04_url"], scene["B08_url"], scene.get("SCL_url"),
        aoi=target_aoi, cloud_mask=cloud_mask
    )
    if "error" in ndvi_result:
        return ndvi_result

    bounds = ndvi_result.get("bounds", [0, 0, 1, 1])
    ndvi_path = MAPS_DIR / "ndvi_map.png"
    ndvi_tif_path = MAPS_DIR / "ndvi_aoi.tif"
    save_ndvi_image(ndvi_result["ndvi"], str(ndvi_path), bounds)

    if ndvi_result.get("transform") is not None and ndvi_result.get("crs") is not None:
        save_ndvi_geotiff(ndvi_result["ndvi"], ndvi_result["transform"], ndvi_result["crs"], str(ndvi_tif_path))

    ndwi_result = calculate_ndwi(
        scene["B03_url"], scene["B08_url"], scene.get("SCL_url"),
        aoi=target_aoi, cloud_mask=cloud_mask
    )
    if "error" in ndwi_result:
        return ndwi_result

    ndwi_path = MAPS_DIR / "ndwi_map.png"
    ndwi_tif_path = MAPS_DIR / "ndwi_aoi.tif"
    save_ndwi_image(ndwi_result["ndwi"], str(ndwi_path), bounds)

    if ndwi_result.get("transform") is not None and ndwi_result.get("crs") is not None:
        save_ndwi_geotiff(ndwi_result["ndwi"], ndwi_result["transform"], ndwi_result["crs"], str(ndwi_tif_path))

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start_date, "end": end_date},
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
            "pixels": {"width": ndvi_result["width"], "height": ndvi_result["height"]},
            "map": "/ndvi-map",
            "geotiff": "/ndvi-geotiff",
            "download_geotiff": "/download/ndvi-geotiff"
        },
        "ndwi": {
            "mean": ndwi_result["mean"],
            "minimum": ndwi_result["min"],
            "maximum": ndwi_result["max"],
            "pixels": {"width": ndwi_result["width"], "height": ndwi_result["height"]},
            "map": "/ndwi-map",
            "geotiff": "/ndwi-geotiff",
            "download_geotiff": "/download/ndwi-geotiff"
        }
    }


# ---------------------------------------------------------------------------
# Central Dispatcher for Compiled / Planned Queries
# ---------------------------------------------------------------------------

def execute_query_analysis(plan: QueryPlan) -> Dict[str, Any]:
    """
    Execute the appropriate geospatial analysis pipeline according to the planned query.
    Utilizes polygon/bounding-box AOI when available.
    """
    target_aoi = plan.aoi_geometry if plan.aoi_geometry else (plan.bbox.to_list() if plan.bbox else None)

    if plan.analysis_type == "ndvi":
        return run_ndvi_analysis(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date=plan.start_date,
            end_date=plan.end_date,
            max_cloud_cover=plan.cloud_cover_max,
            cloud_mask=True,
            aoi=target_aoi
        )
    elif plan.analysis_type == "ndwi":
        return run_ndwi_analysis(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date=plan.start_date,
            end_date=plan.end_date,
            max_cloud_cover=plan.cloud_cover_max,
            cloud_mask=True,
            aoi=target_aoi
        )
    elif plan.analysis_type == "ndvi-ndwi":
        return run_ndvi_ndwi_analysis(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date=plan.start_date,
            end_date=plan.end_date,
            max_cloud_cover=plan.cloud_cover_max,
            cloud_mask=True,
            aoi=target_aoi
        )
    elif plan.analysis_type == "weather":
        return run_weather_analysis(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date=plan.start_date,
            end_date=plan.end_date,
            daily_variables="temperature_2m_max,temperature_2m_min,precipitation_sum",
            analysis=True,
            graph_variables="temperature_2m_max,temperature_2m_min",
            graph_mode="combined"
        )
    elif plan.analysis_type == "change_detection" or plan.query_type == "comparison":
        from services.change_detection_service import run_change_detection
        return run_change_detection(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date_t1=plan.start_date,
            end_date_t1=plan.end_date,
            start_date_t2=plan.comparison_start_date or plan.start_date,
            end_date_t2=plan.comparison_end_date or plan.end_date,
            max_cloud_cover=plan.cloud_cover_max,
            aoi=target_aoi
        )
    elif plan.analysis_type == "search" or plan.query_type == "data_search":
        return search_sentinel_scenes(
            latitude=plan.latitude,
            longitude=plan.longitude,
            start_date=plan.start_date,
            end_date=plan.end_date,
            max_cloud_cover=plan.cloud_cover_max,
            aoi=target_aoi
        )
    else:
        return {
            "message": f"Query processed for {plan.location_name}",
            "analysis_type": plan.analysis_type
        }

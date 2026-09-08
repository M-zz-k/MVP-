import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, Optional, Union, List

from utils.config import MAPS_DIR
from services.raster_service import save_geotiff
from services.stac_service import get_best_sentinel_scene
from services.analysis_service import calculate_ndvi, resolve_target_aoi


def calculate_ndvi_change(
    ndvi_t1: np.ndarray,
    ndvi_t2: np.ndarray,
    loss_threshold: float = -0.15,
    gain_threshold: float = 0.15
) -> Dict[str, Any]:
    """
    Perform bi-temporal change detection and statistical transition categorization.
    """
    min_h = min(ndvi_t1.shape[0], ndvi_t2.shape[0])
    min_w = min(ndvi_t1.shape[1], ndvi_t2.shape[1])
    t1_cropped = ndvi_t1[:min_h, :min_w]
    t2_cropped = ndvi_t2[:min_h, :min_w]

    diff = t2_cropped - t1_cropped
    valid_mask = np.isfinite(diff)
    valid_diff = diff[valid_mask]

    if valid_diff.size == 0:
        return {"error": "No overlapping cloud-free pixels between the two time steps in the AOI."}

    total_valid = valid_diff.size
    loss_pixels = np.sum(valid_diff < loss_threshold)
    gain_pixels = np.sum(valid_diff > gain_threshold)
    stable_pixels = total_valid - (loss_pixels + gain_pixels)

    loss_pct = round(float((loss_pixels / total_valid) * 100), 2)
    gain_pct = round(float((gain_pixels / total_valid) * 100), 2)
    stable_pct = round(float((stable_pixels / total_valid) * 100), 2)

    return {
        "diff_array": diff,
        "mean_change": round(float(np.mean(valid_diff)), 4),
        "std_change": round(float(np.std(valid_diff)), 4),
        "min_change": round(float(np.min(valid_diff)), 4),
        "max_change": round(float(np.max(valid_diff)), 4),
        "transitions": {
            "vegetation_loss_percentage": loss_pct,
            "vegetation_gain_percentage": gain_pct,
            "stable_percentage": stable_pct
        },
        "valid_pixel_count": int(total_valid)
    }


def save_change_map(
    diff: np.ndarray,
    output_path: str,
    bounds: List[float]
) -> None:
    min_x, min_y, max_x, max_y = bounds
    plt.figure(figsize=(10, 8))
    masked_diff = np.ma.masked_invalid(diff)
    plt.imshow(
        masked_diff,
        vmin=-0.5,
        vmax=0.5,
        extent=[min_x, max_x, min_y, max_y],
        origin="upper",
        interpolation="bilinear",
        cmap="coolwarm_r"
    )
    plt.colorbar(label="NDVI Difference (T2 - T1)")
    plt.title("Bi-Temporal Vegetation Change Detection Map", fontsize=14, fontweight="bold")
    plt.xlabel("Coordinate X / Longitude", fontsize=11)
    plt.ylabel("Coordinate Y / Latitude", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def run_change_detection(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    start_date_t1: str = "",
    end_date_t1: str = "",
    start_date_t2: str = "",
    end_date_t2: str = "",
    max_cloud_cover: float = 100.0,
    buffer: float = 0.005,
    aoi: Optional[Union[Dict[str, Any], List[float]]] = None
) -> Dict[str, Any]:
    """
    Execute end-to-end bi-temporal change detection between two periods.
    Supports GeoJSON polygons and bounding boxes.
    """
    target_aoi = resolve_target_aoi(latitude, longitude, aoi, buffer)

    scene_t1 = get_best_sentinel_scene(
        latitude=latitude, longitude=longitude,
        start_date=start_date_t1, end_date=end_date_t1,
        max_cloud_cover=max_cloud_cover, aoi=target_aoi
    )
    scene_t2 = get_best_sentinel_scene(
        latitude=latitude, longitude=longitude,
        start_date=start_date_t2, end_date=end_date_t2,
        max_cloud_cover=max_cloud_cover, aoi=target_aoi
    )

    if not scene_t1 or not scene_t2:
        return {
            "error": "Could not find valid satellite scenes for both comparison periods.",
            "scene_t1_found": scene_t1 is not None,
            "scene_t2_found": scene_t2 is not None
        }

    res_t1 = calculate_ndvi(
        scene_t1["B04_url"], scene_t1["B08_url"], scene_t1.get("SCL_url"),
        aoi=target_aoi, cloud_mask=True
    )
    res_t2 = calculate_ndvi(
        scene_t2["B04_url"], scene_t2["B08_url"], scene_t2.get("SCL_url"),
        aoi=target_aoi, cloud_mask=True
    )

    if "error" in res_t1:
        return {"error": f"Period 1 NDVI failed: {res_t1['error']}"}
    if "error" in res_t2:
        return {"error": f"Period 2 NDVI failed: {res_t2['error']}"}

    change_res = calculate_ndvi_change(res_t1["ndvi"], res_t2["ndvi"])
    if "error" in change_res:
        return change_res

    diff_array = change_res["diff_array"]
    map_path = MAPS_DIR / "change_detection_map.png"
    geotiff_path = MAPS_DIR / "change_detection_aoi.tif"

    bounds = res_t1.get("bounds", [0, 0, 1, 1])
    save_change_map(diff_array, str(map_path), bounds)

    if res_t1.get("transform") is not None and res_t1.get("crs") is not None:
        save_geotiff(diff_array, res_t1["transform"], res_t1["crs"], str(geotiff_path))

    return {
        "analysis": "Bi-Temporal Change Detection",
        "period_1": {
            "start": start_date_t1,
            "end": end_date_t1,
            "scene_id": scene_t1["id"],
            "datetime": scene_t1["datetime"],
            "mean_ndvi": res_t1["mean"]
        },
        "period_2": {
            "start": start_date_t2,
            "end": end_date_t2,
            "scene_id": scene_t2["id"],
            "datetime": scene_t2["datetime"],
            "mean_ndvi": res_t2["mean"]
        },
        "statistics": {
            "mean_change": change_res["mean_change"],
            "std_change": change_res["std_change"],
            "min_change": change_res["min_change"],
            "max_change": change_res["max_change"]
        },
        "transition_summary": change_res["transitions"],
        "map": "/change-map",
        "geotiff": "/change-geotiff",
        "download_geotiff": "/download/change-geotiff"
    }

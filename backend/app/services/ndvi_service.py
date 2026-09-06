import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from app.services.raster_service import read_aoi_from_cog, save_geotiff
from app.services.cloud_mask_service import create_cloud_mask


def calculate_ndvi(
    red_url: str,
    nir_url: str,
    scl_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    cloud_mask: bool = True
):
    red_result = read_aoi_from_cog(
        red_url,
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    red = red_result["data"].astype(float)

    nir_result = read_aoi_from_cog(
        nir_url,
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    nir = nir_result["data"].astype(float)

    denominator = nir + red

    ndvi = np.full_like(
        denominator,
        np.nan,
        dtype=float
    )

    valid = denominator != 0

    ndvi[valid] = (
        (nir[valid] - red[valid])
        /
        denominator[valid]
    )

    if cloud_mask:
        mask = create_cloud_mask(
            scl_url,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            target_shape=red.shape
        )
        ndvi[~mask] = np.nan

    valid_pixels = ndvi[np.isfinite(ndvi)]

    if valid_pixels.size == 0:
        return {
            "error": "No valid pixels found"
        }

    return {
        "ndvi": ndvi,
        "transform": red_result.get("transform"),
        "crs": red_result.get("crs"),
        "mean": round(
            float(np.mean(valid_pixels)),
            4
        ),
        "min": round(
            float(np.min(valid_pixels)),
            4
        ),
        "max": round(
            float(np.max(valid_pixels)),
            4
        ),
        "width": ndvi.shape[1],
        "height": ndvi.shape[0]
    }


def save_ndvi_image(
    ndvi,
    output_path,
    min_lon,
    min_lat,
    max_lon,
    max_lat
):
    plt.figure(figsize=(10, 8))

    masked_ndvi = np.ma.masked_invalid(ndvi)

    plt.imshow(
        masked_ndvi,
        vmin=-1,
        vmax=1,
        extent=[
            min_lon,
            max_lon,
            min_lat,
            max_lat
        ],
        origin="upper",
        interpolation="bilinear"
    )

    plt.colorbar(
        label="NDVI"
    )

    plt.title("NDVI Map")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


def save_ndvi_geotiff(
    ndvi: np.ndarray,
    transform,
    crs,
    output_path: str
):
    """
    Export NDVI array as a standard georeferenced GeoTIFF (.tif)
    """
    save_geotiff(
        data=ndvi,
        transform=transform,
        crs=crs,
        output_path=output_path,
        nodata=-9999.0
    )
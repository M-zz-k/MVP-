import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from app.services.raster_service import read_aoi_from_cog, save_geotiff
from app.services.cloud_mask_service import create_cloud_mask


def calculate_ndwi(
    green_url: str,
    nir_url: str,
    scl_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    cloud_mask: bool = True
):
    green_result = read_aoi_from_cog(
        green_url,
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    green = green_result["data"].astype(float)

    nir_result = read_aoi_from_cog(
        nir_url,
        min_lon,
        min_lat,
        max_lon,
        max_lat
    )

    nir = nir_result["data"].astype(float)

    denominator = green + nir

    ndwi = np.full_like(
        denominator,
        np.nan,
        dtype=float
    )

    valid = denominator != 0

    ndwi[valid] = (
        (green[valid] - nir[valid])
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
            target_shape=green.shape
        )
        ndwi[~mask] = np.nan

    valid_pixels = ndwi[np.isfinite(ndwi)]

    if valid_pixels.size == 0:
        return {
            "error": "No valid pixels found"
        }

    return {
        "ndwi": ndwi,
        "transform": green_result.get("transform"),
        "crs": green_result.get("crs"),
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
        "width": ndwi.shape[1],
        "height": ndwi.shape[0]
    }


def save_ndwi_image(
    ndwi,
    output_path,
    min_lon,
    min_lat,
    max_lon,
    max_lat
):
    plt.figure(figsize=(10, 8))

    masked_ndwi = np.ma.masked_invalid(ndwi)

    plt.imshow(
        masked_ndwi,
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
        label="NDWI"
    )

    plt.title("NDWI Map")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


def save_ndwi_geotiff(
    ndwi: np.ndarray,
    transform,
    crs,
    output_path: str
):
    """
    Export NDWI array as a standard georeferenced GeoTIFF (.tif)
    """
    save_geotiff(
        data=ndwi,
        transform=transform,
        crs=crs,
        output_path=output_path,
        nodata=-9999.0
    )
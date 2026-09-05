import numpy as np

from backend.app.services.raster_service import read_aoi_from_cog


# Sentinel-2 SCL classes to remove
INVALID_SCL_CLASSES = {
    0,   # No data
    1,   # Saturated / defective
    3,   # Cloud shadow
    8,   # Cloud medium probability
    9,   # Cloud high probability
    10,  # Thin cirrus
    11   # Snow / ice
}


def create_cloud_mask(
    scl_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    target_shape
):
    """
    Create a valid-pixel mask using Sentinel-2 SCL.

    True  = valid pixel
    False = cloud/shadow/invalid pixel
    """

    scl = read_aoi_from_cog(
        scl_url,
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        output_shape=target_shape
    )

    scl_data = scl["data"]

    valid_mask = ~np.isin(
        scl_data,
        list(INVALID_SCL_CLASSES)
    )

    return valid_mask
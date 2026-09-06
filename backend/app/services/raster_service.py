import rasterio
import numpy as np
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling

def read_aoi_from_cog(
    cog_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    output_shape=None
):
    """
    Reads only the requested AOI from a remote COG.

    Input coordinates are assumed to be longitude/latitude
    in EPSG:4326.
    """

    with rasterio.open(cog_url) as src:

        # Convert AOI from EPSG:4326 to the raster's CRS
        transformed_bounds = transform_bounds(
            "EPSG:4326",
            src.crs,
            min_lon,
            min_lat,
            max_lon,
            max_lat
        )

        # Convert geographic bounds to a pixel window
        window = from_bounds(
            *transformed_bounds,
            transform=src.transform
        )

        # Round window values to valid pixels
        window = window.round_offsets().round_lengths()
        win_transform = src.window_transform(window)

        # Read ONLY the requested window
        if output_shape:
            data = src.read(
                1,
                window=window,
                out_shape=output_shape,
                resampling=Resampling.nearest
            )
        else:
            data = src.read(
                1,
                window=window
            )

        return {
            "data": data,
            "width": data.shape[1],
            "height": data.shape[0],
            "crs": src.crs,
            "crs_str": str(src.crs),
            "transform": win_transform,
            "window": {
                "col_off": int(window.col_off),
                "row_off": int(window.row_off),
                "width": int(window.width),
                "height": int(window.height)
            }
        }


def save_geotiff(
    data: np.ndarray,
    transform,
    crs,
    output_path: str,
    nodata: float = -9999.0
):
    """
    Saves a 2D numpy array as a georeferenced GeoTIFF (.tif) file
    compatible with QGIS, ArcGIS, GDAL, and other GIS software.
    """
    export_data = np.nan_to_num(data, nan=nodata).astype(np.float32)

    with rasterio.open(
        str(output_path),
        "w",
        driver="GTiff",
        height=export_data.shape[0],
        width=export_data.shape[1],
        count=1,
        dtype=np.float32,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="deflate"
    ) as dst:
        dst.write(export_data, 1)
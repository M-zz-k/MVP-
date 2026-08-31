import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds


def read_aoi_from_cog(
    cog_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
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

        # Read ONLY the requested window
        data = src.read(
            1,
            window=window
        )

        return {
            "data": data,
            "width": data.shape[1],
            "height": data.shape[0],
            "crs": str(src.crs),

            "window": {
                "col_off": int(window.col_off),
                "row_off": int(window.row_off),
                "width": int(window.width),
                "height": int(window.height)
            }
        }
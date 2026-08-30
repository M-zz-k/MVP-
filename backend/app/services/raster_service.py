import rasterio
from rasterio.windows import from_bounds


def read_aoi_from_cog(
    cog_url: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
):
    """
    Reads only the requested geographic AOI
    from a remote Cloud Optimized GeoTIFF.
    """

    with rasterio.open(cog_url) as src:

        window = from_bounds(
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            transform=src.transform
        )

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
                "col_off": window.col_off,
                "row_off": window.row_off,
                "width": window.width,
                "height": window.height
            }
        }
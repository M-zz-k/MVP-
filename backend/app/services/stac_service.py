from pystac_client import Client
import planetary_computer


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def search_sentinel_scenes(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20
):
    """
    Search Sentinel-2 satellite imagery using Microsoft's
    Planetary Computer STAC API.
    """

    # Create a small bounding box around the location
    buffer = 0.05

    bbox = [
        longitude - buffer,  # west
        latitude - buffer,   # south
        longitude + buffer,  # east
        latitude + buffer    # north
    ]

    # Connect to STAC catalog
    catalog = Client.open(STAC_URL)

    # Search Sentinel-2 imagery
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start_date}/{end_date}",
        query={
            "eo:cloud_cover": {
                "lt": max_cloud_cover
            }
        }
    )

    # Get results
    items = list(search.items())

    # Sign Planetary Computer asset URLs
    signed_items = [planetary_computer.sign(item) for item in items]

    results = []

    for item in signed_items[:10]:

        results.append({
            "id": item.id,
            "datetime": item.datetime.isoformat(),
            "cloud_cover": item.properties.get("eo:cloud_cover"),
            "bbox": item.bbox,
            "assets": list(item.assets.keys())
        })

    return {
        "total_scenes_found": len(items),
        "scenes": results
    }
def get_best_sentinel_scene(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    max_cloud_cover: float = 20
):
    """
    Find the best Sentinel-2 scene based on lowest cloud cover.
    """

    buffer = 0.02

    bbox = [
        longitude - buffer,
        latitude - buffer,
        longitude + buffer,
        latitude + buffer
    ]

    catalog = Client.open(STAC_URL)

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start_date}/{end_date}",
        query={
            "eo:cloud_cover": {
                "lt": max_cloud_cover
            }
        }
    )

    items = list(search.items())

    if not items:
        return None

    # Sort scenes by cloud cover
    items.sort(
        key=lambda item: item.properties.get("eo:cloud_cover", 100)
    )

    # Select the least cloudy scene
    best_item = planetary_computer.sign(items[0])

    return {
        "id": best_item.id,
        "datetime": best_item.datetime.isoformat(),
        "cloud_cover": best_item.properties.get("eo:cloud_cover"),

        # These are the important URLs for NDVI
        "B04_url": best_item.assets["B04"].href,
        "B08_url": best_item.assets["B08"].href,

        "bbox": best_item.bbox
    }
from pystac_client import Client
import planetary_computer
import numpy as np
from app.services.raster_service import read_aoi_from_cog

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
    max_cloud_cover: float = 100,
    cloud_mask: bool = True,
    min_valid_fraction: float = 0.20
):
    
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

    # Best cloud-cover scenes first
    items.sort(
        key=lambda item: item.properties.get(
            "eo:cloud_cover",
            100
        )
    )

    print(f"Found {len(items)} candidate scenes")

    for index, item in enumerate(items[:10]):

        item = planetary_computer.sign(item)

        print(
            f"Trying scene {index + 1}: "
            f"{item.id} | "
            f"cloud cover = "
            f"{item.properties.get('eo:cloud_cover')}"
        )

        # Read SCL for this scene
        scl = read_aoi_from_cog(
            item.assets["SCL"].href,
            longitude - buffer,
            latitude - buffer,
            longitude + buffer,
            latitude + buffer
        )

        scl_data = scl["data"]

        # Same invalid classes used by cloud masking
        invalid_classes = {
            0,   # No data
            1,   # Saturated / defective
            3,   # Cloud shadow
            8,   # Cloud medium probability
            9,   # Cloud high probability
            10,  # Thin cirrus
            11   # Snow / ice
        }

        valid_mask = ~np.isin(
            scl_data,
            list(invalid_classes)
        )

        valid_fraction = np.mean(valid_mask)

        print(
            f"Valid pixel fraction: "
            f"{valid_fraction:.2%}"
        )

        # Accept this scene if enough valid pixels exist
        if valid_fraction >= min_valid_fraction:

            print(
                f"Selected scene: {item.id}"
            )

            return {
                "id": item.id,
                "datetime": item.datetime.isoformat(),
                "cloud_cover": item.properties.get(
                    "eo:cloud_cover"
                ),
                "valid_pixel_fraction": round(
                    float(valid_fraction),
                    4
                ),
                "B03_url": item.assets["B03"].href,
                "B04_url": item.assets["B04"].href,
                "B08_url": item.assets["B08"].href,
                "SCL_url": item.assets["SCL"].href,
                "bbox": item.bbox
            }

        print(
            "Scene rejected because too many "
            "pixels are invalid."
        )

    return None
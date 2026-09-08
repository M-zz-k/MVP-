import datetime
from typing import Optional, Union, Dict, Any, List
import shapely.geometry
from shapely.geometry import shape, box

from models.query_models import StructuredQuery, QueryPlan, BoundingBox
from services.geocoding_service import geocode_location
from services.raster_service import normalize_geometry


def plan_and_compile(
    query: StructuredQuery,
    explicit_aoi: Optional[Union[Dict[str, Any], List[float]]] = None,
    explicit_bbox: Optional[Union[List[float], BoundingBox]] = None
) -> QueryPlan:
    """
    Compile a validated StructuredQuery and optional explicit AOI geometry into an explicit QueryPlan.
    Prioritizes user-drawn GeoJSON AOI/bounding-box over text geocoding fallback.
    """
    aoi_geom = None
    bbox = None
    lat = None
    lon = None
    loc_name = "Custom AOI"
    has_polygon = False

    # Priority 1: User-provided explicit GeoJSON geometry (e.g. drawn on map)
    if explicit_aoi:
        try:
            aoi_geom = normalize_geometry(explicit_aoi)
            geom_obj = shape(aoi_geom)
            centroid = geom_obj.centroid
            lat = centroid.y
            lon = centroid.x
            min_lon, min_lat, max_lon, max_lat = geom_obj.bounds
            bbox = BoundingBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)
            has_polygon = aoi_geom.get("type") in ("Polygon", "MultiPolygon")
            loc_name = f"Custom Area ({round(lat, 4)}, {round(lon, 4)})"
        except Exception as e:
            raise ValueError(f"Invalid GeoJSON AOI geometry: {str(e)}")

    # Priority 2: Explicit bounding box
    elif explicit_bbox:
        if isinstance(explicit_bbox, (list, tuple)) and len(explicit_bbox) == 4:
            bbox = BoundingBox(
                min_lon=explicit_bbox[0],
                min_lat=explicit_bbox[1],
                max_lon=explicit_bbox[2],
                max_lat=explicit_bbox[3]
            )
        elif isinstance(explicit_bbox, BoundingBox):
            bbox = explicit_bbox
        lat = (bbox.min_lat + bbox.max_lat) / 2.0
        lon = (bbox.min_lon + bbox.max_lon) / 2.0
        loc_name = f"Bounding Box ({round(lat, 4)}, {round(lon, 4)})"

    # Priority 3: Fallback to Geocoding from location string
    elif query.location:
        geo = geocode_location(query.location)
        if not geo:
            raise ValueError(f"Could not resolve geographic coordinates for location: '{query.location}'")
        lat = geo["latitude"]
        lon = geo["longitude"]
        loc_name = geo["display_name"]
        bbox = BoundingBox(**geo["bbox"]) if geo.get("bbox") else None

    else:
        raise ValueError("Either an explicit AOI geometry/bbox or a location name is required to formulate an execution plan.")

    # Resolve date boundaries with 30-day default
    start = query.start_date
    end = query.end_date
    if not start or not end:
        end_date_obj = datetime.date.today()
        start_date_obj = end_date_obj - datetime.timedelta(days=30)
        start = start or start_date_obj.isoformat()
        end = end or end_date_obj.isoformat()

    # Determine analysis type and bands
    analysis_type = query.analysis_type or "ndvi"
    bands = list(query.bands)
    if not bands:
        if analysis_type == "ndvi":
            bands = ["B04", "B08", "SCL"]
        elif analysis_type == "ndwi":
            bands = ["B03", "B08", "SCL"]
        elif analysis_type == "ndvi-ndwi":
            bands = ["B03", "B04", "B08", "SCL"]
        elif analysis_type == "change_detection":
            bands = ["B04", "B08", "SCL"]

    cloud_max = query.cloud_cover_max if query.cloud_cover_max is not None else 20.0

    return QueryPlan(
        latitude=lat,
        longitude=lon,
        location_name=loc_name,
        bbox=bbox,
        aoi_geometry=aoi_geom,
        has_polygon_aoi=has_polygon,
        start_date=start,
        end_date=end,
        cloud_cover_max=cloud_max,
        analysis_type=analysis_type,
        dataset=query.dataset,
        bands=bands,
        aoi_required=query.aoi_required or has_polygon or (bbox is not None),
        query_type=query.query_type,
        is_temporal_comparison=query.is_temporal_comparison,
        comparison_start_date=query.comparison_start_date,
        comparison_end_date=query.comparison_end_date,
        parameters={
            "requested_index": query.requested_index,
            "has_polygon_aoi": has_polygon
        }
    )


def compile_query(query: StructuredQuery) -> QueryPlan:
    return plan_and_compile(query)

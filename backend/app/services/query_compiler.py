import datetime
from pydantic import BaseModel
from typing import Literal
from app.services.geocode_service import geocode_location
from app.services.nlp_service import StructuredQuery

class CompiledQuery(BaseModel):
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    cloud_cover_max: float
    analysis_type: str
    dataset: str
    bands: list[str]
    aoi_required: bool
    query_type: str
    location_name: str

def compile_query(query: StructuredQuery) -> CompiledQuery:
    if query.location:
        geo = geocode_location(query.location)
        if not geo:
            raise ValueError(f"Could not resolve location: {query.location}")
        lat = geo["latitude"]
        lon = geo["longitude"]
        loc_name = geo["display_name"]
    else:
        raise ValueError("Location is required for the analysis.")
        
    # Date defaults if missing
    start = query.start_date
    end = query.end_date
    if not start or not end:
        end_date_obj = datetime.date.today()
        start_date_obj = end_date_obj - datetime.timedelta(days=30)
        start = start or start_date_obj.isoformat()
        end = end or end_date_obj.isoformat()

    # Determine bands if empty based on analysis type
    bands = query.bands
    if not bands:
        if query.analysis_type == "ndvi":
            bands = ["B04", "B08"]
        elif query.analysis_type == "ndwi":
            bands = ["B03", "B08"]

    return CompiledQuery(
        latitude=lat,
        longitude=lon,
        start_date=start,
        end_date=end,
        cloud_cover_max=query.cloud_cover_max if query.cloud_cover_max is not None else 10.0,
        analysis_type=query.analysis_type or "ndvi",
        dataset=query.dataset,
        bands=bands,
        aoi_required=query.aoi_required,
        query_type=query.query_type,
        location_name=loc_name
    )

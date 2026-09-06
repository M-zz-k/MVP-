import json
import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re
from google import genai
from google.genai import types
from app.config import get_settings

class StructuredQuery(BaseModel):
    location: str | None = Field(description="The place name or location mentioned")
    start_date: str | None = Field(description="Start date in YYYY-MM-DD")
    end_date: str | None = Field(description="End date in YYYY-MM-DD")
    dataset: str = Field(default="sentinel-2-l2a", description="Dataset to use")
    cloud_cover_max: float | None = Field(description="Max cloud cover percentage, e.g. 10.0 or 20.0")
    analysis_type: Literal[
        "ndvi",
        "ndwi",
        "ndvi-ndwi",
        "weather",
        "search"
    ] | None = Field(description="Type of analysis requested")
    bands: list[str] = Field(default=[], description="Specific satellite bands to query")
    aoi_required: bool = Field(default=False, description="Whether an Area of Interest is required")
    query_type: Literal[
        "data_search",
        "analysis",
        "comparison"
    ] = Field(description="High-level category of the query")

    @field_validator('cloud_cover_max')
    def validate_cloud_cover(cls, v):
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError('Cloud cover must be between 0 and 100')
        return v

    @field_validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is not None:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v


def parse_natural_language(query: str) -> StructuredQuery:
    settings = get_settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set or is invalid.")

    client = genai.Client(api_key=settings.gemini_api_key)
    
    today_str = datetime.date.today().isoformat()
    system_instruction = f"""
    You are a geospatial AI assistant.
    Today's date is {today_str}.
    Extract the following information from the user's natural language query.
    - If the user asks for "last month", "this year", calculate the dates accordingly based on today's date.
    - Cloud cover should be a float representing percentage (e.g., 20% -> 20.0).
    - If they ask for NDVI, set analysis_type to "ndvi". If they ask for NDWI, set it to "ndwi".
    - Do NOT determine latitude/longitude, just extract the location name string.
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=StructuredQuery,
            temperature=0.0
        ),
    )
    
    # response.text should be a JSON string matching the schema
    data = json.loads(response.text)
    return StructuredQuery(**data)

def generate_explanation(query: str, analysis_result: dict) -> str:
    settings = get_settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your_api_key_here":
        return "Could not generate explanation due to missing API key."

    client = genai.Client(api_key=settings.gemini_api_key)
    
    system_instruction = """
    You are a geospatial data analyst communicating results to a user.
    You will be provided with the user's original query and the JSON results computed by our backend engine.
    Your task is to write a brief, human-friendly summary of the results.
    RULES:
    1. Base your explanation STRICTLY on the provided JSON results.
    2. DO NOT invent, hallucinate, or guess any numbers, dates, or facts.
    3. Keep it conversational but professional.
    4. Highlight the most interesting statistics (like mean, min, max).
    """

    prompt = f"User Query: {query}\n\nBackend Results: {json.dumps(analysis_result)}"

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2
        ),
    )
    
    return response.text


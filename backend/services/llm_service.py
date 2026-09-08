import json
import datetime
from google import genai
from google.genai import types
from utils.config import get_settings
from models.query_models import StructuredQuery


def parse_natural_language(query: str) -> StructuredQuery:
    """
    Extract structured parameters from a natural language query using Gemini.
    The LLM purely performs intent and entity extraction without executing geospatial logic.
    """
    settings = get_settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set or is invalid.")

    client = genai.Client(api_key=settings.gemini_api_key)

    today_str = datetime.date.today().isoformat()
    system_instruction = f"""
    You are a geospatial AI assistant that translates natural language requests into structured query parameters.
    Today's date is {today_str}.

    Extract the following intent and constraint parameters:
    1. location: The place name, city, region, or landmark mentioned (e.g. 'Bengaluru', 'San Francisco', 'Paris').
    2. start_date & end_date: ISO formatted 'YYYY-MM-DD'. Calculate relative expressions like 'last month', 'this year', 'May 2024' relative to today's date ({today_str}).
    3. dataset: Satellite dataset requested (default to 'sentinel-2-l2a').
    4. cloud_cover_max: Maximum cloud cover as a float (e.g. 'less than 20% cloud cover' -> 20.0). Default to null if unspecified.
    5. analysis_type: One of 'ndvi', 'ndwi', 'ndvi-ndwi', 'weather', 'change_detection', 'search'.
       - If the user asks for vegetation, crop health, greenness, or NDVI -> 'ndvi'.
       - If the user asks for water bodies, moisture, flood, or NDWI -> 'ndwi'.
       - If both vegetation and water are requested -> 'ndvi-ndwi'.
       - If the user asks for temperature, rainfall, precipitation, humidity, weather -> 'weather'.
       - If comparing two time periods, temporal difference, or land cover changes -> 'change_detection'.
       - If simply searching or finding satellite scenes -> 'search'.
    6. requested_index: 'NDVI', 'NDWI', etc. if explicitly requested.
    7. is_temporal_comparison: Set to true if comparing two dates/periods.
    8. comparison_start_date & comparison_end_date: Secondary date range for comparison if present.
    9. aoi_required: True if focused on a specific local bounding box/area of interest.
    10. query_type: 'data_search', 'analysis', or 'comparison'.

    DO NOT compute latitude or longitude coordinates. Only extract the location string.
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

    data = json.loads(response.text)
    return StructuredQuery.model_validate(data)


def generate_explanation(query: str, analysis_result: dict) -> str:
    """
    Generate a human-friendly narrative summary of computed geospatial analysis results.
    """
    settings = get_settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your_api_key_here":
        return "Analysis completed successfully. (LLM explanation omitted - API key not set)."

    client = genai.Client(api_key=settings.gemini_api_key)

    system_instruction = """
    You are an expert geospatial data analyst communicating insights to end users.
    You are given the user's original natural language query and the verified JSON analysis results calculated by the execution engine.
    
    Guidelines:
    1. Base all statements strictly on the numeric and factual results provided.
    2. Do NOT invent or hallucinate metrics, satellite names, or dates.
    3. Clearly explain what the index values (NDVI / NDWI) or weather trends signify in practical terms:
       - NDVI: values > 0.4 indicate dense healthy vegetation, 0.2-0.4 moderate vegetation, < 0.1 barren/built-up/water.
       - NDWI: positive values indicate open water bodies, negative values indicate non-water surfaces.
    4. Keep the summary concise, professional, and actionable (2-4 sentences).
    """

    prompt = f"User Query: {query}\n\nBackend Results: {json.dumps(analysis_result)}"

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            ),
        )
        return response.text
    except Exception as e:
        return f"Analysis completed successfully. Summary: {str(analysis_result.get('index', 'Execution'))} processing finished."

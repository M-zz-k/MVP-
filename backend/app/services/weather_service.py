import requests

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


SUPPORTED_DAILY_VARIABLES = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "apparent_temperature_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "cloud_cover_mean",
    "dew_point_2m_mean",
    "relative_humidity_2m_mean",
    "pressure_msl_mean",
    "surface_pressure_mean"
]


SUPPORTED_HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "snowfall",
    "weather_code",
    "pressure_msl",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m"
]


def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_variables=None,
    hourly_variables=None
):
    """
    Fetch historical weather data.

    Supports:
    - Daily weather data
    - Hourly weather data
    - Date and time information
    """

    # Default daily variables
    if daily_variables is None:
        daily_variables = [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "relative_humidity_2m_mean",
            "wind_speed_10m_max",
            "cloud_cover_mean"
        ]

    # Default hourly variables
    if hourly_variables is None:
        hourly_variables = [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "cloud_cover"
        ]

    # Check daily variables
    invalid_daily = [
        variable
        for variable in daily_variables
        if variable not in SUPPORTED_DAILY_VARIABLES
    ]

    if invalid_daily:
        raise ValueError(
            f"Unsupported daily variables: {invalid_daily}"
        )

    # Check hourly variables
    invalid_hourly = [
        variable
        for variable in hourly_variables
        if variable not in SUPPORTED_HOURLY_VARIABLES
    ]

    if invalid_hourly:
        raise ValueError(
            f"Unsupported hourly variables: {invalid_hourly}"
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,

        "daily": ",".join(daily_variables),
        "hourly": ",".join(hourly_variables),

        "timezone": "auto"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
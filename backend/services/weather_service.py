import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Optional
from utils.config import GRAPHS_DIR

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

SUPPORTED_DAILY_VARIABLES = [
    "weather_code", "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "apparent_temperature_max", "apparent_temperature_min", "apparent_temperature_mean",
    "precipitation_sum", "rain_sum", "snowfall_sum", "precipitation_hours",
    "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant",
    "shortwave_radiation_sum", "et0_fao_evapotranspiration", "sunrise", "sunset",
    "daylight_duration", "sunshine_duration", "cloud_cover_mean", "dew_point_2m_mean",
    "relative_humidity_2m_mean", "pressure_msl_mean", "surface_pressure_mean"
]

SUPPORTED_HOURLY_VARIABLES = [
    "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
    "precipitation", "rain", "snowfall", "weather_code", "pressure_msl",
    "surface_pressure", "cloud_cover", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"
]

VARIABLE_INFO = {
    "temperature_2m_mean": {"label": "Mean Temperature", "unit": "°C"},
    "temperature_2m_max": {"label": "Maximum Temperature", "unit": "°C"},
    "temperature_2m_min": {"label": "Minimum Temperature", "unit": "°C"},
    "precipitation_sum": {"label": "Precipitation", "unit": "mm"},
    "rain_sum": {"label": "Rainfall", "unit": "mm"},
    "relative_humidity_2m_mean": {"label": "Relative Humidity", "unit": "%"},
    "wind_speed_10m_max": {"label": "Maximum Wind Speed", "unit": "km/h"},
    "cloud_cover_mean": {"label": "Cloud Cover", "unit": "%"},
    "pressure_msl_mean": {"label": "Mean Sea Level Pressure", "unit": "hPa"},
    "surface_pressure_mean": {"label": "Surface Pressure", "unit": "hPa"},
    "temperature_2m": {"label": "Temperature", "unit": "°C"},
    "relative_humidity_2m": {"label": "Relative Humidity", "unit": "%"},
    "precipitation": {"label": "Precipitation", "unit": "mm"},
    "wind_speed_10m": {"label": "Wind Speed", "unit": "km/h"},
    "cloud_cover": {"label": "Cloud Cover", "unit": "%"}
}


def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_variables: Optional[List[str]] = None,
    hourly_variables: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch historical weather records for the specified location and time window via Open-Meteo.
    """
    if daily_variables is None:
        daily_variables = [
            "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
            "precipitation_sum", "relative_humidity_2m_mean", "wind_speed_10m_max",
            "cloud_cover_mean"
        ]
    if hourly_variables is None:
        hourly_variables = [
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "wind_speed_10m", "cloud_cover"
        ]

    invalid_daily = [v for v in daily_variables if v not in SUPPORTED_DAILY_VARIABLES]
    if invalid_daily:
        raise ValueError(f"Unsupported daily variables: {invalid_daily}")

    invalid_hourly = [v for v in hourly_variables if v not in SUPPORTED_HOURLY_VARIABLES]
    if invalid_hourly:
        raise ValueError(f"Unsupported hourly variables: {invalid_hourly}")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(daily_variables),
        "hourly": ",".join(hourly_variables),
        "timezone": "auto"
    }

    response = requests.get(WEATHER_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def analyze_weather_trend(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform day-over-day and cumulative trend analysis on weather measurements.
    """
    daily = weather_data.get("daily")
    if not daily:
        return {"error": "No daily weather data available"}

    dates = daily.get("time", [])
    if len(dates) < 2:
        return {"error": "At least two days of data are required"}

    analysis = []
    variables = {
        "temperature_2m_mean": "Temperature",
        "precipitation_sum": "Rainfall",
        "relative_humidity_2m_mean": "Humidity",
        "wind_speed_10m_max": "Wind Speed",
        "cloud_cover_mean": "Cloud Cover"
    }

    for variable, name in variables.items():
        values = daily.get(variable)
        if not values:
            continue

        changes = []
        for i in range(1, len(values)):
            previous = values[i - 1]
            current = values[i]
            if previous is None or current is None:
                continue

            change = current - previous
            direction = "increased" if change > 0 else ("decreased" if change < 0 else "remained stable")

            changes.append({
                "from_date": dates[i - 1],
                "to_date": dates[i],
                "previous_value": previous,
                "current_value": current,
                "change": round(change, 2),
                "direction": direction
            })

        analysis.append({"variable": name, "changes": changes})

    return {"dates": dates, "analysis": analysis}


def save_weather_graphs(
    weather_data: Dict[str, Any],
    variables: List[str],
    output_dir=GRAPHS_DIR,
    mode: str = "separate"
) -> Dict[str, Any]:
    """
    Generate and save high-resolution weather timeseries graphs.
    """
    daily = weather_data.get("daily", {})
    hourly = weather_data.get("hourly", {})

    valid_variables = []
    for var in variables:
        if var in daily:
            valid_variables.append({
                "variable": var, "x": daily.get("time", []), "y": daily.get(var, []), "frequency": "daily"
            })
        elif var in hourly:
            valid_variables.append({
                "variable": var, "x": hourly.get("time", []), "y": hourly.get(var, []), "frequency": "hourly"
            })

    if not valid_variables:
        return {"error": "None of the requested variables are available"}

    if mode == "separate":
        graphs = []
        for item in valid_variables:
            var = item["variable"]
            info = VARIABLE_INFO.get(var, {"label": var.replace("_", " ").title(), "unit": ""})

            plt.figure(figsize=(10, 6))
            plt.plot(item["x"], item["y"], marker="o", color="#2563EB", linewidth=2)
            plt.title(f"{info['label']} Over Time", fontsize=14, fontweight="bold")
            plt.xlabel("Date / Time", fontsize=11)
            plt.ylabel(f"{info['label']} ({info['unit']})" if info["unit"] else info["label"], fontsize=11)
            plt.xticks(rotation=45, ha="right")
            plt.grid(True, linestyle="--", alpha=0.6)
            plt.tight_layout()

            output_path = output_dir / f"{var}.png"
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            graphs.append({
                "variable": var,
                "label": info["label"],
                "unit": info["unit"],
                "url": f"/weather-graph/{var}"
            })
        return {"mode": "separate", "graphs": graphs}

    elif mode == "combined":
        frequencies = {item["frequency"] for item in valid_variables}
        if len(frequencies) > 1:
            return {"error": "Combined graph requires all variables to have the same frequency"}

        plt.figure(figsize=(12, 7))
        for item in valid_variables:
            var = item["variable"]
            info = VARIABLE_INFO.get(var, {"label": var.replace("_", " ").title(), "unit": ""})
            label = f"{info['label']} ({info['unit']})" if info["unit"] else info["label"]
            plt.plot(item["x"], item["y"], marker="o", linewidth=2, label=label)

        plt.title("Weather Variables Over Time", fontsize=14, fontweight="bold")
        plt.xlabel("Date / Time", fontsize=11)
        plt.ylabel("Value", fontsize=11)
        plt.xticks(rotation=45, ha="right")
        plt.legend(loc="upper right")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        output_path = output_dir / "combined_weather_graph.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        return {"mode": "combined", "graphs": [{"url": "/weather-graph/combined"}]}

    return {"error": "Invalid graph mode. Use 'separate' or 'combined'."}


def run_weather_analysis(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_variables: Optional[str] = None,
    hourly_variables: Optional[str] = None,
    analysis: bool = False,
    graph_variables: Optional[str] = None,
    graph_mode: str = "separate"
) -> Dict[str, Any]:
    daily_vars = [v.strip() for v in daily_variables.split(",")] if daily_variables else None
    hourly_vars = [v.strip() for v in hourly_variables.split(",")] if hourly_variables else None

    weather_data = get_historical_weather(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        daily_variables=daily_vars,
        hourly_variables=hourly_vars
    )

    response = {
        "location": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start_date, "end": end_date},
        "weather": weather_data
    }

    if analysis:
        response["trend_analysis"] = analyze_weather_trend(weather_data)

    if graph_variables:
        variables = [v.strip() for v in graph_variables.split(",")]
        response["graphs"] = save_weather_graphs(weather_data, variables, GRAPHS_DIR, graph_mode)

    return response

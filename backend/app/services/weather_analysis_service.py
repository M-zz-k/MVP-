def analyze_weather_trend(weather_data):
    """
    Analyze day-to-day changes in historical weather data.
    """

    daily = weather_data.get("daily")

    if not daily:
        return {
            "error": "No daily weather data available"
        }

    dates = daily.get("time", [])

    if len(dates) < 2:
        return {
            "error": "At least two days of data are required"
        }

    analysis = []

    # Variables we want to analyze
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

            if change > 0:
                direction = "increased"
            elif change < 0:
                direction = "decreased"
            else:
                direction = "remained stable"

            changes.append({
                "from_date": dates[i - 1],
                "to_date": dates[i],
                "previous_value": previous,
                "current_value": current,
                "change": round(change, 2),
                "direction": direction
            })

        analysis.append({
            "variable": name,
            "changes": changes
        })

    return {
        "dates": dates,
        "analysis": analysis
    }
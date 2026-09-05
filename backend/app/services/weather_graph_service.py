import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


VARIABLE_INFO = {
    "temperature_2m_mean": {
        "label": "Temperature",
        "unit": "°C"
    },
    "temperature_2m_max": {
        "label": "Maximum Temperature",
        "unit": "°C"
    },
    "temperature_2m_min": {
        "label": "Minimum Temperature",
        "unit": "°C"
    },
    "precipitation_sum": {
        "label": "Precipitation",
        "unit": "mm"
    },
    "rain_sum": {
        "label": "Rainfall",
        "unit": "mm"
    },
    "relative_humidity_2m_mean": {
        "label": "Relative Humidity",
        "unit": "%"
    },
    "wind_speed_10m_max": {
        "label": "Maximum Wind Speed",
        "unit": "km/h"
    },
    "cloud_cover_mean": {
        "label": "Cloud Cover",
        "unit": "%"
    },
    "pressure_msl_mean": {
        "label": "Mean Sea Level Pressure",
        "unit": "hPa"
    },
    "surface_pressure_mean": {
        "label": "Surface Pressure",
        "unit": "hPa"
    },
    "temperature_2m": {
        "label": "Temperature",
        "unit": "°C"
    },
    "relative_humidity_2m": {
        "label": "Relative Humidity",
        "unit": "%"
    },
    "precipitation": {
        "label": "Precipitation",
        "unit": "mm"
    },
    "wind_speed_10m": {
        "label": "Wind Speed",
        "unit": "km/h"
    },
    "cloud_cover": {
        "label": "Cloud Cover",
        "unit": "%"
    }
}


def get_variable_data(weather_data, variable):

    daily = weather_data.get("daily", {})
    hourly = weather_data.get("hourly", {})

    if variable in daily:
        return (
            daily.get("time", []),
            daily.get(variable, []),
            "daily"
        )

    if variable in hourly:
        return (
            hourly.get("time", []),
            hourly.get(variable, []),
            "hourly"
        )

    return None, None, None


def save_weather_graphs(
    weather_data,
    variables,
    output_dir,
    mode="separate"
):

    valid_variables = []

    for variable in variables:

        x_values, y_values, frequency = get_variable_data(
            weather_data,
            variable
        )

        if x_values and y_values:
            valid_variables.append({
                "variable": variable,
                "x": x_values,
                "y": y_values,
                "frequency": frequency
            })

    if not valid_variables:
        return {
            "error": "None of the requested variables are available"
        }

    # ------------------------------------------------
    # SEPARATE GRAPHS
    # ------------------------------------------------

    if mode == "separate":

        graphs = []

        for item in valid_variables:

            variable = item["variable"]
            x_values = item["x"]
            y_values = item["y"]

            info = VARIABLE_INFO.get(
                variable,
                {
                    "label": variable.replace("_", " ").title(),
                    "unit": ""
                }
            )

            plt.figure(figsize=(10, 6))

            plt.plot(
                x_values,
                y_values,
                marker="o"
            )

            plt.title(
                f"{info['label']} Over Time"
            )

            plt.xlabel("Date / Time")

            if info["unit"]:
                plt.ylabel(
                    f"{info['label']} ({info['unit']})"
                )
            else:
                plt.ylabel(info["label"])

            plt.xticks(
                rotation=45,
                ha="right"
            )

            plt.grid(True)

            plt.tight_layout()

            filename = f"{variable}.png"

            output_path = output_dir / filename

            plt.savefig(
                output_path,
                dpi=300,
                bbox_inches="tight"
            )

            plt.close()

            graphs.append({
                "variable": variable,
                "label": info["label"],
                "unit": info["unit"],
                "url": f"/weather-graph/{variable}"
            })

        return {
            "mode": "separate",
            "graphs": graphs
        }

    # ------------------------------------------------
    # COMBINED GRAPH
    # ------------------------------------------------

    elif mode == "combined":

        frequencies = set(
            item["frequency"]
            for item in valid_variables
        )

        if len(frequencies) > 1:

            return {
                "error": (
                    "Combined graph requires all variables "
                    "to have the same frequency "
                    "(daily or hourly)"
                )
            }

        plt.figure(figsize=(12, 7))

        for item in valid_variables:

            variable = item["variable"]

            info = VARIABLE_INFO.get(
                variable,
                {
                    "label": variable.replace("_", " ").title(),
                    "unit": ""
                }
            )

            label = info["label"]

            if info["unit"]:
                label = f"{label} ({info['unit']})"

            plt.plot(
                item["x"],
                item["y"],
                marker="o",
                label=label
            )

        plt.title("Weather Variables Over Time")

        plt.xlabel("Date / Time")

        plt.ylabel("Value")

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.legend()

        plt.grid(True)

        plt.tight_layout()

        output_path = output_dir / "combined_weather_graph.png"

        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

        return {
            "mode": "combined",
            "graphs": [
                {
                    "url": "/weather-graph/combined"
                }
            ]
        }

    else:

        return {
            "error": "Invalid graph mode. Use 'separate' or 'combined'."
        }
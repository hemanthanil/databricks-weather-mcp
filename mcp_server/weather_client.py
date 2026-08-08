import requests
from datetime import date


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherAPIError(Exception):
    """Raised when weather data cannot be retrieved."""


def resolve_location(location: str) -> dict:
    """
    Resolve a city or postal code into coordinates.

    Args:
        location: City name or postal code, e.g. "Vancouver" or "Chicago".

    Returns:
        Dict containing location name, latitude, longitude, country,
        timezone, and administrative region.
    """

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        results = data.get("results")

        if not results:
            raise WeatherAPIError(
                f"Could not find location: {location}"
            )

        result = results[0]

        return {
            "name": result.get("name"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
            "country": result.get("country"),
            "region": result.get("admin1"),
            "timezone": result.get("timezone"),
        }

    except requests.RequestException as exc:
        raise WeatherAPIError(
            f"Location service unavailable: {exc}"
        ) from exc

def weather_code_to_description(code: int) -> str:
    """Convert an Open-Meteo WMO weather code to readable text."""
    return WEATHER_CODES.get(code, "Unknown conditions")

def get_current_weather(location: str) -> dict:
    """
    Get current weather conditions for a location.

    Args:
        location: City name or postal code.

    Returns:
        Current temperature, humidity, apparent temperature,
        precipitation, weather code, and wind speed.
    """

    place = resolve_location(location)

    try:
        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        weather_code = current.get("weather_code")

        return {
            "location": place,
            "temperature_c": current.get("temperature_2m"),
            "apparent_temperature_c": current.get(
                "apparent_temperature"
            ),
            "humidity_percent": current.get(
                "relative_humidity_2m"
            ),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "weather_code": weather_code,
            "conditions": weather_code_to_description(weather_code),
            "observed_at": current.get("time"),
        }

    except requests.RequestException as exc:
        raise WeatherAPIError(
            f"Weather service unavailable: {exc}"
        ) from exc


def get_forecast(location: str, days: int = 7) -> dict:
    """
    Get a daily weather forecast.

    Args:
        location: City name or postal code.
        days: Number of forecast days from 1 to 16.

    Returns:
        Dict containing location information and daily forecasts.
    """

    if days < 1 or days > 16:
        raise ValueError("days must be between 1 and 16")

    place = resolve_location(location)

    try:
        response = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max,"
                    "precipitation_sum,"
                    "wind_speed_10m_max"
                ),
                "forecast_days": days,
                "timezone": "auto",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})

        forecasts = []

        dates = daily.get("time", [])

        for i, forecast_date in enumerate(dates):
            forecasts.append(
                {
                    "date": forecast_date,
                    "temperature_high_c":
                        daily["temperature_2m_max"][i],
                    "temperature_low_c":
                        daily["temperature_2m_min"][i],
                    "precipitation_probability_percent":
                        daily["precipitation_probability_max"][i],
                    "precipitation_mm":
                        daily["precipitation_sum"][i],
                    "wind_speed_max_kmh":
                        daily["wind_speed_10m_max"][i],
                    "weather_code":
                        daily["weather_code"][i],
                    "conditions":
                        weather_code_to_description(
                            daily["weather_code"][i]
                        ),
                }
            )

        return {
            "location": place,
            "forecast": forecasts,
        }

    except requests.RequestException as exc:
        raise WeatherAPIError(
            f"Forecast service unavailable: {exc}"
        ) from exc


def get_travel_recommendation(
    location: str,
    target_date: str,
) -> dict:
    """
    Generate simple weather-based travel recommendations.

    Rules:
    - Umbrella recommended when precipitation probability >= 40%.
    - Jacket recommended when daily low <= 12 C.
    - Heat caution when daily high >= 30 C.
    - Wind caution when maximum wind >= 40 km/h.

    Args:
        location: City name or postal code.
        target_date: Forecast date in YYYY-MM-DD format.

    Returns:
        Forecast plus recommendation flags and explanation.
    """

    forecast_data = get_forecast(location, days=16)

    matching_day = next(
        (
            day
            for day in forecast_data["forecast"]
            if day["date"] == target_date
        ),
        None,
    )

    if not matching_day:
        raise WeatherAPIError(
            f"No forecast available for {target_date}. "
            "Open-Meteo forecasts are limited to the available "
            "forecast window."
        )

    rain_probability = (
        matching_day["precipitation_probability_percent"] or 0
    )

    high = matching_day["temperature_high_c"]
    low = matching_day["temperature_low_c"]
    wind = matching_day["wind_speed_max_kmh"]

    umbrella = rain_probability >= 40
    jacket = low is not None and low <= 15
    heat_caution = high is not None and high >= 30
    wind_caution = wind is not None and wind >= 40

    recommendations = []

    if umbrella:
        recommendations.append(
            f"Bring an umbrella: precipitation probability is "
            f"{rain_probability}%."
        )

    if jacket:
        recommendations.append(
            f"Bring a jacket: temperature may fall to {low}°C."
        )

    if heat_caution:
        recommendations.append(
            f"Prepare for hot weather: the high is {high}°C."
        )

    if wind_caution:
        recommendations.append(
            f"Expect strong wind: speeds may reach {wind} km/h."
        )

    if not recommendations:
        recommendations.append(
            "No major weather precautions are indicated by the "
            "current forecast."
        )

    return {
        "location": forecast_data["location"],
        "date": target_date,
        "forecast": matching_day,
        "umbrella_recommended": umbrella,
        "jacket_recommended": jacket,
        "heat_caution": heat_caution,
        "wind_caution": wind_caution,
        "recommendations": recommendations,
    }

def compare_weather(locations: list[str], days: int = 3) -> dict:
    """
    Compare forecasts across multiple locations.

    Args:
        locations: List of city names or postal codes.
        days: Number of forecast days to compare.

    Returns:
        Forecast summaries for each location.
    """

    if len(locations) < 2:
        raise WeatherAPIError(
            "At least two locations are required for comparison."
        )

    if len(locations) > 5:
        raise WeatherAPIError(
            "A maximum of five locations can be compared."
        )

    results = []

    for location in locations:
        forecast = get_forecast(location, days)

        results.append({
            "location": forecast["location"],
            "forecast": forecast["forecast"],
        })

    return {
        "days": days,
        "locations_compared": len(results),
        "results": results,
    }

def get_historical_weather(
    location: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Get historical daily weather for a location.

    Args:
        location: City name or postal code.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Historical daily weather including high/low temperature,
        precipitation, wind speed, weather code, and readable conditions.
    """

    place = resolve_location(location)

    try:
        response = requests.get(
            HISTORICAL_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "start_date": start_date,
                "end_date": end_date,
                "daily": (
                    "weather_code,"
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_sum,"
                    "wind_speed_10m_max"
                ),
                "timezone": "auto",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])

        history = []

        for i, historical_date in enumerate(dates):
            weather_code = daily["weather_code"][i]

            history.append(
                {
                    "date": historical_date,
                    "temperature_high_c":
                        daily["temperature_2m_max"][i],
                    "temperature_low_c":
                        daily["temperature_2m_min"][i],
                    "precipitation_mm":
                        daily["precipitation_sum"][i],
                    "wind_speed_max_kmh":
                        daily["wind_speed_10m_max"][i],
                    "weather_code": weather_code,
                    "conditions":
                        weather_code_to_description(weather_code),
                }
            )

        return {
            "location": place,
            "start_date": start_date,
            "end_date": end_date,
            "history": history,
        }

    except requests.RequestException as exc:
        raise WeatherAPIError(
            f"Historical weather service unavailable: {exc}"
        ) from exc
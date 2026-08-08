import os

from fastmcp import FastMCP

import weather_client


mcp = FastMCP("weather-intelligence")


@mcp.tool
def get_current_weather(location: str) -> dict:
    """
    Get the current weather conditions for a location.

    Args:
        location: City name or postal code, for example
                  "Vancouver", "Chicago", or "V6B 1A1".

    Returns:
        A dictionary containing temperature, apparent temperature,
        humidity, precipitation, wind speed, and weather code.

        If the location cannot be resolved or the weather service
        fails, returns a dictionary containing an error.
    """

    try:
        return weather_client.get_current_weather(location)

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@mcp.tool
def get_forecast(location: str, days: int = 7) -> dict:
    """
    Get the daily weather forecast for a location.

    Args:
        location: City name or postal code.
        days: Number of forecast days. Must be between 1 and 16.

    Returns:
        A dictionary containing daily high/low temperatures,
        precipitation probability, precipitation amount,
        wind speed, and weather code.

        If the request fails, returns a clean error dictionary.
    """

    try:
        return weather_client.get_forecast(
            location=location,
            days=days,
        )

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@mcp.tool
def get_travel_recommendation(
    location: str,
    target_date: str,
) -> dict:
    """
    Make a simple weather-based travel recommendation.

    The recommendation applies deterministic rules to the
    weather forecast:

    - Recommend an umbrella when precipitation probability
      is at least 40%.
    - Recommend a jacket when the forecast low is 12 C or colder.
    - Add a heat warning when the forecast high is 30 C or hotter.
    - Add a wind warning when maximum wind reaches 40 km/h.

    Args:
        location: City name or postal code.
        target_date: Date in YYYY-MM-DD format.

    Returns:
        The forecast for the requested date together with
        recommendation flags and explanations.

        If the date or location cannot be resolved, returns
        a clean error dictionary.
    """

    try:
        return weather_client.get_travel_recommendation(
            location=location,
            target_date=target_date,
        )

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }

@mcp.tool
def compare_weather(
    locations: list[str],
    days: int = 3,
) -> dict:
    """
    Compare weather forecasts across multiple cities.

    Args:
        locations: Two to five city names or postal codes.
        days: Number of days to compare.

    Returns:
        Forecast information for each requested location.
    """

    try:
        return weather_client.compare_weather(
            locations=locations,
            days=days,
        )

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }

@mcp.tool
def get_historical_weather(
    location: str,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Get historical weather for a location and date range.

    Args:
        location: City name or postal code.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        Historical daily high/low temperatures, precipitation,
        wind speed, weather code, and readable conditions.

        If the request fails, returns a clean error dictionary.
    """

    try:
        return weather_client.get_historical_weather(
            location=location,
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


if __name__ == "__main__":
    port = int(
        os.getenv(
            "DATABRICKS_APP_PORT",
            os.getenv("PORT", 8000),
        )
    )

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )
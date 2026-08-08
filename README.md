# databricks-weather-mcp
# Weather Prediction MCP Server + Databricks Agent

This project was built for Day 3 homework using the `databricks-lakebase-app-day-3` repository as a reference pattern.

The goal was to build a weather-focused MCP server, deploy it as a Databricks App, and connect it to a Databricks Agent so the agent can answer current weather, forecast, historical weather, and recommendation questions through tool calls.

## Architecture

```text
User
  ↓
Databricks Agent / Playground
  ↓
MCP Tool
  ↓
Databricks App
  ↓
weather_mcp_server.py
  ↓
weather_client.py
  ↓
Open-Meteo API
```

All HTTP requests, location resolution, response parsing, and weather logic are handled inside `weather_client.py`.

## Weather API

This project uses **Open-Meteo**.

Reasons for choosing Open-Meteo:

* No API key required
* No credit card required
* Free for development/non-commercial use
* Supports current weather and multi-day forecasts
* Provides a geocoding API for resolving city names
* Provides historical weather data
* Avoids storing or managing API secrets for this project

Because Open-Meteo does not require authentication, no API keys or secrets are committed to this repository.

## Project Structure

```text
.
├── mcp_server/
│   ├── weather_client.py
│   ├── weather_mcp_server.py
│   ├── requirements.txt
│   └── app.yaml
│
├── agent/
│   └── system_prompt.md
│
├── screenshots/
│   └── ...
│
└── README.md
```

## MCP Tools

### `get_current_weather(location)`

Returns current weather conditions for a city or postal code.

Includes:

* Temperature
* Apparent temperature
* Humidity
* Precipitation
* Wind speed
* WMO weather code
* Human-readable conditions

Example:

```text
What's the weather in Vancouver right now?
```

---

### `get_forecast(location, days)`

Returns a multi-day daily forecast.

Includes:

* Daily high temperature
* Daily low temperature
* Precipitation probability
* Precipitation amount
* Maximum wind speed
* Weather code
* Human-readable conditions

Example:

```text
What is the weather forecast in Vancouver for the next 3 days?
```

---

### `get_travel_recommendation(location, target_date)`

Applies simple deterministic rules to the forecast and returns weather-related travel recommendations.

Rules currently used:

* Recommend an umbrella if precipitation probability is at least 40%
* Recommend a jacket if the forecast low is 15°C or colder
* Add a heat caution if the forecast high is at least 30°C
* Add a wind caution if maximum wind speed is at least 40 km/h

This tool demonstrates derived reasoning rather than simply returning raw API data.

Example:

```text
I'm going to Seattle on August 10, 2026.
Should I bring an umbrella or jacket?
```

---

### `compare_weather(locations, days)`

Compares the weather forecast across multiple cities.

The tool accepts between two and five locations and returns the forecast for each location so the agent can compare conditions.

Example:

```text
Compare the weather in Vancouver, Seattle, and Calgary
for the next 3 days. Which city has the best weather
for an outdoor trip?
```

---

### `get_historical_weather(location, start_date, end_date)`

Returns historical weather data for a location and date range using Open-Meteo's Historical Weather API.

Includes:

* Daily high and low temperatures
* Precipitation
* Maximum wind speed
* Weather code
* Human-readable conditions

Example:

```text
What was the weather like in Vancouver
from August 1 to August 3, 2025?
```

## MCP Server Design

The MCP server is built with **FastMCP**.

Tool functions are exposed using:

```python
@mcp.tool
```

The MCP functions contain only the tool interface and error handling.

For example:

```python
@mcp.tool
def get_current_weather(location: str) -> dict:
    try:
        return weather_client.get_current_weather(location)
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
```

All external API calls are kept in `weather_client.py`.

This follows the same separation-of-responsibility pattern used in the Day 3 Alpaca example:

```text
MCP Tool
   ↓
Adapter / Client
   ↓
External API
```

## Error Handling

Invalid locations and API failures return clean error responses instead of Python stack traces.

Example:

```json
{
  "status": "error",
  "message": "Could not find location: invalid-location"
}
```

The agent is instructed to explain tool failures and ask the user to clarify the location rather than guessing weather information.

## Agent System Prompt

The Databricks agent is configured with weather-specific tool-selection rules and guardrails.

Key rules include:

```text
You are a weather intelligence assistant.

Always use the available weather tools before answering weather
questions. Never invent current, forecast, or historical weather data.

Tool selection:

- Use get_current_weather for current conditions.
- Use get_forecast for future weather and multi-day forecasts.
- Use get_travel_recommendation for umbrella, jacket, heat,
  wind, or travel-preparation questions.
- Use compare_weather when comparing multiple locations.
- Use get_historical_weather for dates in the past.

Guardrails:

- If a location cannot be resolved, ask the user to clarify.
- If a tool returns an error, explain the failure rather than guessing.
- Base weather descriptions only on values returned by tools.
- Clearly distinguish forecast information from certainty.
- Do not invent weather classifications not returned by the tools.
```

The system prompt is stored in:

```text
agent/system_prompt.md
```

## Running the MCP Server

Install dependencies:

```bash
pip install -r requirements.txt
```

The MCP server starts using:

```bash
python weather_mcp_server.py
```

The Databricks App uses `app.yaml` to launch the MCP server.

## Databricks Deployment

The `mcp_server` directory is deployed as its own Databricks App.

High-level deployment flow:

```text
Git repository
   ↓
Databricks App
   ↓
MCP server
   ↓
Register as external MCP
   ↓
Databricks Playground / Agent
```

After deployment:

1. Deploy the `mcp_server` folder as a Databricks App.
2. Verify that the application is running successfully.
3. Register the deployed application as an external MCP.
4. Add the MCP tools to the Databricks agent.
5. Add the system prompt and guardrails.
6. Test tool calls in Playground.

## Demonstration

The agent was tested with multiple natural-language questions.

### Current Weather

```text
What's the weather in Vancouver right now?
```

Tool used:

```text
get_current_weather
```

### Multi-Day Forecast

```text
What is the weather forecast in Vancouver for the next 3 days?
```

Tool used:

```text
get_forecast
```

### Travel Recommendation

```text
I'm going to Seattle on August 10, 2026.
Should I bring an umbrella or jacket?
```

Tools used:

```text
get_forecast
get_travel_recommendation
```

### Multi-City Comparison — Stretch

```text
Compare the weather in Vancouver, Seattle, and Calgary
for the next 3 days. Which city has the best weather
for an outdoor trip?
```

Tool used:

```text
compare_weather
```

### Historical Weather — Stretch

```text
What was the weather like in Vancouver
from August 1 to August 3, 2025?
```

Tool used:

```text
get_historical_weather
```

## Requirements

Main Python dependencies:

```text
fastmcp
requests
```

See:

```text
mcp_server/requirements.txt
```

## Security

No API keys are hardcoded or committed to the repository.

Open-Meteo does not require authentication for this implementation, so Databricks Secrets are not required.

If a future weather provider requiring authentication is added, credentials should be stored using Databricks Secrets rather than environment values committed to source control.

## What I Learned

This project demonstrates how an MCP server can act as a controlled tool layer between an AI agent and an external API.

The main design principles used were:

* Separate the MCP interface from API integration logic
* Keep MCP tools small and focused
* Return structured data rather than free-form text
* Add deterministic logic for recommendations
* Use agent guardrails to reduce hallucination
* Return clean errors instead of application stack traces
* Allow the agent to decide which specialized tool should be used for a user's natural-language request


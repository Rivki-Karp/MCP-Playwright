import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Loading .env file explicitly to ensure variables are available
load_dotenv()

mcp = FastMCP("weather-USA")

# Fallback values if environment variables are missing
NWS_API_BASE = os.getenv("NWS_API_BASE", "https://api.weather.gov")
USER_AGENT = os.getenv("USER_AGENT", "WeatherAssistant/1.0")

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling and Netfree support."""
    headers = {
        "User-Agent": USER_AGENT, 
        "Accept": "application/geo+json"
    }
    
    # Configuration for Netfree and proxy environments
    transport = httpx.AsyncHTTPTransport(verify=False)
    
    async with httpx.AsyncClient(transport=transport) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            # Log the status for debugging
            if response.status_code != 200:
                return {"error": f"API returned status {response.status_code}", "detail": response.text}
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc","Unknown")}
Severity: {props.get("severity","Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instructions", "No specific instructions provided")}
"""

@mcp.tool()
async def get_alerts_in_USA(state: str) -> str:
    """Get weather alerts for a USA state (e.g. NY, CA)."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    
    if not data or "features" not in data:
        error_msg = data.get("error") if data else "Unknown error"
        return f"Unable to fetch alerts: {error_msg}"
    
    if not data["features"]:
        return f"No active alerts for {state}."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast_in_USA(latitude: float, longitude: float) -> str:
    """Get a detailed 7-day weather forecast for a USA location."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    
    if not points_data or "properties" not in points_data:
        error_msg = points_data.get("error") if points_data else "Unknown error"
        return f"Error fetching location metadata: {error_msg}"
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data or "properties" not in forecast_data:
        return "Unable to fetch detailed forecast content."
    
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    
    # Formatting for a "perfect" user-friendly response
    for period in periods[:5]:
        forecast = f"""
**{period["name"]}**:
- Temperature: {period["temperature"]}°{period["temperatureUnit"]}
- Wind: {period["windSpeed"]} {period["windDirection"]}
- Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast.strip())
        
    return "### 5-Day Forecast Summary:\n\n" + "\n---\n".join(forecasts)

def main():
    # Ensuring stdio transport for Host integration
    mcp.run(transport="stdio")
    
if __name__ == "__main__":
    main()
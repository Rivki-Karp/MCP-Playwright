# Weather Assistant MCP (Multi-Server)

An intelligent weather assistant built using the **Model Context Protocol (MCP)**. This project integrates two distinct weather sources to provide a comprehensive global forecast experience.

## Features

- **Israel Weather (Browser-Based)**: Uses **Playwright** to automate a real browser session, navigating `weather2day.co.il`, performing searches in Hebrew, and extracting live data.
- **USA Weather (API-Based)**: Connects directly to the **National Weather Service (NWS) API** to fetch detailed 7-day forecasts and active weather alerts.
- **Multi-Server Architecture**: A single `ChatHost` manages two independent MCP servers, each exposing its own set of tools. Tools are namespaced by server to prevent collisions.
- **Automated Cleanup**: The browser-based server automatically closes the browser once data has been extracted.

## Technology Stack

- **Python 3.13+**
- **FastMCP (MCP SDK)**: For creating and managing MCP servers.
- **Playwright**: For browser automation and web scraping.
- **Httpx**: For asynchronous HTTP requests to the NWS API.
- **Anthropic (`claude-haiku-4-5`)**: The LLM that selects tools and generates responses.
- **python-dotenv**: For managing environment variables.

## Project Structure

```
host.py            # ChatHost – connects MCP clients and drives the LLM conversation loop
client.py          # MCPClient – generic stdio MCP client wrapper
weather_USA.py     # MCP server: NWS API tools (get_forecast_in_USA, get_alerts_in_USA)
weather_Israel.py  # MCP server: Playwright tools (open, search, select, extract)
pyproject.toml     # Project metadata and dependencies
```

## Getting Started

### 1. Prerequisites

Ensure you have [`uv`](https://github.com/astral-sh/uv) installed (modern Python package manager).

### 2. Installation

Clone the repository and install dependencies:

```bash
uv sync
uv run playwright install chromium
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_api_key_here
NWS_API_BASE=https://api.weather.gov
USER_AGENT=WeatherAssistant/1.0
```

### 4. Run

```bash
uv run host.py
```

## How It Works

`host.py` starts a chat loop. On each message, it:

1. Collects all tools from both MCP servers (prefixed as `weather_USA__<tool>` and `weather_Israel__<tool>`).
2. Sends the user query and available tools to `claude-haiku-4-5`.
3. The model decides which tool(s) to call and with what arguments.
4. Results are fed back to the model until a final text response is produced.

**Israel flow** (Playwright, 4 steps):
1. `open_weather_forecast_israel` – opens `weather2day.co.il/forecast`.
2. `enter_weather_forecast_city_israel` – types the city name in Hebrew.
3. `select_weather_forecast_city_israel` – picks the first autocomplete result.
4. `extract_weather_data_israel` – scrapes temperature & conditions, then closes the browser.

**USA flow** (NWS API):
- `get_forecast_in_USA(latitude, longitude)` – returns a structured 7-day forecast.
- `get_alerts_in_USA(state)` – returns active weather alerts for a US state (e.g. `NY`, `FL`).

## Example Queries

- `"What is the weather in Bnei Brak?"` — triggers the Playwright automation
- `"Get the forecast for New York City."` — triggers the NWS API
- `"Are there any weather alerts in Florida?"` — triggers alert lookup
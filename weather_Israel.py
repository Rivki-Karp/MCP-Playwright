import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather_israel_mcp")

# Initialize FastMCP server
mcp = FastMCP("WeatherIsrael")

# Global browser state to maintain session
state = {
    "playwright": None,
    "browser": None,
    "page": None
}

async def ensure_browser():
    """Ensures that a browser instance and page are available."""
    if state["page"] is None:
        state["playwright"] = await async_playwright().start()
        state["browser"] = await state["playwright"].chromium.launch(headless=False)
        state["page"] = await state["browser"].new_page()
    return state["page"]

@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Step 1: Opens the Israeli weather forecast website."""
    try:
        page = await ensure_browser()
        await page.goto("https://www.weather2day.co.il/forecast", wait_until="networkidle")
        return "Weather website opened successfully."
    except Exception as e:
        return f"Error opening website: {str(e)}"

@mcp.tool()
async def enter_weather_forecast_city_israel(city_name_hebrew: str) -> str:
    """Step 2: Inputs the city name in Hebrew into the search field."""
    try:
        page = await ensure_browser()
        search_selector = "input#city_search_forecast"
        
        await page.wait_for_selector(search_selector, state="visible")
        await page.click(search_selector)
        await page.fill(search_selector, "") 
        
        # Human-like typing to trigger the specific autocomplete list[cite: 1]
        await page.type(search_selector, city_name_hebrew, delay=200)
        
        return f"City '{city_name_hebrew}' entered into the search field."
    except Exception as e:
        return f"Error entering city: {str(e)}"

@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Step 3: Selects the city from the specific autocomplete list identified in HTML[cite: 1]."""
    try:
        page = await ensure_browser()
        
        # Correct selectors based on the provided HTML[cite: 1]
        list_selector = "#city_search_forecastautocomplete-list"
        item_selector = f"{list_selector} div"
        
        # Wait for the suggestions to appear[cite: 1]
        await page.wait_for_selector(item_selector, timeout=7000)
        
        # Click the first suggestion to trigger navigation[cite: 1]
        await page.click(item_selector)
        
        # Safety Enter and wait for load[cite: 1]
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        
        return "City selected and weather page loaded."
    except Exception as e:
        return f"Error selecting city: {str(e)}"

@mcp.tool()
async def extract_weather_data_israel() -> str:
    """Step 4: Extracts data and then closes the browser[cite: 1]."""
    try:
        page = await ensure_browser()
        await page.wait_for_selector(".current-weather", timeout=10000)
        
        temp = await page.inner_text(".temperature")
        details = await page.inner_text(".weather-details")
        
        result = f"Weather Data:\nTemperature: {temp}\nDetails: {details}"
        
        # Closing the browser after the final action[cite: 1]
        await close_israel_browser()
        
        return result
    except Exception as e:
        await close_israel_browser()
        return f"Error extracting data or browser closed: {str(e)}"

async def close_israel_browser():
    """Helper function to clean up browser resources[cite: 1]."""
    if state["browser"]:
        await state["browser"].close()
    if state["playwright"]:
        await state["playwright"].stop()
    state["page"] = None
    state["browser"] = None
    state["playwright"] = None

if __name__ == "__main__":
    mcp.run()
import mcp.server.fastmcp as fastmcp
from playwright.async_api import async_playwright

# Initialize FastMCP server for Israel weather
mcp = fastmcp.FastMCP("WeatherIsrael")

# Global dictionary to manage Playwright lifecycle
_browser_state = {
    "playwright": None,
    "browser": None,
    "page": None
}

async def get_page():
    """
    Ensures a single browser instance is used across tool calls.
    Launched in non-headless mode to allow visual tracking of the process.
    """
    if _browser_state["page"] is None:
        _browser_state["playwright"] = await async_playwright().start()
        _browser_state["browser"] = await _browser_state["playwright"].chromium.launch(headless=False)
        _browser_state["page"] = await _browser_state["browser"].new_page()
    return _browser_state["page"]

@mcp.tool()
async def open_weather_forecast_israel():
    """
    Step 1: Opens the browser and navigates to the Israeli weather website.
    """
    page = await get_page()
    await page.goto("https://www.weather2day.co.il/forecast")
    return "Weather website opened successfully."

@mcp.tool()
async def enter_weather_forecast_city_israel(city_name: str):
    """
    Step 2: Enters the requested city name into the search input field.
    """
    page = await get_page()
    # Selector for the search input field on weather2day
    search_selector = "input#search-input" 
    await page.wait_for_selector(search_selector)
    await page.fill(search_selector, city_name)
    return f"City '{city_name}' entered into search field."

@mcp.tool()
async def select_weather_forecast_city_israel():
    """
    Step 3: Selects the first result (typically by pressing Enter) and waits for navigation.
    """
    page = await get_page()
    await page.keyboard.press("Enter")
    # Wait for the page to load the specific city's forecast
    await page.wait_for_load_state("networkidle")
    return "City selected and forecast page loaded."

@mcp.tool()
async def scrape_weather_data():
    """
    Step 4 (RAG): Extracts the text content from the forecast page for the LLM to process.
    This provides the context needed for the LLM to answer the user directly.
    """
    page = await get_page()
    # Extracting the main forecast container text to minimize token noise
    # We focus on the body or a specific forecast container
    content = await page.inner_text("body")
    
    # Basic cleaning and truncation to fit within model context limits
    clean_content = " ".join(content.split())
    return f"Extracted Forecast Data: {clean_content[:2000]}"
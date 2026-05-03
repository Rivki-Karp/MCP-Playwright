import os
import asyncio
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("weather-Israel")
FORECAST_URL = os.getenv("FORECAST_URL")

# Browser state management
browser_state = {"page": None, "browser": None, "playwright": None}

async def ensure_browser():
    if not browser_state["page"]:
        browser_state["playwright"] = await async_playwright().start()
        browser_state["browser"] = await browser_state["playwright"].chromium.launch(headless=False)
        context = await browser_state["browser"].new_context(ignore_https_errors=True)
        browser_state["page"] = await context.new_page()
    return browser_state["page"]

@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Opens the weather forecast website in the browser."""
    page = await ensure_browser()
    await page.goto(FORECAST_URL)
    return f"Successfully opened {FORECAST_URL}"

@mcp.tool()
async def enter_weather_forecast_city_israel(city_name: str) -> str:
    """Inputs the city name into the search field."""
    page = await ensure_browser()
    search_selector = "input#autocomplete"
    await page.wait_for_selector(search_selector)
    await page.fill(search_selector, city_name)
    return f"Entered city: {city_name}"

@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Selects the first result from the city suggestion list."""
    page = await ensure_browser()
    item_selector = ".ui-menu-item >> nth=0"
    await page.wait_for_selector(item_selector)
    await page.click(item_selector)
    return "City selected from the list."

@mcp.tool()
async def get_weather_report_israel() -> str:
    """Extracts the forecast data from the page for the LLM context."""
    page = await ensure_browser()
    await page.wait_for_selector(".forecast-wrap")
    text_content = await page.inner_text(".forecast-wrap")
    return f"Forecast data extracted:\n{text_content[:2000]}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
# MCP Israel Weather with Playwright

## Project Goal
This project implements an MCP (Model Context Protocol) Server that uses Playwright automation to fetch real-time weather data from Israeli websites, allowing the LLM to control a browser.

## How to Run
1. Install dependencies: `uv sync`
2. Install Chromium: `uv run playwright install chromium`
3. Run the host: `uv run host.py`

## Example Questions
- "What is the weather in Jerusalem today?"
- "Open the weather site and tell me if it will rain in Tel Aviv."
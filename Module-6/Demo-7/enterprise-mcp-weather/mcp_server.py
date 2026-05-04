import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Weather Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """Fetch real-time weather data"""
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    if not city:
        return "Error: City is required."

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            return f"The current weather in {city} is {temp}°C with {desc}."

        return f"Error: API returned {response.status_code}"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
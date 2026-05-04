import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables securely
load_dotenv()

# Initialize the MCP Server
mcp = FastMCP("Weather Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """Fetches the current weather for a given city."""
    print(f"\n[MCP Server] 🛠️ Tool called: Fetching weather for {city}...")
    
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY is not configured on the server."

    # OpenWeatherMap API Endpoint (units=metric ensures Celsius)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Parsing the specific JSON structure from OpenWeatherMap
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The current weather in {city} is {temp}°C and {desc}."
        elif response.status_code == 401:
            return "Error: Invalid OpenWeatherMap API Key. Did you just create it? It may take 15 mins to activate."
        else:
            return f"Error: Could not retrieve weather for {city}. API returned {response.status_code}."
    except Exception as e:
        return f"Error: Failed to connect to weather service. Details: {e}"

if __name__ == "__main__":
    print("☁️ Starting MCP Weather Server (OpenWeatherMap Edition) on stdio...")
    mcp.run(transport='stdio')
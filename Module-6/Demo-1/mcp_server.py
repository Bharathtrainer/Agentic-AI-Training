from mcp.server.fastmcp import FastMCP
import requests

# Initialize the MCP Server
mcp = FastMCP("Weather Server")

@mcp.tool()
def get_weather(city: str) -> str:
    """Fetches the current weather for a given city."""
    print(f"\n[MCP Server] 🛠️ Tool called: Fetching weather for {city}...")
    
    # Using a free, no-auth weather API
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['current_condition'][0]['temp_C']
            desc = data['current_condition'][0]['weatherDesc'][0]['value']
            return f"The current weather in {city} is {temp}°C and {desc}."
        else:
            return f"Error: Could not retrieve weather for {city}. API returned {response.status_code}."
    except Exception as e:
        return f"Error: Failed to connect to weather service. Details: {e}"

if __name__ == "__main__":
    print("☁️ Starting MCP Weather Server on stdio...")
    mcp.run(transport='stdio')
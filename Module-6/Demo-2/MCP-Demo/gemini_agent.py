import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables securely
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client()

# 1. The Tool Execution Function (Updated for OpenWeatherMap)
def get_weather(city: str) -> str:
    """Fetches the current weather for a given city."""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"The current weather in {city} is {temp}°C and {desc}."
    return f"Failed to get weather data. Status code: {response.status_code}"

def run_agent(user_prompt: str):
    print("🤖 Agent: Thinking about how to solve this...")
    
    # Configure the Agent
    model_id = 'gemini-2.5-flash'
    config = types.GenerateContentConfig(
        tools=[get_weather], 
        temperature=0.2, 
    )

    # First Pass
    response = client.models.generate_content(
        model=model_id,
        contents=user_prompt,
        config=config,
    )

    # Check for tool call
    if response.function_calls:
        for tool_call in response.function_calls:
            if tool_call.name == "get_weather":
                city_arg = tool_call.args["city"]
                print(f"🤖 Agent: I need to check the weather in {city_arg}.")
                
                # Execute the tool
                weather_data = get_weather(city_arg)
                print(f"📊 Tool Data: {weather_data}\n")

                # Second Pass
                print("🤖 Agent: Reasoning based on the new data...")
                final_response = client.models.generate_content(
                    model=model_id,
                    contents=[
                        user_prompt, 
                        response.candidates[0].content, 
                        types.Part.from_function_response(
                            name="get_weather",
                            response={"result": weather_data} 
                        )
                    ],
                    config=config
                )
                print(f"\n✅ Final Answer:\n{final_response.text}")
    else:
        print(f"\n✅ Final Answer:\n{response.text}")

if __name__ == "__main__":
    print("🌟 Welcome to the MCP Weather Agent (OpenWeatherMap Edition)!")
    print("Type 'exit' or 'quit' at any time to stop the program.\n")
    
    while True:
        user_input = input("👤 You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        if not user_input.strip():
            continue
            
        run_agent(user_input)
        print("-" * 50)
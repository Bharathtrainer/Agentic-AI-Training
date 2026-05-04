import os
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Load environment variables securely
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client()

# 2. The Tool Execution Function (Mirroring the MCP capability)
def get_weather(city: str) -> str:
    """Fetches the current weather for a given city."""
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    data = response.json()
    temp = data['current_condition'][0]['temp_C']
    desc = data['current_condition'][0]['weatherDesc'][0]['value']
    return f"The current weather in {city} is {temp}°C and {desc}."

def run_agent(user_prompt: str):
    print(f"👤 User: {user_prompt}\n")
    print("🤖 Agent: Thinking about how to solve this...")
    
    # Configure the Agent with access to the tool
    model_id = 'gemini-2.5-flash'
    config = types.GenerateContentConfig(
        tools=[get_weather], 
        temperature=0.2, # Low temperature for more analytical reasoning
    )

    # First Pass: Ask the LLM how to proceed
    response = client.models.generate_content(
        model=model_id,
        contents=user_prompt,
        config=config,
    )

    # Check if the Agent requested a tool call
    if response.function_calls:
        for tool_call in response.function_calls:
            if tool_call.name == "get_weather":
                city_arg = tool_call.args["city"]
                print(f"🤖 Agent: I need to check the weather in {city_arg}.")
                
                # Execute the tool
                weather_data = get_weather(city_arg)
                print(f"📊 Tool Data: {weather_data}\n")

                # Second Pass: Provide the data back to the LLM for final reasoning
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
        # If the prompt didn't require external tools
        print(f"\n✅ Final Answer:\n{response.text}")

if __name__ == "__main__":
    print("🌟 Welcome to the MCP Weather Agent!")
    print("Type 'exit' or 'quit' at any time to stop the program.\n")
    
    while True:
        # 1. Get manual input from the user
        user_input = input("👤 You: ")
        
        # 2. Allow the user to exit the loop
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        # 3. Skip empty inputs
        if not user_input.strip():
            continue
            
        # 4. Run the agent with the dynamic prompt
        run_agent(user_input)
        print("-" * 50) # Adds a separator line between questions
import os
import requests
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError

# Import our custom enterprise logger
from app.logger import setup_logger

load_dotenv()
logger = setup_logger("WeatherAgent")

class WeatherAgent:
    def __init__(self):
        """Initializes the agent and validates configuration."""
        logger.info("Initializing Enterprise Weather Agent...")
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY missing from environment variables.")
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        
        self.client = genai.Client()
        self.model_id = 'gemini-2.5-flash'
        logger.info("Agent initialized successfully.")

    @staticmethod
    def get_weather(city: str) -> str:
        """Fetches the current weather for a given city."""
        logger.info(f"Tool Execution Requested: Fetching weather for {city}")
        
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                logger.info(f"Tool Execution Successful: {temp}°C in {city}")
                return f"The current weather in {city} is {temp}°C and {desc}."
            
            logger.warning(f"Tool Execution Failed: API returned status {response.status_code}")
            return f"Failed to get weather data. Status code: {response.status_code}"
            
        except Exception as e:
            logger.error(f"Critical Tool Error: {e}")
            return "Error connecting to weather service."

    # --- ENTERPRISE RESILIENCE ---
    # Retries up to 5 times, waiting 2^x seconds between retries, ONLY if it's a ClientError
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(ClientError),
        before_sleep=lambda retry_state: logger.warning(
            f"API Rate Limit hit. Retrying in {retry_state.next_action.sleep} seconds... (Attempt {retry_state.attempt_number}/5)"
        )
    )
    def _call_gemini(self, contents, config):
        """Helper method to wrap the Gemini API call with retry logic."""
        return self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config,
        )

    def ask(self, user_prompt: str):
        """Handles the reasoning loop for a given prompt."""
        logger.info(f"Processing new prompt: '{user_prompt}'")
        
        config = types.GenerateContentConfig(
            tools=[self.get_weather], 
            temperature=0.2, 
        )

        try:
            # First Pass: Ask the LLM (Using the retry wrapper)
            logger.info("Sending initial request to Gemini...")
            response = self._call_gemini(user_prompt, config)

            # Check for tool call
            if response.function_calls:
                for tool_call in response.function_calls:
                    if tool_call.name == "get_weather":
                        city_arg = tool_call.args["city"]
                        
                        # Execute the tool
                        weather_data = self.get_weather(city_arg)

                        # Second Pass: Reasoning (Using the retry wrapper)
                        logger.info("Sending tool data back to Gemini for final reasoning...")
                        final_response = self._call_gemini(
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
                        print(f"\n✅ Final Answer:\n{final_response.text}\n")
            else:
                logger.info("No tools required for this prompt.")
                print(f"\n✅ Final Answer:\n{response.text}\n")
                
        except RetryError as e:
            # If it still fails after all retries are exhausted
            logger.error(f"Exhausted all retries. The AI service is currently overloaded.")
            print("\n❌ Error: The AI service is experiencing heavy traffic. Please wait a minute and try again.\n")
        except ClientError as e:
            # Catching immediate client errors that aren't retried
            logger.error(f"Client error occurred: {e}")
            print("\n❌ Error: There was an issue connecting to the AI service.\n")

if __name__ == "__main__":
    agent = WeatherAgent()
    
    print("-" * 50)
    print("🌟 Enterprise Agent Ready (With Auto-Retry). Type 'exit' to quit.")
    print("-" * 50)
    
    while True:
        user_input = input("\n👤 You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            logger.info("Shutting down agent.")
            print("Goodbye!")
            break
            
        if not user_input.strip():
            continue
            
        agent.ask(user_input)
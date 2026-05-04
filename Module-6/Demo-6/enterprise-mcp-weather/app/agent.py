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
        
        # --- Persistent Chat Session for Memory ---
        self.chat_session = self.client.chats.create(
            model=self.model_id,
            config=types.GenerateContentConfig(
                tools=[self.get_weather],
                temperature=0.2,
            )
        )
        logger.info("Agent and Chat Session initialized successfully.")

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

    # --- Enterprise Resilience (Retries) ---
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(ClientError),
        before_sleep=lambda retry_state: logger.warning(
            f"API Rate Limit hit. Retrying in {retry_state.next_action.sleep} seconds... (Attempt {retry_state.attempt_number}/5)"
        )
    )
    def _send_message(self, content):
        """Helper method to wrap the Chat API call with retry logic."""
        return self.chat_session.send_message(content)

    def ask(self, user_prompt: str) -> str:
        """Handles the reasoning loop and returns the final text response to the UI."""
        logger.info(f"Processing new prompt: '{user_prompt}'")
        
        try:
            # First Pass: Send prompt to the persistent chat
            logger.info("Sending message to Gemini Chat Session...")
            response = self._send_message(user_prompt)

            if response.function_calls:
                for tool_call in response.function_calls:
                    if tool_call.name == "get_weather":
                        city_arg = tool_call.args["city"]
                        
                        # Execute the tool
                        weather_data = self.get_weather(city_arg)

                        # Second Pass: Send tool result back to the chat
                        logger.info("Sending tool data back to chat session for final reasoning...")
                        final_response = self._send_message(
                            types.Part.from_function_response(
                                name="get_weather",
                                response={"result": weather_data} 
                            )
                        )
                        # RETURN the final text to Streamlit
                        return final_response.text
            else:
                logger.info("No tools required for this prompt.")
                # RETURN the text to Streamlit
                return response.text
                
        except RetryError as e:
            logger.error(f"Exhausted all retries. The AI service is currently overloaded.")
            return "❌ Error: The AI service is experiencing heavy traffic. Please wait a minute and try again."
        except ClientError as e:
            logger.error(f"Client error occurred: {e}")
            return "❌ Error: There was an issue connecting to the AI service."
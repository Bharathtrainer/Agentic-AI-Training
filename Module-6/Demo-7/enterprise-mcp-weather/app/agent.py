import os
import json
import requests
import ollama
from dotenv import load_dotenv
from app.logger import setup_logger

load_dotenv()
logger = setup_logger("OllamaWeatherAgent")


class WeatherAgent:
    def __init__(self):
        logger.info("Initializing Local Ollama Weather Agent...")
        self.model_id = 'llama3.1'

        # ✅ STRICT SYSTEM PROMPT
        self.messages = [{
            'role': 'system',
            'content': (
                "You are a strict Weather Assistant.\n"
                "RULES:\n"
                "1. If user asks about weather → ALWAYS call the tool.\n"
                "2. NEVER answer from your own knowledge.\n"
                "3. NEVER say you don't have real-time data.\n"
                "4. ALWAYS use tool result to respond.\n"
                "5. If city is missing → ask for city.\n"
                "6. Keep answers short and professional."
            )
        }]

        # ✅ TOOL SCHEMA (REQUIRED FOR OLLAMA)
        self.tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name like Bengaluru, London"
                        }
                    },
                    "required": ["city"]
                }
            }
        }]

        logger.info(f"Agent initialized with model: {self.model_id}")

    # ✅ TOOL IMPLEMENTATION (SOURCE OF TRUTH)
    @staticmethod
    def get_weather(city: str) -> str:
        logger.info(f"Tool Execution Requested: Weather for {city}")

        if not city:
            return "Error: City not provided."

        api_key = os.environ.get("OPENWEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        try:
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]

                logger.info(f"Tool Success: {temp}°C in {city}")
                return f"The current weather in {city} is {temp}°C with {desc}."

            return f"Error: Weather API returned {response.status_code}"

        except Exception as e:
            logger.error(f"Weather Tool Error: {e}")
            return "Error connecting to weather service."

    # ✅ MAIN AGENT LOOP (GROUNDING FIX APPLIED)
    def ask(self, user_prompt: str) -> str:
        logger.info(f"Processing prompt: '{user_prompt}'")

        self.messages.append({'role': 'user', 'content': user_prompt})

        try:
            # 🔹 First pass: LLM decides tool usage
            response = ollama.chat(
                model=self.model_id,
                messages=self.messages,
                tools=self.tools
            )

            message = response.get("message", {})
            tool_calls = message.get("tool_calls")

            # ✅ TOOL EXECUTION FLOW
            if tool_calls:
                self.messages.append(message)

                for tool in tool_calls:
                    function_name = tool["function"]["name"]
                    args = tool["function"].get("arguments", {})

                    # Handle JSON string args safely
                    if isinstance(args, str):
                        args = json.loads(args)

                    city = args.get("city")

                    if not city:
                        logger.warning("Empty city received from model")
                        return "Please provide a city name."

                    # 🔥 CALL TOOL (REAL DATA)
                    result = self.get_weather(city)

                    # Append tool response (for traceability)
                    self.messages.append({
                        "role": "tool",
                        "name": function_name,
                        "content": result,
                    })

                # ✅ 🔥 CRITICAL FIX: DO NOT CALL LLM AGAIN
                logger.info("Returning grounded tool response (no LLM rewrite)...")

                self.messages.append({
                    "role": "assistant",
                    "content": result
                })

                return result

            # ✅ No tool used (e.g., greeting)
            self.messages.append(message)
            return message.get("content", "")

        except Exception as e:
            logger.error(f"Local Inference Error: {e}")
            return "❌ Error: Ensure 'ollama serve' is running."
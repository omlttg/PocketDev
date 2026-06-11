import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Define a mock tool
def get_weather(location: str):
    """Get weather of a location"""
    return f"Weather in {location} is sunny"

model = genai.GenerativeModel('gemini-2.5-flash', tools=[get_weather])
response = model.generate_content("What is the weather in Hanoi?")
print("Response parts:", response.parts)
for part in response.parts:
    print("Part function_call type:", type(part.function_call))
    print("Part function_call fields:", dir(part.function_call))
    print("Part function_call Name:", part.function_call.name)
    print("Part function_call Args:", part.function_call.args)
    if part.function_call.name:
        print("This part contains a valid function call!")

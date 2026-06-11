import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content("Hello")
print("Response type:", type(response))
print("Available attributes in response:", dir(response))

# Check candidates
if response.candidates:
    candidate = response.candidates[0]
    print("Candidate parts:", candidate.content.parts)
    for part in candidate.content.parts:
        print("Part attributes:", dir(part))
        if hasattr(part, "function_call"):
            print("Part has function_call:", part.function_call)

import os

from dotenv import load_dotenv
from google import genai

# Load the API key from your local .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY was not found in .env")

# Connect to Gemini
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=(
            "You are MethodMind, an educational AI assistant. "
            "In two sentences, explain why a student should "
            "understand the method behind solving an algebra "
            "problem instead of memorising its answer."
        ),
    )

    print("\nGemini connection successful!\n")
    print(response.text)

finally:
    client.close()
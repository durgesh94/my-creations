
# This script demonstrates how to use the Gemini API to generate content using the Gemini model.

from dotenv import load_dotenv
from google import genai
import os

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Call Gemini model
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Explain what RAG is in simple terms."
)

# Print response
print("RESPONSE: ", response.text)

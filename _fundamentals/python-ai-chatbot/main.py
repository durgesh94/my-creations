
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing")

# Initialize Gemini AI client with the provided API key
client = genai.Client(api_key=api_key)

print("🤖 Gemini AI Chatbot")
print("Type 'exit' to stop the chatbot.\n")

while True:
    # 1. Get user input
    user_input = input("You: ").strip()

    # 2. Check exit condition
    if user_input.lower() in ["exit", "quit"]:
        print("Chatbot: Goodbye!")
        break

    # 3. Ignore empty input
    if not user_input:
        continue

    try:
        # 4. Send request to Gemini
        response = client.models.generate_content(
            model=model,
            contents=user_input
        )

        # 5. Display generated answer
        print(f"\nGemini: {response.text}\n")

    except Exception as error:
        print(f"\nError: {error}\n")

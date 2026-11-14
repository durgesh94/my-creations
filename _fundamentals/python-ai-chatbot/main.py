
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

# Create a chat session
chat = client.chats.create(model=model)

print("🤖 Gemini AI Chatbot with Memory")
print("Commands: exit, history, clear\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ["exit", "quit"]:
        print("Chatbot: Goodbye!")
        break

    if user_input.lower() == "clear":
        # Start a new chat session
        chat = client.chats.create(model=model)
        print("Chatbot: Conversation cleared.\n")
        continue

    if user_input.lower() == "history":
        # Display stored conversation
        for message in chat.get_history():
            text = " ".join(
                part.text
                for part in message.parts
                if part.text
            )
            print(f"{message.role}: {text}")
        print()
        continue

    if not user_input:
        continue

    try:
        # Send message with chat history
        response = chat.send_message(user_input)

        print(f"\nGemini: {response.text}\n")

    except Exception as error:
        print(f"\nError: {error}\n")

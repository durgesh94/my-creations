
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Initialize the Gemini client with the API key from environment variables
client = genai.Client(api_key=API_KEY)


# 1. Our Python tool
def get_doctors(specialization: str) -> list[dict]:
    """Find doctors by medical specialization."""
    doctors = [
        {"name": "Dr. Amit", "specialization": "Cardiology"},
        {"name": "Dr. Priya", "specialization": "Dermatology"},
        {"name": "Dr. Rahul", "specialization": "Cardiology"},
    ]

    return [
        doctor
        for doctor in doctors
        if doctor["specialization"].lower()
        == specialization.lower()
    ]


# 2. Tell Gemini which tools are available
config = types.GenerateContentConfig(
    tools=[get_doctors],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    ),
    system_instruction=(
        "You are a hospital assistant. "
        "Use the get_doctors tool for doctor searches. "
        "Never invent doctor records."
    ),
)

# 3. User question
question = "Find all cardiology doctors"

response = client.models.generate_content(
    model=MODEL,
    contents=question,
    config=config,
)

# 4. Inspect the LLM's decision
if response.function_calls:
    tool_call = response.function_calls[0]

    print("LLM selected:", tool_call.name)
    print("Arguments:", tool_call.args)

    # 5. Our application executes the tool
    if tool_call.name == "get_doctors":
        result = get_doctors(**tool_call.args)

        print("Tool result:", result)

        # 6. Return the tool result to Gemini
        final_response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=question)],
                ),
                response.candidates[0].content,
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name="get_doctors",
                            response={"doctors": result},
                        )
                    ],
                ),
            ],
            config=config,
        )

        print("Final answer:", final_response.text)
else:
    print("No tool requested.")
    print("LLM response:", response.text)

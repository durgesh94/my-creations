
import os
from datetime import date, timedelta

from dotenv import load_dotenv
from google import genai
from google.genai import types
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_STEPS = 8
MAX_TOOL_CALLS = 16

# ---------------------------------
# 1. Mock hospital data
# ---------------------------------

DOCTORS = [
    {"id": "doc_101", "name": "Dr. Amit",
     "specialization": "Cardiology"},
    {"id": "doc_102", "name": "Dr. Priya",
     "specialization": "Dermatology"},
    {"id": "doc_103", "name": "Dr. Rahul",
     "specialization": "Cardiology"},
]

SLOTS = {
    "doc_101": ["10:00", "11:30"],
    "doc_102": ["12:00"],
    "doc_103": ["14:00", "16:30"],
}

APPOINTMENTS = [
    {"patient_id": "pat_101", "doctor_id": "doc_101",
     "date": "2026-11-20", "time": "10:00"},
    {"patient_id": "pat_101", "doctor_id": "doc_103",
     "date": "2026-11-22", "time": "14:00"},
]

# ---------------------------------
# 2. Mock RAG policy documents
# ---------------------------------

POLICIES = [
    {
        "id": "policy_01",
        "title": "Appointment Cancellation",
        "text": (
            "Patients can cancel appointments at least "
            "24 hours before the scheduled time without "
            "a cancellation charge. Late cancellations "
            "may incur a fee."
        ),
    },
    {
        "id": "policy_02",
        "title": "Patient Registration",
        "text": (
            "New patients must complete registration "
            "and provide their name, contact details "
            "and valid identification."
        ),
    },
    {
        "id": "policy_03",
        "title": "Hospital Discharge",
        "text": (
            "Before discharge, patients must settle "
            "outstanding bills and collect their "
            "discharge summary and prescriptions."
        ),
    },
    {
        "id": "policy_04",
        "title": "Appointment Booking",
        "text": (
            "Appointments can be booked based on doctor "
            "availability. Patients must select an "
            "available appointment slot."
        ),
    },
]

# Build the retrieval index once
policy_texts = [
    p["title"] + " " + p["text"]
    for p in POLICIES
]

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
)

policy_vectors = vectorizer.fit_transform(policy_texts)


# ---------------------------------
# 3. Tool functions
# ---------------------------------

def get_doctors(specialization: str) -> list[dict]:
    """Find doctors by medical specialization."""
    return [
        d for d in DOCTORS
        if specialization.lower() in d["specialization"].lower()
    ]


def get_available_slots(doctor_id: str) -> dict:
    """Get mock appointment slots for a doctor."""
    if doctor_id not in SLOTS:
        return {"error": "Doctor not found"}

    return {
        "doctor_id": doctor_id,
        "slots": SLOTS[doctor_id],
        "note": "Fictional sample slots, not live availability",
    }


def get_patient_appointments(patient_id: str) -> list[dict]:
    """Get mock appointments for a patient."""
    return [
        a for a in APPOINTMENTS
        if a["patient_id"] == patient_id
    ]


def search_hospital_policy(query: str) -> dict:
    """Retrieve relevant hospital policy passages."""
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector, policy_vectors
    )[0]

    ranked = scores.argsort()[::-1]
    results = []

    for index in ranked[:2]:
        score = float(scores[index])

        # Exclude zero-overlap documents
        if score <= 0:
            continue

        policy = POLICIES[int(index)]

        results.append({
            "id": policy["id"],
            "title": policy["title"],
            "text": policy["text"],
            "score": round(score, 4),
        })

    return {
        "query": query,
        "matches": results,
        "note": (
            "Fictional training policies. "
            "Scores are retrieval similarities, "
            "not probabilities of correctness."
        ),
    }


# ---------------------------------
# 4. Tool registry
# ---------------------------------

TOOL_REGISTRY = {
    "get_doctors": get_doctors,
    "get_available_slots": get_available_slots,
    "get_patient_appointments": get_patient_appointments,
    "search_hospital_policy": search_hospital_policy,
}

TOOL_PARAMETERS = {
    "get_doctors": "specialization",
    "get_available_slots": "doctor_id",
    "get_patient_appointments": "patient_id",
    "search_hospital_policy": "query",
}


# ---------------------------------
# 5. Gemini tool configuration
# ---------------------------------

config = types.GenerateContentConfig(
    tools=list(TOOL_REGISTRY.values()),
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    ),
    system_instruction=(
        "You are a hospital AI assistant using fictional data. "
        "Use tools for doctor searches, appointments, "
        "availability and hospital policy questions. "
        "Never invent doctors, slots or policy details. "
        "For policy answers, use retrieved evidence and "
        "mention the policy title. "
        "If evidence is missing, say so. "
        "Never claim mock slots are live availability. "
        "Do not book or modify appointments."
    ),
)


# ---------------------------------
# 6. Validate and execute tool
# ---------------------------------

def execute_tool(name: str, args: dict) -> dict:
    if name not in TOOL_REGISTRY:
        return {"error": "Unknown tool"}

    expected_parameter = TOOL_PARAMETERS[name]

    if not isinstance(args, dict):
        return {"error": "Invalid arguments"}

    if set(args) != {expected_parameter}:
        return {"error": "Unexpected or missing arguments"}

    value = args[expected_parameter]

    if not isinstance(value, str) or not value.strip():
        return {"error": "Invalid argument value"}

    try:
        result = TOOL_REGISTRY[name](value)
        return {"data": result}
    except Exception:
        return {"error": "Tool execution failed"}


# ---------------------------------
# 7. Agent execution loop
# ---------------------------------

def run_agent(question: str) -> str:
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)],
        )
    ]

    total_tool_calls = 0

    for step in range(1, MAX_STEPS + 1):
        print(f"\n=== AGENT STEP {step} ===")

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )

        if not response.candidates:
            return "No model response available."

        model_content = response.candidates[0].content

        if model_content is None:
            return "No model content available."

        # Preserve the model's tool-call message
        contents.append(model_content)

        calls = response.function_calls or []

        if not calls:
            return response.text or "No final answer generated."

        if total_tool_calls + len(calls) > MAX_TOOL_CALLS:
            return "Agent stopped: tool-call limit reached."

        tool_response_parts = []

        for call in calls:
            name = call.name
            args = dict(call.args or {})

            print("Selected tool:", name)
            print("Arguments:", args)

            result = execute_tool(name, args)

            print("Tool result:", result)

            tool_response_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response=result,
                )
            )

            total_tool_calls += 1

        # Gemini function responses use role="user"
        contents.append(
            types.Content(
                role="user",
                parts=tool_response_parts,
            )
        )

    return "Agent stopped: maximum steps reached."


# ---------------------------------
# 8. Test multiple questions
# ---------------------------------

if __name__ == "__main__":
    questions = [
        "Find all cardiology doctors.",
        "Find cardiology doctors and show their slots.",
        "What is the appointment cancellation policy?",
        (
            "Show appointments for patient pat_101 "
            "and explain the cancellation policy."
        ),
        "What is the refund policy for cancelled surgeries?",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print("USER:", question)

        answer = run_agent(question)

        print("\nFINAL ANSWER:")
        print(answer)

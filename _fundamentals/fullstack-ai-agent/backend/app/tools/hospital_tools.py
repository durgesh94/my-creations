
from langchain_core.tools import tool

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
    {
        "patient_id": "pat_101",
        "doctor_id": "doc_101",
        "date": "2026-11-20",
        "time": "10:00",
    }
]

POLICIES = [
    {
        "id": "policy_01",
        "title": "Appointment Cancellation",
        "text": (
            "Appointments can be cancelled at least "
            "24 hours before the scheduled time "
            "without a cancellation charge. "
            "Late cancellations may incur a fee."
        ),
    },
    {
        "id": "policy_02",
        "title": "Patient Registration",
        "text": (
            "New patients must provide their name, "
            "contact details and valid identification."
        ),
    },
    {
        "id": "policy_03",
        "title": "Hospital Discharge",
        "text": (
            "Patients must settle outstanding bills "
            "before discharge."
        ),
    },
]


@tool
def get_doctors(specialization: str) -> list[dict]:
    """Find doctors by medical specialization."""
    return [
        d for d in DOCTORS
        if specialization.lower() in d["specialization"].lower()
    ]


@tool
def get_available_slots(doctor_id: str) -> dict:
    """Get fictional available slots for a doctor ID."""
    if doctor_id not in SLOTS:
        return {"error": "Doctor not found"}

    return {
        "doctor_id": doctor_id,
        "slots": SLOTS[doctor_id],
        "live": False,
    }


@tool
def get_patient_appointments(patient_id: str) -> list[dict]:
    """Retrieve fictional appointments for a patient ID."""
    return [
        a for a in APPOINTMENTS
        if a["patient_id"] == patient_id
    ]


@tool
def search_hospital_policy(query: str) -> dict:
    """Search hospital policies for relevant information."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    documents = [
        p["title"] + " " + p["text"]
        for p in POLICIES
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(documents)
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(query_vector, matrix)[0]
    ranked = scores.argsort()[::-1]

    matches = [
        {
            **POLICIES[int(i)],
            "score": round(float(scores[i]), 4),
        }
        for i in ranked[:2]
        if scores[i] > 0
    ]

    return {
        "matches": matches,
        "note": (
            "Fictional policies. Lexical matches "
            "do not guarantee sufficient evidence."
        ),
    }


from datetime import date, datetime
from typing import Any

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def book_appointment(
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
) -> dict[str, Any]:
    """
    Request approval before booking a mock appointment.

    Use only when the user explicitly asks to book
    an appointment. The date must be YYYY-MM-DD
    and the time must be HH:MM in 24-hour format.
    """

    # Validate date and time.
    try:
        requested_date = date.fromisoformat(
            appointment_date
        )
        requested_time = datetime.strptime(
            appointment_time, "%H:%M"
        ).time()
    except ValueError:
        return {
            "status": "invalid_datetime",
            "message": "Use YYYY-MM-DD and HH:MM.",
        }

    # Validate that the requested date is not past.
    if requested_date < date.today():
        return {
            "status": "invalid_date",
            "message": "Cannot book a past date.",
        }

    # Phase 1: mock slot lookup.
    # Replace this with your existing availability
    # tool or appointment service later.
    mock_slots = {
        "doc_101": ["10:00", "11:30"],
        "doc_103": ["14:00", "16:30"],
    }

    available_slots = mock_slots.get(doctor_id, [])

    if requested_time.strftime("%H:%M") not in available_slots:
        return {
            "status": "unavailable",
            "message": "Requested slot is unavailable.",
        }

    # Phase 2: pause execution before booking.
    approval = interrupt({
        "type": "appointment_approval",
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "message": (
            "Do you approve this appointment booking?"
        ),
    })

    # This section executes only after resumption.
    if approval != "approve":
        return {
            "status": "cancelled",
            "message": "Appointment booking cancelled.",
        }

    # Mock booking only: no real database changes.
    return {
        "status": "confirmed",
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "message": "Mock appointment booked successfully.",
    }

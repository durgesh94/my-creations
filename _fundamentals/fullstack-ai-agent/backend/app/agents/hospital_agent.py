
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.tools.hospital_tools import (
    get_doctors,
    get_available_slots,
    get_patient_appointments,
    search_hospital_policy,
)

from app.tools.appointment_booking import book_appointment

load_dotenv()

# 1. Register available tools
tools = [
    get_doctors,
    get_available_slots,
    get_patient_appointments,
    search_hospital_policy,
    book_appointment,
]

# 2. Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    google_api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
)

# 3. Bind tools to the model
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """
You are a hospital AI assistant.

Use tools for doctor searches, appointments,
availability, and hospital policy questions.

Rules:
- Never invent doctor or appointment information.
- Available slots are fictional, not live.
- Cite policy titles when answering policy questions.
- If policy evidence is insufficient, say so.
- Never book or modify appointments.
- Patient data is fictional training data.


Appointment booking rules:

1. Use book_appointment only when the user explicitly
   requests an appointment booking.
2. Collect doctor ID, appointment date and time.
3. Never invent missing appointment details.
4. Use YYYY-MM-DD for dates and HH:MM for times.
5. The booking tool requires human approval.
6. Never claim an appointment is confirmed before
   the booking tool returns status "confirmed".
7. All appointment bookings are fictional mock bookings.

"""


# 4. Define the LLM node for handling user messages
def chatbot(state: MessagesState):
    response = llm_with_tools.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
        ]
    )
    # Return the response as a dictionary with the updated messages state.
    # like {"messages": [response]} content the updated conversation state.
    return {"messages": [response]}


# 5. Build the graph for the hospital AI assistant
builder = StateGraph(MessagesState)

# Add nodes for the chatbot that handles user messages
builder.add_node("chatbot", chatbot)
# Add nodes for the tools that the chatbot can invoke
builder.add_node("tools", ToolNode(tools))

# Connect the start node to the chatbot node
builder.add_edge(START, "chatbot")

# 6. Conditional routing for tool invocation like doctor searches, appointments, and policy queries
builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    },
)

# 7. Return tool results to Gemini
builder.add_edge("tools", "chatbot")

# 8. Compile the graph
def create_hospital_agent(
    checkpointer: BaseCheckpointSaver,
):
    return builder.compile(
        checkpointer=checkpointer
    )

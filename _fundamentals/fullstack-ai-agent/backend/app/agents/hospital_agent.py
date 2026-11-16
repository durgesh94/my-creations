
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.tools.hospital_tools import (
    get_doctors,
    get_available_slots,
    get_patient_appointments,
    search_hospital_policy,
)

load_dotenv()

# 1. Register available tools
tools = [
    get_doctors,
    get_available_slots,
    get_patient_appointments,
    search_hospital_policy,
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
"""


# 4. Define the LLM node
def chatbot(state: MessagesState):
    response = llm_with_tools.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
        ]
    )

    return {"messages": [response]}


# 5. Build the graph
builder = StateGraph(MessagesState)

builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot")

# 6. Conditional routing
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
hospital_agent = builder.compile()

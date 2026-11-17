
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.agent import router as agent_router

from contextlib import asynccontextmanager
from app.core.langgraph import (
    create_checkpoint_pool,
    create_checkpointer,
)
from app.agents.hospital_agent import (
    create_hospital_agent,
)

# Define the lifespan context for FastAPI to set up LangGraph checkpointing.
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with create_checkpoint_pool() as pool:

        checkpointer = create_checkpointer(pool)

        # Initialize LangGraph checkpoint tables.
        await checkpointer.setup()

        # Compile the graph with PostgreSQL persistence.
        app.state.hospital_agent = (
            create_hospital_agent(checkpointer)
        )

        print("LangGraph PostgreSQL checkpointer ready")

        yield


# Initialize the FastAPI app with the custom lifespan for LangGraph checkpoint setup.
app = FastAPI(lifespan=lifespan)

# Allow the React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"]
)

# Include the chat router
app.include_router(chat_router)

# Include the conversations router
app.include_router(conversations_router)

# Include the agent router
app.include_router(agent_router)

# Health check endpoint
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "UP",
        "message": "AI Chatbot API is running"
    }

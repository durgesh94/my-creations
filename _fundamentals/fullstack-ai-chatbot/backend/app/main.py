
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Chatbot API",
    description="Multi-model AI chatbot using FastAPI",
    version="1.0.0"
)

# Allow the React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

# Include the chat router
app.include_router(chat_router)

# Include the conversations router
app.include_router(conversations_router)

# Health check endpoint
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "UP",
        "message": "AI Chatbot API is running"
    }

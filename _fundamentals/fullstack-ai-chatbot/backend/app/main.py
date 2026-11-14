
from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="AI Chatbot API",
    description="Multi-model AI chatbot using FastAPI",
    version="1.0.0"
)

app.include_router(chat_router)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "UP",
        "message": "AI Chatbot API is running"
    }

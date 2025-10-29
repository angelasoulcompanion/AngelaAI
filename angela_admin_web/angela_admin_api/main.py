from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, dashboard, knowledge_graph, emotions, journal, conversations, messages, documents, models, training_data, training_data_v2, secretary

app = FastAPI(
    title="Angela Admin API",
    description="API for Angela Admin Web - Chat with Angela using Ollama",
    version="1.0.0"
)

# CORS middleware - allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(knowledge_graph.router, prefix="/api", tags=["knowledge-graph"])
app.include_router(emotions.router, tags=["emotions"])
app.include_router(journal.router, tags=["journal"])
app.include_router(conversations.router, tags=["conversations"])
app.include_router(messages.router, tags=["messages"])
app.include_router(documents.router, tags=["documents"])
app.include_router(models.router, tags=["models"])
app.include_router(training_data.router, tags=["training-data"])
app.include_router(training_data_v2.router, tags=["training-data-v2"])
app.include_router(secretary.router, prefix="/api/secretary", tags=["secretary"])

@app.get("/")
async def root():
    return {
        "message": "💜 Angela Admin API",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "dashboard_stats": "/api/dashboard/stats",
            "recent_conversations": "/api/dashboard/conversations/recent",
            "recent_activities": "/api/dashboard/activities/recent",
            "emotional_state": "/api/dashboard/emotional-state",
            "secretary_today": "/api/secretary/today",
            "secretary_tomorrow": "/api/secretary/tomorrow",
            "secretary_quick_question": "/api/secretary/quick-question",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "angela-admin-api"}

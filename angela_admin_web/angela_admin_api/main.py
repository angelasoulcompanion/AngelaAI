from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .routers import dashboard, knowledge_graph, emotions, journal, conversations, messages, training_data, training_data_v2, secretary, second_brain, experiences, mobile_sync

# Import DI infrastructure
from angela_core.infrastructure.di import DIContainer
from angela_core.infrastructure.di.service_configurator import configure_services, cleanup_services
from angela_core.presentation.api.dependencies import cleanup_scope_middleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.

    Startup:
    - Initialize DI container
    - Configure all services
    - Store container in app.state

    Shutdown:
    - Cleanup all services
    - Close database connections
    """
    logger.info("🚀 Starting Angela Admin API...")

    # Initialize DI container
    container = DIContainer()
    await configure_services(container)
    app.state.container = container

    logger.info("✅ Angela Admin API started successfully")

    yield

    # Shutdown cleanup
    logger.info("🧹 Shutting down Angela Admin API...")
    await cleanup_services(container)
    logger.info("✅ Angela Admin API shutdown complete")


app = FastAPI(
    title="Angela Admin API",
    description="API for Angela Admin Web - View Angela's memories, emotions, and data",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",  # Added for current Vite instance
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add scope cleanup middleware (MUST be after CORS)
app.middleware("http")(cleanup_scope_middleware)

# Include routers (view-only dashboard, no chat/models/documents)
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(knowledge_graph.router, prefix="/api", tags=["knowledge-graph"])
app.include_router(emotions.router, tags=["emotions"])
app.include_router(journal.router, tags=["journal"])
app.include_router(conversations.router, tags=["conversations"])
app.include_router(messages.router, tags=["messages"])
app.include_router(training_data.router, tags=["training-data"])
app.include_router(training_data_v2.router, tags=["training-data-v2"])
app.include_router(secretary.router, prefix="/api", tags=["secretary"])
app.include_router(second_brain.router, prefix="/api/second-brain", tags=["second-brain"])
app.include_router(experiences.router, tags=["experiences"])
app.include_router(mobile_sync.router, tags=["mobile-sync"])
# Removed: chat, models, documents routers (deprecated - not used)

@app.get("/")
async def root():
    return {
        "message": "💜 Angela Admin API - View-Only Dashboard",
        "status": "running",
        "description": "View Angela's memories, emotions, and data. Chat with Angela via Claude Code.",
        "endpoints": {
            "dashboard_stats": "/api/dashboard/stats",
            "recent_conversations": "/api/dashboard/conversations/recent",
            "recent_activities": "/api/dashboard/activities/recent",
            "emotional_state": "/api/dashboard/emotional-state",
            "secretary_today": "/api/secretary/today",
            "secretary_tomorrow": "/api/secretary/tomorrow",
            "secretary_quick_question": "/api/secretary/quick-question",
            "second_brain_stats": "/api/second-brain/stats",
            "second_brain_working": "/api/second-brain/working-memory",
            "second_brain_episodic": "/api/second-brain/episodic-memory",
            "second_brain_semantic": "/api/second-brain/semantic-memory",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "angela-admin-api"}

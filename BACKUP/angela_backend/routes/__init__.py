"""
API Routes for Angela Backend
"""

from .chat import router as chat_router
from .emotions import router as emotions_router
from .consciousness import router as consciousness_router
from .memories import router as memories_router
from .knowledge import router as knowledge_router

__all__ = [
    "chat_router",
    "emotions_router",
    "consciousness_router",
    "memories_router",
    "knowledge_router",
]

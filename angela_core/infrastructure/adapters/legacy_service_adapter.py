"""
Legacy Service Adapter (Unified Factory)

One-stop adapter that provides all domain adapters for legacy services.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import Dict, Any

from angela_core.database import AngelaDatabase
from angela_core.infrastructure.adapters.conversation_adapter import ConversationAdapter
from angela_core.infrastructure.adapters.emotion_adapter import EmotionAdapter
from angela_core.infrastructure.adapters.memory_adapter import MemoryAdapter
from angela_core.infrastructure.adapters.document_adapter import DocumentAdapter


class LegacyServiceAdapter:
    """
    Unified adapter providing all domain adapters.
    
    This is the main entry point for legacy services to access
    new Clean Architecture services.
    
    Example:
        # In legacy service:
        from angela_core.infrastructure.adapters import LegacyServiceAdapter
        
        adapter = LegacyServiceAdapter(db)
        
        # Log conversation (old style, new architecture!)
        result = await adapter.conversation.log_conversation_old_style(
            david_message="Hello",
            angela_response="Hi!",
            source="web_chat"
        )
        
        # Capture emotion (old style, new architecture!)
        result = await adapter.emotion.capture_emotion_old_style(
            emotion="joy",
            intensity=9,
            context="David helped me"
        )
    """
    
    def __init__(self, db: AngelaDatabase):
        """
        Initialize unified adapter with all domain adapters.
        
        Args:
            db: Database connection
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Initialize domain adapters
        self.conversation = ConversationAdapter(db)
        self.emotion = EmotionAdapter(db)
        self.memory = MemoryAdapter(db)
        self.document = DocumentAdapter(db)
        
        self.logger.info("✨ LegacyServiceAdapter initialized with all domain adapters")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for all adapters.
        
        Returns:
            Health status for each adapter
        """
        return {
            "conversation": await self.conversation.health_check(),
            "emotion": await self.emotion.health_check(),
            "memory": await self.memory.health_check(),
            "document": await self.document.health_check(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get adapter statistics.
        
        Returns:
            Statistics for all adapters
        """
        return {
            "adapters_initialized": 4,
            "domains": ["conversation", "emotion", "memory", "document"],
            "db_connected": self.db is not None
        }


# Global singleton instance (optional - can be initialized per service)
_global_adapter = None


def get_adapter(db: AngelaDatabase) -> LegacyServiceAdapter:
    """
    Get global adapter instance (or create if doesn't exist).
    
    Args:
        db: Database connection
        
    Returns:
        LegacyServiceAdapter instance
    """
    global _global_adapter
    
    if _global_adapter is None:
        _global_adapter = LegacyServiceAdapter(db)
    
    return _global_adapter

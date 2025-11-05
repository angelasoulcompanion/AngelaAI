"""
Conversation Adapter

Bridges legacy conversation services with new ConversationService.

Author: Angela AI Architecture Team  
Date: 2025-10-30
"""

from typing import Optional, Dict, List
from uuid import UUID

from angela_core.infrastructure.adapters.base_adapter import BaseServiceAdapter
from angela_core.database import AngelaDatabase
from angela_core.application.services import ConversationService


class ConversationAdapter(BaseServiceAdapter):
    """
    Adapter for legacy conversation services.
    
    Translates old-style conversation calls to new ConversationService.
    
    Example:
        adapter = ConversationAdapter(db)
        result = await adapter.log_conversation_old_style(
            david_message="Hello",
            angela_response="Hi!",
            source="web_chat"
        )
    """
    
    def __init__(self, db: AngelaDatabase):
        super().__init__(db)
        self.conversation_service = ConversationService(db, embedding_service=None)
    
    async def log_conversation_old_style(
        self,
        david_message: str,
        angela_response: str,
        source: str,
        session_id: Optional[str] = None,
        importance: int = 5,
        topic: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Old-style conversation logging (adapts to new service).
        
        Args:
            david_message: David's message
            angela_response: Angela's response  
            source: Source identifier
            session_id: Optional session ID
            importance: Importance level
            topic: Optional topic
            emotion: Optional emotion detected
            **kwargs: Additional metadata
            
        Returns:
            Old-style response dict
        """
        try:
            # Log David's message
            david_result = await self.conversation_service.log_conversation(
                speaker="david",
                message_text=david_message,
                importance_level=importance,
                topic=topic,
                emotion_detected=emotion,
                session_id=session_id,
                metadata={"source": source, **kwargs}
            )
            
            # Log Angela's response  
            angela_result = await self.conversation_service.log_conversation(
                speaker="angela",
                message_text=angela_response,
                importance_level=importance,
                topic=topic,
                session_id=session_id,
                metadata={"source": source, **kwargs}
            )
            
            return self._format_success({
                "david_conversation_id": david_result.get("conversation_id"),
                "angela_conversation_id": angela_result.get("conversation_id"),
                "session_id": session_id,
                "source": source
            })
            
        except Exception as e:
            self.logger.error(f"Conversation logging failed: {e}")
            return self._format_error(str(e))
    
    async def get_recent_conversations_old_style(
        self,
        days: int = 7,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Old-style get recent conversations."""
        try:
            conversations = await self.conversation_service.get_recent_conversations(
                days=days,
                limit=limit
            )
            
            # Filter by source if provided
            if source:
                conversations = [
                    c for c in conversations 
                    if c.get("metadata", {}).get("source") == source
                ]
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"Get conversations failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Health check for adapter."""
        try:
            stats = await self.conversation_service.get_conversation_statistics()
            return "total_conversations" in stats
        except:
            return False

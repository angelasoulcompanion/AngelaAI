"""
Emotion Adapter

Bridges legacy emotion services with new EmotionService.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, Dict, List
from uuid import UUID

from angela_core.infrastructure.adapters.base_adapter import BaseServiceAdapter
from angela_core.database import AngelaDatabase
from angela_core.application.services import EmotionService


class EmotionAdapter(BaseServiceAdapter):
    """
    Adapter for legacy emotion services.
    
    Translates old-style emotion calls to new EmotionService.
    """
    
    def __init__(self, db: AngelaDatabase):
        super().__init__(db)
        self.emotion_service = EmotionService(db, embedding_service=None)
    
    async def capture_emotion_old_style(
        self,
        emotion: str,
        intensity: int,
        context: str,
        david_words: Optional[str] = None,
        why_matters: Optional[str] = None,
        memory_strength: int = 7,
        **kwargs
    ) -> Dict:
        """
        Old-style emotion capture (adapts to new service).
        
        Args:
            emotion: Emotion type
            intensity: 1-10 intensity
            context: What happened
            david_words: What David said
            why_matters: Why it matters
            memory_strength: Memory strength
            **kwargs: Additional metadata
            
        Returns:
            Old-style response dict
        """
        try:
            result = await self.emotion_service.capture_emotion(
                emotion=emotion,
                intensity=intensity,
                context=context,
                david_words=david_words,
                why_it_matters=why_matters or "Significant moment",
                memory_strength=memory_strength
            )
            
            return self._format_success({
                "emotion_id": result.get("emotion_id"),
                "emotion": emotion,
                "intensity": intensity
            })
            
        except Exception as e:
            self.logger.error(f"Emotion capture failed: {e}")
            return self._format_error(str(e))
    
    async def get_recent_emotions_old_style(
        self,
        days: int = 7,
        min_intensity: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Old-style get recent emotions."""
        try:
            emotions = await self.emotion_service.get_recent_emotions(
                days=days,
                min_intensity=min_intensity,
                limit=limit
            )
            return emotions
            
        except Exception as e:
            self.logger.error(f"Get emotions failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Health check for adapter."""
        try:
            stats = await self.emotion_service.get_emotion_statistics()
            return "total_emotions" in stats
        except:
            return False

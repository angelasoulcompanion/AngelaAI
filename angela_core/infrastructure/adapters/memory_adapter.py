"""
Memory Adapter

Bridges legacy memory services with new MemoryService.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, Dict, List
from uuid import UUID

from angela_core.infrastructure.adapters.base_adapter import BaseServiceAdapter
from angela_core.database import AngelaDatabase
from angela_core.application.services import MemoryService


class MemoryAdapter(BaseServiceAdapter):
    """
    Adapter for legacy memory services.
    
    Translates old-style memory calls to new MemoryService.
    """
    
    def __init__(self, db: AngelaDatabase):
        super().__init__(db)
        self.memory_service = MemoryService(db)
    
    async def consolidate_memories_old_style(
        self,
        batch_size: int = 100,
        apply_decay: bool = True,
        **kwargs
    ) -> Dict:
        """
        Old-style memory consolidation (adapts to new service).
        
        Args:
            batch_size: Max batch size
            apply_decay: Apply decay
            **kwargs: Additional params
            
        Returns:
            Old-style response dict
        """
        try:
            result = await self.memory_service.consolidate_memories(
                batch_size=batch_size,
                apply_decay=apply_decay,
                min_strength=kwargs.get("min_strength", 0.1)
            )
            
            return self._format_success({
                "consolidated": result.get("consolidated_count", 0),
                "decayed": result.get("decayed_count", 0),
                "forgotten": result.get("forgotten_count", 0),
                "processing_time": result.get("processing_time", 0)
            })
            
        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")
            return self._format_error(str(e))
    
    async def get_memory_health_old_style(self) -> Dict:
        """Old-style memory health check."""
        try:
            health = await self.memory_service.get_memory_health()
            return health
            
        except Exception as e:
            self.logger.error(f"Get memory health failed: {e}")
            return {"health_score": 0, "error": str(e)}
    
    async def health_check(self) -> bool:
        """Health check for adapter."""
        try:
            stats = await self.memory_service.get_memory_statistics()
            return "total_memories" in stats
        except Exception as e:
            return False

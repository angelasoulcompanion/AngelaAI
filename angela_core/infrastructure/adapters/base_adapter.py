"""
Base Service Adapter

Foundation for adapters that bridge legacy services with Clean Architecture.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import Optional
from abc import ABC, abstractmethod

from angela_core.database import AngelaDatabase


class BaseServiceAdapter(ABC):
    """
    Base adapter class for legacy service integration.
    
    Provides common infrastructure for adapters that translate
    between old-style service calls and new Clean Architecture services.
    
    Pattern: Adapter Pattern
    Purpose: Allow legacy code to use new architecture without full refactoring
    
    Example:
        class MyAdapter(BaseServiceAdapter):
            async def old_style_method(self, **kwargs):
                # Translate old call to new service
                result = await self.new_service.new_method(...)
                # Return in old format
                return self._format_old_style(result)
    """
    
    def __init__(self, db: AngelaDatabase):
        """
        Initialize base adapter.
        
        Args:
            db: Database connection
        """
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"✨ {self.__class__.__name__} initialized")
    
    def _format_success(self, data: dict) -> dict:
        """
        Format success response in old-style format.
        
        Args:
            data: Data from new service
            
        Returns:
            Old-style success response
        """
        return {
            "success": True,
            "data": data
        }
    
    def _format_error(self, error: str) -> dict:
        """
        Format error response in old-style format.
        
        Args:
            error: Error message
            
        Returns:
            Old-style error response
        """
        return {
            "success": False,
            "error": error
        }
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Health check for adapter.
        
        Returns:
            True if adapter is healthy
        """
        pass

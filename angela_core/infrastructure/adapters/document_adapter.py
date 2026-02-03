"""
Document Adapter

Bridges legacy document services with new DocumentService.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, Dict, List
from uuid import UUID

from angela_core.infrastructure.adapters.base_adapter import BaseServiceAdapter
from angela_core.database import AngelaDatabase
from angela_core.application.services import DocumentService


class DocumentAdapter(BaseServiceAdapter):
    """
    Adapter for legacy document/RAG services.
    
    Translates old-style document calls to new DocumentService.
    """
    
    def __init__(self, db: AngelaDatabase):
        super().__init__(db)
        self.document_service = DocumentService(db, embedding_service=None)
    
    async def ingest_document_old_style(
        self,
        file_path: str,
        title: Optional[str] = None,
        category: str = "general",
        importance: float = 0.5,
        **kwargs
    ) -> Dict:
        """
        Old-style document ingestion (adapts to new service).
        
        Args:
            file_path: Path to document
            title: Document title
            category: Category
            importance: Importance score
            **kwargs: Additional params
            
        Returns:
            Old-style response dict
        """
        try:
            result = await self.document_service.ingest_document(
                file_path=file_path,
                title=title,
                category=category,
                importance_score=importance,
                generate_embeddings=kwargs.get("generate_embeddings", False)
            )
            
            return self._format_success({
                "document_id": result.get("document_id"),
                "chunks_created": result.get("chunks_created", 0),
                "processing_time": result.get("processing_time", 0)
            })
            
        except Exception as e:
            self.logger.error(f"Document ingestion failed: {e}")
            return self._format_error(str(e))
    
    async def get_documents_old_style(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Old-style get documents."""
        try:
            if category:
                documents = await self.document_service.get_documents_by_category(
                    category=category,
                    limit=limit
                )
            else:
                documents = await self.document_service.get_documents_ready_for_rag(
                    limit=limit
                )
            return documents
            
        except Exception as e:
            self.logger.error(f"Get documents failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Health check for adapter."""
        try:
            stats = await self.document_service.get_document_statistics()
            return "total_documents" in stats
        except Exception as e:
            return False

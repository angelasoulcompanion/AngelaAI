"""
Document Service

High-level application service for document management (RAG system).
Coordinates use cases, repositories, and services for document operations.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from pathlib import Path

from angela_core.database import AngelaDatabase
from angela_core.domain.entities.document import DocumentCategory, ProcessingStatus
from angela_core.infrastructure.persistence.repositories import DocumentRepository
from angela_core.application.use_cases.document import (
    IngestDocumentUseCase,
    IngestDocumentInput
)


class DocumentService:
    """
    High-level service for document management (RAG system).

    This service provides a simplified API for:
    - Ingesting documents
    - Retrieving documents
    - Searching documents with RAG
    - Managing document lifecycle

    Coordinates:
    - IngestDocumentUseCase
    - DocumentRepository
    - EmbeddingService (optional)

    Example:
        >>> service = DocumentService(db)
        >>> result = await service.ingest_document(
        ...     file_path="/path/to/doc.pdf",
        ...     title="Architecture Guide",
        ...     category="angela_core",
        ...     importance=0.9
        ... )
        >>> if result["success"]:
        ...     print(f"Ingested: {result['document_id']}")
        ...     print(f"Chunks: {result['chunks_created']}")
    """

    def __init__(
        self,
        db: AngelaDatabase,
        embedding_service: Optional[Any] = None
    ):
        """
        Initialize document service with dependencies.

        Args:
            db: Database connection
            embedding_service: Optional embedding service
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Initialize repository
        self.document_repo = DocumentRepository(db)

        # Initialize use cases
        self.ingest_document_use_case = IngestDocumentUseCase(
            document_repo=self.document_repo,
            embedding_service=embedding_service
        )

    # ========================================================================
    # HIGH-LEVEL API - DOCUMENT INGESTION
    # ========================================================================

    async def ingest_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        category: str = "general",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance_score: float = 0.5,
        quality_rating: float = 0.7,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG system.

        Args:
            file_path: Path to document file
            title: Document title (defaults to filename)
            category: Document category ('angela_core', 'programming', etc.)
            author: Document author
            tags: List of tags
            importance_score: Importance (0.0-1.0)
            quality_rating: Quality (0.0-1.0)
            chunk_size: Target chunk size (characters)
            chunk_overlap: Overlap between chunks (characters)
            generate_embeddings: Whether to generate embeddings

        Returns:
            {
                "success": bool,
                "document_id": UUID (if success),
                "chunks_created": int (if success),
                "embeddings_generated": int (if success),
                "processing_time": float (if success),
                "error": str (if failure)
            }
        """
        try:
            # Convert string category to enum
            category_enum = DocumentCategory(category.lower())

            # Create input
            input_data = IngestDocumentInput(
                file_path=file_path,
                title=title,
                category=category_enum,
                author=author,
                tags=tags,
                importance_score=importance_score,
                quality_rating=quality_rating,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                generate_embeddings=generate_embeddings
            )

            # Execute use case
            result = await self.ingest_document_use_case.execute(input_data)

            # Return simplified result
            if result.success:
                return {
                    "success": True,
                    "document_id": str(result.data.document.id),
                    "title": result.data.document.title,
                    "chunks_created": result.data.chunks_created,
                    "embeddings_generated": result.data.embeddings_generated,
                    "processing_time": result.data.processing_time_seconds,
                    "file_path": file_path,
                    "category": category
                }
            else:
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            self.logger.error(f"Error ingesting document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def ingest_directory(
        self,
        directory_path: str,
        pattern: str = "*.md",
        category: str = "general",
        importance_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Batch ingest all documents in a directory.

        Args:
            directory_path: Path to directory
            pattern: File pattern (e.g., "*.md", "*.pdf")
            category: Document category
            importance_score: Importance for all documents

        Returns:
            {
                "success": bool,
                "total_files": int,
                "successful": int,
                "failed": int,
                "results": List[Dict]
            }
        """
        try:
            dir_path = Path(directory_path)

            if not dir_path.exists() or not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}"
                }

            # Find all matching files
            files = list(dir_path.glob(pattern))

            results = []
            successful = 0
            failed = 0

            for file_path in files:
                result = await self.ingest_document(
                    file_path=str(file_path),
                    category=category,
                    importance_score=importance_score
                )

                results.append({
                    "file": str(file_path),
                    "success": result["success"],
                    "document_id": result.get("document_id"),
                    "error": result.get("error")
                })

                if result["success"]:
                    successful += 1
                else:
                    failed += 1

            return {
                "success": True,
                "total_files": len(files),
                "successful": successful,
                "failed": failed,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Error ingesting directory: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HIGH-LEVEL API - DOCUMENT RETRIEVAL
    # ========================================================================

    async def get_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document dict or None if not found
        """
        try:
            document = await self.document_repo.get_by_id(document_id)

            if document:
                return self._document_to_dict(document)
            return None

        except Exception as e:
            self.logger.error(f"Error getting document: {e}")
            return None

    async def get_documents_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get documents by category.

        Args:
            category: Document category
            limit: Maximum results

        Returns:
            List of document dicts
        """
        try:
            documents = await self.document_repo.get_by_category(
                category=category.lower(),
                limit=limit
            )

            return [self._document_to_dict(d) for d in documents]

        except Exception as e:
            self.logger.error(f"Error getting documents by category: {e}")
            return []

    async def get_documents_ready_for_rag(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get documents ready for RAG (status=completed with chunks).

        Args:
            limit: Maximum results

        Returns:
            List of RAG-ready document dicts
        """
        try:
            documents = await self.document_repo.get_ready_for_rag(limit=limit)

            return [self._document_to_dict(d) for d in documents]

        except Exception as e:
            self.logger.error(f"Error getting RAG-ready documents: {e}")
            return []

    async def get_important_documents(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get important documents (importance >= threshold).

        Args:
            threshold: Importance threshold (0.0-1.0)
            limit: Maximum results

        Returns:
            List of important document dicts
        """
        try:
            documents = await self.document_repo.get_important(
                threshold=threshold,
                limit=limit
            )

            return [self._document_to_dict(d) for d in documents]

        except Exception as e:
            self.logger.error(f"Error getting important documents: {e}")
            return []

    # ========================================================================
    # HIGH-LEVEL API - RAG SEARCH
    # ========================================================================

    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Semantic search for documents using RAG.

        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional category filter

        Returns:
            List of (document_dict, similarity_score) tuples
        """
        try:
            # Generate query embedding
            if not hasattr(self, 'embedding_service') or self.embedding_service is None:
                self.logger.warning("Embedding service not available for search")
                return []

            query_embedding = await self.embedding_service.generate_embedding(query)

            # Prepare filters
            filters = {}
            if category:
                filters['category'] = category.lower()

            # Search documents
            results = await self.document_repo.search_by_vector(
                embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )

            # Convert to dicts with similarity scores
            return [(self._document_to_dict(doc), score) for doc, score in results]

        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []

    async def get_document_chunks(
        self,
        document_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of chunk dicts
        """
        try:
            chunks = await self.document_repo.get_chunks_by_document(document_id)

            return [self._chunk_to_dict(c) for c in chunks]

        except Exception as e:
            self.logger.error(f"Error getting document chunks: {e}")
            return []

    # ========================================================================
    # HIGH-LEVEL API - DOCUMENT MANAGEMENT
    # ========================================================================

    async def retry_failed_document(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Retry processing a failed document.

        Args:
            document_id: Document UUID

        Returns:
            {"success": bool, "error": str (if failure)}
        """
        try:
            # Get document
            document = await self.document_repo.get_by_id(document_id)

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            if document.processing_status != ProcessingStatus.FAILED:
                return {
                    "success": False,
                    "error": f"Document is not in failed state: {document.processing_status.value}"
                }

            # Reset to pending
            document = document.retry_processing()
            await self.document_repo.update(document_id, document)

            # Re-ingest
            result = await self.ingest_document(
                file_path=document.file_path,
                title=document.title,
                category=document.category.value,
                importance_score=document.importance_score
            )

            return result

        except Exception as e:
            self.logger.error(f"Error retrying document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def archive_document(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Archive a document (soft delete).

        Args:
            document_id: Document UUID

        Returns:
            {"success": bool, "error": str (if failure)}
        """
        try:
            document = await self.document_repo.get_by_id(document_id)

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            # Archive
            document = document.archive()
            await self.document_repo.update(document_id, document)

            return {
                "success": True,
                "document_id": str(document_id),
                "status": "archived"
            }

        except Exception as e:
            self.logger.error(f"Error archiving document: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HIGH-LEVEL API - DOCUMENT ANALYTICS
    # ========================================================================

    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get document system statistics.

        Returns:
            {
                "total_documents": int,
                "by_category": {"angela_core": int, ...},
                "by_status": {"completed": int, "failed": int, ...},
                "total_chunks": int,
                "avg_chunks_per_document": float,
                "ready_for_rag": int
            }
        """
        try:
            # Get all documents
            all_documents = await self.document_repo.list(limit=10000)

            # Calculate statistics
            total = len(all_documents)
            by_category = {}
            by_status = {}
            total_chunks = 0

            for doc in all_documents:
                category = doc.category.value
                by_category[category] = by_category.get(category, 0) + 1

                status = doc.processing_status.value
                by_status[status] = by_status.get(status, 0) + 1

                total_chunks += doc.total_chunks

            # Get RAG-ready count
            rag_ready = await self.document_repo.get_ready_for_rag(limit=10000)

            return {
                "total_documents": total,
                "by_category": by_category,
                "by_status": by_status,
                "total_chunks": total_chunks,
                "avg_chunks_per_document": total_chunks / total if total > 0 else 0,
                "ready_for_rag": len(rag_ready),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting document statistics: {e}")
            return {
                "total_documents": 0,
                "error": str(e)
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _document_to_dict(self, document) -> Dict[str, Any]:
        """
        Convert document entity to dictionary.

        Args:
            document: Document entity

        Returns:
            Dictionary representation
        """
        return {
            "document_id": str(document.id),
            "title": document.title,
            "file_path": document.file_path,
            "file_type": document.file_type.value,
            "file_size_bytes": document.file_size_bytes,
            "category": document.category.value,
            "tags": document.tags,
            "author": document.author,
            "summary": document.summary,
            "short_summary": document.short_summary,
            "key_topics": document.key_topics,
            "total_chunks": document.total_chunks,
            "processing_status": document.processing_status.value,
            "processing_error": document.processing_error,
            "importance_score": document.importance_score,
            "quality_rating": document.quality_rating,
            "is_ready_for_rag": document.is_ready_for_rag(),
            "is_important": document.is_important(),
            "access_count": document.access_count,
            "last_accessed_at": document.last_accessed_at.isoformat() if document.last_accessed_at else None,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "has_embedding": (document.embedding is not None)
        }

    def _chunk_to_dict(self, chunk) -> Dict[str, Any]:
        """
        Convert chunk entity to dictionary.

        Args:
            chunk: DocumentChunk entity

        Returns:
            Dictionary representation
        """
        return {
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "content_length": len(chunk.content),
            "importance_score": chunk.importance_score,
            "has_embedding": (chunk.embedding is not None),
            "metadata": chunk.metadata
        }

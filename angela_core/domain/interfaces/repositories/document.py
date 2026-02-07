"""Document repository interface for Angela AI (RAG system)."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from abc import abstractmethod

from .base import IRepository


class IDocumentRepository(IRepository):
    """
    Extended interface for document-specific queries (RAG system).
    Handles document storage and vector search.
    """

    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Vector similarity search.

        Args:
            embedding: Query embedding vector (768 dimensions)
            top_k: Number of top results to return
            filters: Optional filters (e.g., category, source)

        Returns:
            List of (Document, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """Get documents by category."""
        ...

    @abstractmethod
    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Any]:
        """Get documents by processing status (pending, processing, completed, failed)."""
        ...

    @abstractmethod
    async def get_ready_for_rag(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get documents ready for RAG (status=completed with chunks)."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get important documents (importance_score >= threshold)."""
        ...

    @abstractmethod
    async def get_by_tags(
        self,
        tags: List[str],
        limit: int = 100
    ) -> List[Any]:
        """Get documents by tags."""
        ...

    @abstractmethod
    async def search_by_title(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Search documents by title."""
        ...

    @abstractmethod
    async def get_by_source(
        self,
        source: str,
        limit: int = 100
    ) -> List[Any]:
        """Get documents by source (e.g., file path, URL)."""
        ...

    @abstractmethod
    async def batch_create(
        self,
        documents: List[Any]
    ) -> List[Any]:
        """Batch insert documents (optimized for imports)."""
        ...

    # DocumentChunk methods
    @abstractmethod
    async def get_chunk_by_id(self, id: UUID) -> Optional[Any]:
        """Get document chunk by ID."""
        ...

    @abstractmethod
    async def create_chunk(self, chunk: Any) -> Any:
        """Save new document chunk."""
        ...

    @abstractmethod
    async def get_chunks_by_document(
        self,
        document_id: UUID,
        limit: int = 1000
    ) -> List[Any]:
        """Get all chunks for a document."""
        ...

    @abstractmethod
    async def get_important_chunks(
        self,
        document_id: UUID,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get important chunks from a document."""
        ...

    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """Count documents by processing status."""
        ...

    @abstractmethod
    async def count_chunks(self, document_id: UUID) -> int:
        """Count chunks for a document."""
        ...

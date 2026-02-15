"""Embedding repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from abc import abstractmethod

from .base import IRepository


class IEmbeddingRepository(IRepository):
    """
    Extended interface for vector embedding operations.
    Provides unified access to similarity search across all embedding tables.
    """

    @abstractmethod
    async def search_conversations(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Search conversations by vector similarity.

        Args:
            embedding: Query embedding (384 dimensions)
            top_k: Number of results
            filters: Optional filters (speaker, importance, date_range, etc.)

        Returns:
            List of (Conversation, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def search_emotions(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Search emotions by vector similarity.

        Args:
            embedding: Query embedding
            top_k: Number of results
            filters: Optional filters (emotion_type, intensity, etc.)

        Returns:
            List of (Emotion, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def search_memories(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Search memories by vector similarity.

        Args:
            embedding: Query embedding
            top_k: Number of results
            filters: Optional filters (phase, importance, etc.)

        Returns:
            List of (Memory, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def search_knowledge(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Search knowledge nodes by vector similarity.

        Args:
            embedding: Query embedding
            top_k: Number of results
            filters: Optional filters (category, understanding_level, etc.)

        Returns:
            List of (KnowledgeNode, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def search_documents(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Search document chunks by vector similarity.

        Args:
            embedding: Query embedding
            top_k: Number of results
            filters: Optional filters (document_id, importance, etc.)

        Returns:
            List of (DocumentChunk, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def search_all(
        self,
        embedding: List[float],
        top_k_per_table: int = 3
    ) -> Dict[str, List[tuple[Any, float]]]:
        """
        Search across all tables simultaneously.

        Args:
            embedding: Query embedding
            top_k_per_table: Number of results per table

        Returns:
            Dictionary with results from all tables:
            {
                "conversations": [(entity, score), ...],
                "emotions": [(entity, score), ...],
                "memories": [(entity, score), ...],
                "knowledge": [(entity, score), ...],
                "documents": [(entity, score), ...]
            }
        """
        ...

    @abstractmethod
    async def get_tables_with_embeddings(self) -> List[str]:
        """
        Get list of tables that have embedding columns.

        Returns:
            List of table names
        """
        ...

    @abstractmethod
    async def count_embeddings(self, table_name: str) -> int:
        """
        Count number of records with embeddings in a table.

        Args:
            table_name: Table name

        Returns:
            Count of records with non-null embeddings
        """
        ...

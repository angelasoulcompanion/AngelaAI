#!/usr/bin/env python3
"""
Embedding Repository - Unified Vector Operations

Provides unified access to vector similarity search across all embedding tables.
Enables cross-table semantic search for RAG and knowledge retrieval.
"""

import asyncpg
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from angela_core.domain import (
    Conversation, Emotion, Memory, KnowledgeNode, DocumentChunk
)
from angela_core.domain.interfaces.repositories import IEmbeddingRepository
from angela_core.infrastructure.persistence.repositories import (
    ConversationRepository,
    EmotionRepository,
    MemoryRepository,
    KnowledgeRepository,
    DocumentRepository
)


class EmbeddingRepository(IEmbeddingRepository):
    """
    Unified repository for vector embedding operations.

    Provides semantic search capabilities across all tables with embeddings:
    - conversations (384-dim vectors)
    - angela_emotions (384-dim vectors)
    - long_term_memory (384-dim vectors)
    - knowledge_nodes (384-dim vectors)
    - document_chunks (384-dim vectors)

    Uses pgvector <=> operator for cosine distance similarity search.
    """

    def __init__(self, db):
        """
        Initialize embedding repository.

        Args:
            db: Database connection pool
        """
        self.db = db

        # Initialize individual repositories for entity conversion
        self.conversation_repo = ConversationRepository(db)
        self.emotion_repo = EmotionRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.knowledge_repo = KnowledgeRepository(db)
        self.document_repo = DocumentRepository(db)

        # Table metadata
        self.embedding_tables = {
            "conversations": {
                "table": "conversations",
                "pk": "conversation_id",
                "repo": self.conversation_repo
            },
            "emotions": {
                "table": "angela_emotions",
                "pk": "emotion_id",
                "repo": self.emotion_repo
            },
            "memories": {
                "table": "long_term_memory",
                "pk": "id",
                "repo": self.memory_repo
            },
            "knowledge": {
                "table": "knowledge_nodes",
                "pk": "node_id",
                "repo": self.knowledge_repo
            },
            "documents": {
                "table": "document_chunks",
                "pk": "chunk_id",
                "repo": self.document_repo
            }
        }

    # ========================================================================
    # DOMAIN-SPECIFIC SEARCHES
    # ========================================================================

    async def search_conversations(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Conversation, float]]:
        """
        Search conversations by vector similarity.

        Args:
            embedding: Query embedding (384 dimensions)
            top_k: Number of results
            filters: Optional filters (speaker, importance, date_range, etc.)

        Returns:
            List of (Conversation, similarity_score) tuples
        """
        query = """
            SELECT *, (embedding <=> $1::vector) as distance
            FROM conversations
            WHERE embedding IS NOT NULL
        """

        params = [embedding]
        param_count = 1

        # Apply filters
        if filters:
            if filters.get("speaker"):
                param_count += 1
                query += f" AND speaker = ${param_count}"
                params.append(filters["speaker"])

            if filters.get("min_importance"):
                param_count += 1
                query += f" AND importance_level >= ${param_count}"
                params.append(filters["min_importance"])

            if filters.get("date_from"):
                param_count += 1
                query += f" AND created_at >= ${param_count}"
                params.append(filters["date_from"])

        query += f" ORDER BY distance ASC LIMIT ${param_count + 1}"
        params.append(top_k)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        # Convert to entities with similarity scores
        results = []
        for row in rows:
            conversation = self.conversation_repo._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((conversation, similarity))

        return results

    async def search_emotions(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Emotion, float]]:
        """Search emotions by vector similarity."""
        query = """
            SELECT *, (embedding <=> $1::vector) as distance
            FROM angela_emotions
            WHERE embedding IS NOT NULL
        """

        params = [embedding]
        param_count = 1

        # Apply filters
        if filters:
            if filters.get("emotion_type"):
                param_count += 1
                query += f" AND emotion = ${param_count}"
                params.append(filters["emotion_type"])

            if filters.get("min_intensity"):
                param_count += 1
                query += f" AND intensity >= ${param_count}"
                params.append(filters["min_intensity"])

            if filters.get("min_memory_strength"):
                param_count += 1
                query += f" AND memory_strength >= ${param_count}"
                params.append(filters["min_memory_strength"])

        query += f" ORDER BY distance ASC LIMIT ${param_count + 1}"
        params.append(top_k)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            emotion = self.emotion_repo._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((emotion, similarity))

        return results

    async def search_memories(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Memory, float]]:
        """Search memories by vector similarity."""
        query = """
            SELECT *, (embedding <=> $1::vector) as distance
            FROM long_term_memory
            WHERE embedding IS NOT NULL
        """

        params = [embedding]
        param_count = 1

        # Apply filters
        if filters:
            if filters.get("memory_phase"):
                param_count += 1
                query += f" AND memory_phase = ${param_count}"
                params.append(filters["memory_phase"])

            if filters.get("min_importance"):
                param_count += 1
                query += f" AND importance >= ${param_count}"
                params.append(filters["min_importance"])

            if filters.get("min_strength"):
                param_count += 1
                query += f" AND strength >= ${param_count}"
                params.append(filters["min_strength"])

        query += f" ORDER BY distance ASC LIMIT ${param_count + 1}"
        params.append(top_k)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            memory = self.memory_repo._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((memory, similarity))

        return results

    async def search_knowledge(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[KnowledgeNode, float]]:
        """Search knowledge nodes by vector similarity."""
        query = """
            SELECT *, (embedding <=> $1::vector) as distance
            FROM knowledge_nodes
            WHERE embedding IS NOT NULL
        """

        params = [embedding]
        param_count = 1

        # Apply filters
        if filters:
            if filters.get("category"):
                param_count += 1
                query += f" AND category = ${param_count}"
                params.append(filters["category"])

            if filters.get("min_understanding"):
                param_count += 1
                query += f" AND understanding_level >= ${param_count}"
                params.append(filters["min_understanding"])

            if filters.get("about_david"):
                param_count += 1
                query += f" AND is_about_david = ${param_count}"
                params.append(True)

        query += f" ORDER BY distance ASC LIMIT ${param_count + 1}"
        params.append(top_k)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            knowledge = self.knowledge_repo._row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((knowledge, similarity))

        return results

    async def search_documents(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[DocumentChunk, float]]:
        """Search document chunks by vector similarity."""
        query = """
            SELECT *, (embedding <=> $1::vector) as distance
            FROM document_chunks
            WHERE embedding IS NOT NULL
        """

        params = [embedding]
        param_count = 1

        # Apply filters
        if filters:
            if filters.get("document_id"):
                param_count += 1
                query += f" AND document_id = ${param_count}"
                params.append(filters["document_id"])

            if filters.get("min_importance"):
                param_count += 1
                query += f" AND importance_score >= ${param_count}"
                params.append(filters["min_importance"])

        query += f" ORDER BY distance ASC LIMIT ${param_count + 1}"
        params.append(top_k)

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            chunk = self.document_repo._chunk_row_to_entity(row)
            similarity = 1.0 - float(row['distance'])
            results.append((chunk, similarity))

        return results

    # ========================================================================
    # CROSS-TABLE SEARCH
    # ========================================================================

    async def search_all(
        self,
        embedding: List[float],
        top_k_per_table: int = 3
    ) -> Dict[str, List[tuple[Any, float]]]:
        """
        Search across all tables simultaneously.

        This is the most powerful method - enables semantic search
        across Angela's entire knowledge base in one call.

        Args:
            embedding: Query embedding (384 dimensions)
            top_k_per_table: Number of results per table

        Returns:
            Dictionary with results from all tables
        """
        # Execute all searches in parallel
        import asyncio

        conversations_task = self.search_conversations(embedding, top_k_per_table)
        emotions_task = self.search_emotions(embedding, top_k_per_table)
        memories_task = self.search_memories(embedding, top_k_per_table)
        knowledge_task = self.search_knowledge(embedding, top_k_per_table)
        documents_task = self.search_documents(embedding, top_k_per_table)

        # Wait for all searches to complete
        conversations, emotions, memories, knowledge, documents = await asyncio.gather(
            conversations_task,
            emotions_task,
            memories_task,
            knowledge_task,
            documents_task
        )

        return {
            "conversations": conversations,
            "emotions": emotions,
            "memories": memories,
            "knowledge": knowledge,
            "documents": documents
        }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_tables_with_embeddings(self) -> List[str]:
        """Get list of tables that have embedding columns."""
        return list(self.embedding_tables.keys())

    async def count_embeddings(self, table_name: str) -> int:
        """
        Count number of records with embeddings in a table.

        Args:
            table_name: Table name (conversations, emotions, memories, knowledge, documents)

        Returns:
            Count of records with non-null embeddings
        """
        if table_name not in self.embedding_tables:
            return 0

        table_info = self.embedding_tables[table_name]
        table = table_info["table"]

        query = f"""
            SELECT COUNT(*) FROM {table}
            WHERE embedding IS NOT NULL
        """

        async with self.db.acquire() as conn:
            count = await conn.fetchval(query)

        return count

    # ========================================================================
    # BASE REPOSITORY METHODS (NOT APPLICABLE)
    # ========================================================================

    async def get_by_id(self, id: UUID) -> Optional[Any]:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support get_by_id - use domain-specific repositories")

    async def get_all(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = True) -> List[Any]:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support get_all - use search methods instead")

    async def create(self, entity: Any) -> Any:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support create - use domain-specific repositories")

    async def update(self, id: UUID, entity: Any) -> Any:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support update - use domain-specific repositories")

    async def delete(self, id: UUID) -> bool:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support delete - use domain-specific repositories")

    async def exists(self, id: UUID) -> bool:
        """Not applicable for embedding repository."""
        raise NotImplementedError("EmbeddingRepository doesn't support exists - use domain-specific repositories")

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count total embeddings across all tables."""
        counts = {}
        for table_name in self.embedding_tables.keys():
            counts[table_name] = await self.count_embeddings(table_name)
        return sum(counts.values())

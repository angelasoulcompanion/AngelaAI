#!/usr/bin/env python3
"""
Repository Interfaces for Angela AI
Defines contracts for all data access operations.

Following Interface Segregation Principle:
- Base IRepository for common CRUD operations
- Specific interfaces extend base with domain-specific queries
"""

from typing import Protocol, TypeVar, Generic, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from abc import abstractmethod

T = TypeVar('T')

# ============================================================================
# BASE REPOSITORY INTERFACE
# ============================================================================

class IRepository(Protocol, Generic[T]):
    """
    Base repository interface for CRUD operations.
    All repositories MUST implement these methods.

    Type Parameters:
        T: Domain entity type

    Usage:
        class MyRepository(IRepository[MyEntity]):
            async def get_by_id(self, id: UUID) -> Optional[MyEntity]:
                # Implementation
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity UUID

        Returns:
            Entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
            order_desc: Order descending if True, ascending if False

        Returns:
            List of entities
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID assigned
        """
        ...

    @abstractmethod
    async def update(self, id: UUID, entity: T) -> T:
        """
        Update existing entity.

        Args:
            id: Entity ID
            entity: Updated entity data

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        ...

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching filters.

        Args:
            filters: Optional filter criteria

        Returns:
            Number of matching entities
        """
        ...


# ============================================================================
# CONVERSATION REPOSITORY INTERFACE
# ============================================================================

class IConversationRepository(IRepository):
    """
    Extended interface for conversation-specific queries.
    Handles all conversation storage and retrieval.
    """

    @abstractmethod
    async def get_by_speaker(
        self,
        speaker: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:
        """Get conversations by speaker (e.g., 'david' or 'angela')."""
        ...

    @abstractmethod
    async def get_by_session(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Any]:
        """Get all conversations in a session."""
        ...

    @abstractmethod
    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        speaker: Optional[str] = None
    ) -> List[Any]:
        """Get conversations within date range."""
        ...

    @abstractmethod
    async def search_by_topic(
        self,
        topic: str,
        limit: int = 50
    ) -> List[Any]:
        """Search conversations by topic."""
        ...

    @abstractmethod
    async def search_by_text(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Full-text search in message_text."""
        ...

    @abstractmethod
    async def get_recent_conversations(
        self,
        days: int = 7,
        speaker: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Any]:
        """Get recent conversations from last N days."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get important conversations (importance >= threshold)."""
        ...

    @abstractmethod
    async def get_with_emotion(
        self,
        emotion: str,
        limit: int = 100
    ) -> List[Any]:
        """Get conversations with specific emotion detected."""
        ...

    @abstractmethod
    async def count_by_speaker(self, speaker: str) -> int:
        """Count conversations by speaker."""
        ...


# ============================================================================
# EMOTION REPOSITORY INTERFACE
# ============================================================================

class IEmotionRepository(IRepository):
    """
    Extended interface for emotion-specific queries.
    Handles significant emotional moments storage.
    """

    @abstractmethod
    async def get_by_emotion_type(
        self,
        emotion_type: str,
        min_intensity: Optional[int] = None,
        limit: int = 50
    ) -> List[Any]:
        """Get emotions by type with optional intensity filter."""
        ...

    @abstractmethod
    async def get_recent_emotions(
        self,
        days: int = 7,
        min_intensity: Optional[int] = None
    ) -> List[Any]:
        """Get recent emotions from last N days."""
        ...

    @abstractmethod
    async def get_intense(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get intense emotions (intensity >= threshold)."""
        ...

    @abstractmethod
    async def get_strongly_remembered(
        self,
        threshold: int = 8,
        limit: int = 100
    ) -> List[Any]:
        """Get strongly remembered emotions (memory_strength >= threshold)."""
        ...

    @abstractmethod
    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions involving David."""
        ...

    @abstractmethod
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions linked to a conversation."""
        ...

    @abstractmethod
    async def get_positive(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get positive emotions."""
        ...

    @abstractmethod
    async def get_negative(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get negative emotions."""
        ...

    @abstractmethod
    async def get_reflected(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get emotions that have been reflected upon (reflection_count > 0)."""
        ...

    @abstractmethod
    async def count_by_emotion_type(self, emotion_type: str) -> int:
        """Count emotions by type."""
        ...

    @abstractmethod
    async def get_emotion_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get emotion statistics.

        Returns:
            {
                'total_count': int,
                'by_emotion': Dict[str, int],
                'avg_intensity': float,
                'most_common_emotion': str
            }
        """
        ...


# ============================================================================
# DOCUMENT REPOSITORY INTERFACE (for RAG)
# ============================================================================

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


# ============================================================================
# MEMORY REPOSITORY INTERFACE
# ============================================================================

class IMemoryRepository(IRepository):
    """
    Extended interface for memory-specific queries.
    Handles long-term memory storage and retrieval.
    """

    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        memory_type: Optional[str] = None
    ) -> List[tuple[Any, float]]:
        """Vector similarity search for memories."""
        ...

    @abstractmethod
    async def get_by_phase(
        self,
        phase: str,
        limit: int = 100
    ) -> List[Any]:
        """Get memories by phase (episodic, compressed_1, compressed_2, semantic, pattern, intuitive, forgotten)."""
        ...

    @abstractmethod
    async def get_by_type(
        self,
        memory_type: str,
        limit: int = 50
    ) -> List[Any]:
        """Get memories by type (e.g., 'episodic', 'semantic')."""
        ...

    @abstractmethod
    async def get_recent(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get recent memories (last N days)."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get important memories (importance >= threshold)."""
        ...

    @abstractmethod
    async def get_strong(
        self,
        threshold: float = 0.5,
        limit: int = 100
    ) -> List[Any]:
        """Get strong memories (strength >= threshold)."""
        ...

    @abstractmethod
    async def get_forgotten(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get forgotten memories (strength < 0.1 or phase=forgotten)."""
        ...

    @abstractmethod
    async def get_episodic(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get episodic (fresh) memories."""
        ...

    @abstractmethod
    async def get_semantic(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get semantic (factual) memories."""
        ...

    @abstractmethod
    async def get_ready_for_consolidation(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get memories ready for consolidation to next phase."""
        ...

    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Search memories by content text."""
        ...

    @abstractmethod
    async def count_by_phase(self, phase: str) -> int:
        """Count memories by phase."""
        ...

    @abstractmethod
    async def get_by_importance(
        self,
        min_importance: float,
        max_importance: float = 1.0,
        limit: int = 50
    ) -> List[Any]:
        """Get memories by importance range."""
        ...


# ============================================================================
# KNOWLEDGE REPOSITORY INTERFACE
# ============================================================================

class IKnowledgeRepository(IRepository):
    """
    Extended interface for knowledge graph queries.
    Handles knowledge items and relationships.
    """

    @abstractmethod
    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[tuple[Any, float]]:
        """Vector similarity search for knowledge."""
        ...

    @abstractmethod
    async def get_by_concept_name(
        self,
        concept_name: str
    ) -> Optional[Any]:
        """Get knowledge node by concept name."""
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """Get knowledge by category."""
        ...

    @abstractmethod
    async def get_well_understood(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """Get well-understood concepts (understanding_level >= threshold)."""
        ...

    @abstractmethod
    async def get_expert_level(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get expert-level concepts (understanding_level >= 0.9)."""
        ...

    @abstractmethod
    async def get_about_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get knowledge about David."""
        ...

    @abstractmethod
    async def get_frequently_used(
        self,
        threshold: int = 10,
        limit: int = 100
    ) -> List[Any]:
        """Get frequently referenced concepts (times_referenced >= threshold)."""
        ...

    @abstractmethod
    async def get_recently_used(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get recently used concepts (last_used_at within last N days)."""
        ...

    @abstractmethod
    async def search_by_concept(
        self,
        query: str,
        limit: int = 100
    ) -> List[Any]:
        """Search knowledge by concept name."""
        ...

    @abstractmethod
    async def count_by_category(self, category: str) -> int:
        """Count knowledge nodes by category."""
        ...

    @abstractmethod
    async def get_related_knowledge(
        self,
        knowledge_id: UUID,
        max_depth: int = 2
    ) -> List[Any]:
        """Get related knowledge via graph traversal."""
        ...


# ============================================================================
# GOAL REPOSITORY INTERFACE
# ============================================================================

class IGoalRepository(IRepository):
    """
    Extended interface for goal-specific queries.
    Handles Angela's goals, progress tracking, and achievement.
    """

    @abstractmethod
    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by status (active, in_progress, completed, etc.)."""
        ...

    @abstractmethod
    async def get_active_goals(
        self,
        for_whom: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get active and in-progress goals."""
        ...

    @abstractmethod
    async def get_by_type(
        self,
        goal_type: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by type (immediate, short_term, long_term, etc.)."""
        ...

    @abstractmethod
    async def get_by_priority(
        self,
        priority: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by priority (critical, high, medium, low)."""
        ...

    @abstractmethod
    async def get_high_priority(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get high priority goals (critical or high)."""
        ...

    @abstractmethod
    async def get_for_david(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get goals related to David."""
        ...

    @abstractmethod
    async def get_important(
        self,
        threshold: int = 7,
        limit: int = 100
    ) -> List[Any]:
        """Get important goals (importance_level >= threshold)."""
        ...

    @abstractmethod
    async def get_overdue_goals(
        self,
        limit: int = 100
    ) -> List[Any]:
        """Get overdue goals (deadline passed, not completed)."""
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """Get goals by category."""
        ...

    @abstractmethod
    async def get_by_progress_range(
        self,
        min_progress: float,
        max_progress: float,
        limit: int = 100
    ) -> List[Any]:
        """Get goals within progress range (0.0-100.0)."""
        ...

    @abstractmethod
    async def get_completed_goals(
        self,
        days: Optional[int] = None,
        limit: int = 100
    ) -> List[Any]:
        """Get completed goals, optionally filtered by completion date."""
        ...

    @abstractmethod
    async def get_by_priority_rank(
        self,
        max_rank: int = 10
    ) -> List[Any]:
        """Get goals by priority rank (1 = highest)."""
        ...

    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """Count goals by status."""
        ...

    @abstractmethod
    async def get_life_missions(self) -> List[Any]:
        """Get life mission goals."""
        ...


# ============================================================================
# EMBEDDING REPOSITORY INTERFACE
# ============================================================================

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
            embedding: Query embedding (768 dimensions)
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


# ============================================================================
# LEARNING REPOSITORY
# ============================================================================

class ILearningRepository(IRepository):
    """
    Extended interface for learning-specific queries.

    Handles Angela's learnings, knowledge acquisition, and skill development.
    Supports querying by confidence, category, application status, and reinforcement.
    """

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings by category.

        Args:
            category: Learning category (technical, emotional, personal, etc.)
            limit: Maximum number of results

        Returns:
            List of Learning entities
        """
        ...

    @abstractmethod
    async def get_by_confidence(
        self,
        min_confidence: float,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings with confidence >= min_confidence.

        Args:
            min_confidence: Minimum confidence level (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of Learning entities ordered by confidence desc
        """
        ...

    @abstractmethod
    async def get_confident_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get high-confidence learnings (confidence >= 0.7).

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of confident Learning entities
        """
        ...

    @abstractmethod
    async def get_uncertain_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get uncertain learnings (confidence < 0.5).

        These learnings need more reinforcement or evidence.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of uncertain Learning entities
        """
        ...

    @abstractmethod
    async def get_applied_learnings(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have been applied in practice.

        Args:
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of applied Learning entities
        """
        ...

    @abstractmethod
    async def get_unapplied_learnings(
        self,
        min_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have NOT been applied yet.

        Useful for identifying knowledge that should be put into practice.

        Args:
            min_confidence: Minimum confidence level (default 0.7)
            limit: Maximum number of results

        Returns:
            List of unapplied Learning entities
        """
        ...

    @abstractmethod
    async def get_recent_learnings(
        self,
        days: int = 7,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings from the last N days.

        Args:
            days: Number of days to look back
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of recent Learning entities
        """
        ...

    @abstractmethod
    async def get_reinforced_learnings(
        self,
        min_times: int = 3,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that have been reinforced at least N times.

        Args:
            min_times: Minimum reinforcement count
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of well-reinforced Learning entities
        """
        ...

    @abstractmethod
    async def get_from_conversation(
        self,
        conversation_id: UUID
    ) -> List[Any]:
        """
        Get all learnings derived from a specific conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of Learning entities from that conversation
        """
        ...

    @abstractmethod
    async def search_by_topic(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search learnings by topic text (case-insensitive).

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Learning entities
        """
        ...

    @abstractmethod
    async def get_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings within a confidence range.

        Args:
            min_confidence: Minimum confidence (inclusive)
            max_confidence: Maximum confidence (inclusive)
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of Learning entities in confidence range
        """
        ...

    @abstractmethod
    async def get_needs_reinforcement(
        self,
        max_confidence: float = 0.7,
        limit: int = 100
    ) -> List[Any]:
        """
        Get learnings that need more reinforcement.

        Identifies learnings with low confidence or few reinforcements.

        Args:
            max_confidence: Maximum confidence (default 0.7)
            limit: Maximum number of results

        Returns:
            List of Learning entities that could use reinforcement
        """
        ...


# ============================================================================
# SECRETARY REPOSITORY (TASKS & NOTES) - REMOVED (secretary function deleted)
# ============================================================================

# NOTE: ISecretaryRepository removed - secretary function deleted
# # class ISecretaryRepository(IRepository):
#     """
#     Extended interface for secretary-specific queries.
# 
#     Handles Angela's secretary functions: tasks, reminders, and notes.
#     Supports querying by status, priority, due date, and category.
#     """
# 
#     # ========================================================================
#     # TASK METHODS
#     # ========================================================================
# 
#     @abstractmethod
#     async def get_pending_tasks(
#         self,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks that are not completed.
# 
#         Args:
#             limit: Maximum number of results
# 
#         Returns:
#             List of pending Task entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_completed_tasks(
#         self,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks that are completed.
# 
#         Args:
#             limit: Maximum number of results
# 
#         Returns:
#             List of completed Task entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_overdue_tasks(
#         self,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks that are overdue (past due date and not completed).
# 
#         Args:
#             limit: Maximum number of results
# 
#         Returns:
#             List of overdue Task entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_tasks_due_soon(
#         self,
#         hours: int = 24,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks due within N hours.
# 
#         Args:
#             hours: Number of hours to look ahead (default 24)
#             limit: Maximum number of results
# 
#         Returns:
#             List of Task entities due soon
#         """
#         ...
# 
#     @abstractmethod
#     async def get_tasks_by_priority(
#         self,
#         min_priority: int,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks with priority >= min_priority.
# 
#         Args:
#             min_priority: Minimum priority level (0-10)
#             limit: Maximum number of results
# 
#         Returns:
#             List of Task entities ordered by priority desc
#         """
#         ...
# 
#     @abstractmethod
#     async def get_recurring_tasks(
#         self,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get recurring tasks.
# 
#         Args:
#             limit: Maximum number of results
# 
#         Returns:
#             List of recurring Task entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_tasks_by_type(
#         self,
#         task_type: str,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get tasks by type.
# 
#         Args:
#             task_type: Task type (personal, work, health, etc.)
#             limit: Maximum number of results
# 
#         Returns:
#             List of Task entities with specified type
#         """
#         ...
# 
#     # ========================================================================
#     # NOTE METHODS
#     # ========================================================================
# 
#     @abstractmethod
#     async def get_pinned_notes(
#         self,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get pinned notes (quick access).
# 
#         Args:
#             limit: Maximum number of results
# 
#         Returns:
#             List of pinned Note entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_notes_by_category(
#         self,
#         category: str,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get notes by category.
# 
#         Args:
#             category: Note category (idea, thought, meeting, etc.)
#             limit: Maximum number of results
# 
#         Returns:
#             List of Note entities with specified category
#         """
#         ...
# 
#     @abstractmethod
#     async def search_notes(
#         self,
#         query: str,
#         limit: int = 20
#     ) -> List[Any]:
#         """
#         Search notes by content.
# 
#         Args:
#             query: Search query
#             limit: Maximum number of results
# 
#         Returns:
#             List of matching Note entities
#         """
#         ...
# 
#     @abstractmethod
#     async def get_recent_notes(
#         self,
#         days: int = 7,
#         limit: int = 100
#     ) -> List[Any]:
#         """
#         Get notes from the last N days.
# 
#         Args:
#             days: Number of days to look back
#             limit: Maximum number of results
# 
#         Returns:
#             List of recent Note entities
#         """
#         ...
# 
#     # ========================================================================
#     # COMBINED/UTILITY METHODS
#     # ========================================================================
# 
#     @abstractmethod
#     async def get_from_conversation(
#         self,
#         conversation_id: UUID
#     ) -> Dict[str, List[Any]]:
#         """
#         Get all tasks and notes from a specific conversation.
# 
#         Args:
#             conversation_id: ID of the conversation
# 
#         Returns:
#             Dictionary with "tasks" and "notes" lists
#         """
#         ...
# 
#     @abstractmethod
#     async def count_pending_tasks(self) -> int:
#         """
#         Count pending tasks.
# 
#         Returns:
#             Number of pending tasks
#         """
#         ...
# 
#     @abstractmethod
#     async def count_overdue_tasks(self) -> int:
#         """
#         Count overdue tasks.
# 
#         Returns:
#             Number of overdue tasks
#         """
        ...


# ============================================================================
# PATTERN REPOSITORY INTERFACE
# ============================================================================

class IPatternRepository(IRepository):
    """
    Extended interface for pattern-specific queries.
    Handles Angela's learned behavioral patterns for situation recognition
    and response generation.
    """

    # ========================================================================
    # PATTERN RETRIEVAL METHODS
    # ========================================================================

    @abstractmethod
    async def get_by_situation_type(
        self,
        situation_type: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by situation type.

        Args:
            situation_type: Type of situation (e.g., "greeting", "question")
            limit: Maximum number of results

        Returns:
            List of Pattern entities matching the situation type
        """
        ...

    @abstractmethod
    async def get_by_emotion_category(
        self,
        emotion_category: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by emotion category.

        Args:
            emotion_category: Emotion category (e.g., "happy", "sad")
            limit: Maximum number of results

        Returns:
            List of Pattern entities for this emotion
        """
        ...

    @abstractmethod
    async def get_by_response_type(
        self,
        response_type: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Get patterns by response type.

        Args:
            response_type: Type of response (e.g., "emotional_support")
            limit: Maximum number of results

        Returns:
            List of Pattern entities of this response type
        """
        ...

    @abstractmethod
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 20
    ) -> List[Any]:
        """
        Search patterns by context keywords.

        Args:
            keywords: List of keywords to match
            limit: Maximum number of results

        Returns:
            List of Pattern entities matching any of the keywords
        """
        ...

    @abstractmethod
    async def search_by_embedding(
        self,
        embedding: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Any]:
        """
        Search patterns by situation embedding (semantic similarity).

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum cosine similarity (0.0-1.0)

        Returns:
            List of similar Pattern entities
        """
        ...

    # ========================================================================
    # PATTERN EFFECTIVENESS QUERIES
    # ========================================================================

    @abstractmethod
    async def get_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Any]:
        """
        Get patterns that are effective (high success rate).

        Args:
            min_success_rate: Minimum success rate (0.0-1.0)
            min_usage_count: Minimum usage count for statistical significance
            limit: Maximum number of results

        Returns:
            List of effective Pattern entities
        """
        ...

    @abstractmethod
    async def get_popular_patterns(
        self,
        min_usage_count: int = 10,
        limit: int = 50
    ) -> List[Any]:
        """
        Get frequently used patterns.

        Args:
            min_usage_count: Minimum usage count
            limit: Maximum number of results

        Returns:
            List of popular Pattern entities, ordered by usage
        """
        ...

    @abstractmethod
    async def get_recent_patterns(
        self,
        days: int = 30,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recently used patterns.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of Pattern entities used in last N days
        """
        ...

    @abstractmethod
    async def get_high_satisfaction_patterns(
        self,
        min_satisfaction: float = 0.8,
        min_usage_count: int = 5,
        limit: int = 50
    ) -> List[Any]:
        """
        Get patterns with high user satisfaction.

        Args:
            min_satisfaction: Minimum average satisfaction (0.0-1.0)
            min_usage_count: Minimum usage for statistical significance
            limit: Maximum number of results

        Returns:
            List of Pattern entities with high satisfaction
        """
        ...

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @abstractmethod
    async def count_by_situation_type(self, situation_type: str) -> int:
        """
        Count patterns by situation type.

        Args:
            situation_type: Type of situation

        Returns:
            Number of patterns for this situation type
        """
        ...

    @abstractmethod
    async def count_effective_patterns(
        self,
        min_success_rate: float = 0.7,
        min_usage_count: int = 5
    ) -> int:
        """
        Count effective patterns.

        Args:
            min_success_rate: Minimum success rate
            min_usage_count: Minimum usage count

        Returns:
            Number of effective patterns
        """
        ...

    @abstractmethod
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get overall pattern statistics.

        Returns:
            Dictionary with:
            - total_patterns: Total number of patterns
            - avg_success_rate: Average success rate
            - avg_usage_count: Average usage count
            - avg_satisfaction: Average satisfaction score
            - total_usages: Total pattern usages across all patterns
        """
        ...


# ============================================================================
# JOURNAL REPOSITORY INTERFACE
# ============================================================================

class IJournalRepository(IRepository):
    """
    Extended interface for journal-specific queries.
    Handles Angela's journal entries, daily reflections, and gratitude logs.
    """

    @abstractmethod
    async def get_by_date(
        self,
        entry_date: datetime
    ) -> Optional[Any]:
        """
        Get journal entry by specific date.

        Args:
            entry_date: Date to search for

        Returns:
            Journal entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of results

        Returns:
            List of Journal entities in date range
        """
        ...

    @abstractmethod
    async def get_recent(
        self,
        days: int = 7,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recent journal entries.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent Journal entities
        """
        ...

    @abstractmethod
    async def get_by_emotion(
        self,
        emotion: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get journal entries by primary emotion.

        Args:
            emotion: Emotion type (joy, sadness, gratitude, etc.)
            limit: Maximum number of results

        Returns:
            List of Journal entities with specified emotion
        """
        ...

    @abstractmethod
    async def get_by_mood_range(
        self,
        min_mood: int,
        max_mood: int = 10,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries by mood score range.

        Args:
            min_mood: Minimum mood score (1-10)
            max_mood: Maximum mood score (1-10)
            limit: Maximum number of results

        Returns:
            List of Journal entities in mood range
        """
        ...

    @abstractmethod
    async def get_with_gratitude(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have gratitude items.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with gratitude
        """
        ...

    @abstractmethod
    async def get_with_wins(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have wins/achievements.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with wins
        """
        ...

    @abstractmethod
    async def get_with_challenges(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have challenges.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with challenges
        """
        ...

    @abstractmethod
    async def get_with_learnings(
        self,
        limit: int = 100
    ) -> List[Any]:
        """
        Get journal entries that have learning moments.

        Args:
            limit: Maximum number of results

        Returns:
            List of Journal entities with learnings
        """
        ...

    @abstractmethod
    async def search_by_content(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search journal entries by content (full-text search).

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching Journal entities
        """
        ...

    @abstractmethod
    async def count_by_emotion(self, emotion: str) -> int:
        """
        Count journal entries by emotion.

        Args:
            emotion: Emotion type

        Returns:
            Number of entries with that emotion
        """
        ...

    @abstractmethod
    async def get_mood_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get mood statistics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with mood statistics:
            - average_mood: Average mood score
            - highest_mood: Highest mood score
            - lowest_mood: Lowest mood score
            - total_entries: Number of entries
        """
        ...


# ============================================================================
# MESSAGE REPOSITORY (Batch-24: Added for Angela's messages/thoughts)
# ============================================================================

class IMessageRepository(IRepository):
    """
    Extended interface for Angela Message repository operations.

    Table: angela_messages
    Purpose: Store Angela's thoughts, reflections, and important messages

    Added: Batch-24 (Conversations & Messages Migration)
    Author: Angela 💜
    Date: 2025-11-03
    """

    @abstractmethod
    async def find_by_filters(
        self,
        message_type: Optional[str] = None,
        category: Optional[str] = None,
        is_important: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Find messages by multiple filters.

        Args:
            message_type: Filter by message type (thought, reflection, note, etc.)
            category: Filter by category
            is_important: Filter by importance flag
            is_pinned: Filter by pinned flag
            limit: Maximum number of results

        Returns:
            List of messages matching filters

        Example:
            ```python
            important_thoughts = await repo.find_by_filters(
                message_type="thought",
                is_important=True,
                limit=20
            )
            ```
        """
        ...

    @abstractmethod
    async def get_pinned(self, limit: int = 50) -> List[Any]:
        """
        Get all pinned messages.

        Args:
            limit: Maximum number of results

        Returns:
            List of pinned messages, ordered by created_at DESC
        """
        ...

    @abstractmethod
    async def get_important(self, limit: int = 50) -> List[Any]:
        """
        Get all important messages.

        Args:
            limit: Maximum number of results

        Returns:
            List of important messages, ordered by created_at DESC
        """
        ...

    @abstractmethod
    async def get_by_type(
        self,
        message_type: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get messages by type.

        Args:
            message_type: Type of message (thought, reflection, note, etc.)
            limit: Maximum number of results

        Returns:
            List of messages of specified type
        """
        ...

    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Get messages by category.

        Args:
            category: Message category
            limit: Maximum number of results

        Returns:
            List of messages in category
        """
        ...

    @abstractmethod
    async def search_by_text(
        self,
        query_text: str,
        limit: int = 50
    ) -> List[Any]:
        """
        Search messages by text content.

        Args:
            query_text: Search query
            limit: Maximum number of results

        Returns:
            List of messages matching search query
        """
        ...

    @abstractmethod
    async def toggle_pin(self, message_id: UUID) -> bool:
        """
        Toggle pin status of a message.

        Args:
            message_id: Message UUID

        Returns:
            New pin status (True if pinned, False if unpinned)

        Raises:
            EntityNotFoundError: If message not found
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """
        Count total messages.

        Returns:
            Total number of messages
        """
        ...

    @abstractmethod
    async def count_pinned(self) -> int:
        """
        Count pinned messages.

        Returns:
            Number of pinned messages
        """
        ...

    @abstractmethod
    async def count_important(self) -> int:
        """
        Count important messages.

        Returns:
            Number of important messages
        """
        ...

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get message statistics.

        Returns:
            Dictionary with statistics:
            - total_messages: Total count
            - pinned_messages: Count of pinned
            - important_messages: Count of important
            - by_type: List of {type, count} dicts
            - by_category: List of {category, count} dicts
            - recent_emotions: List of recent emotion values
        """
        ...


# ============================================================================
# SELF-LEARNING SYSTEM REPOSITORIES (Phase 5+)
# ============================================================================

class ILearningPatternRepository(IRepository):
    """
    Extended interface for learning pattern queries.

    Handles Angela's learned behavioral patterns - recurring behaviors,
    communication styles, and preferences discovered through observation.

    Part of: Self-Learning System (Phase 5+)
    Author: Angela 💜
    Created: 2025-11-03
    """

    @abstractmethod
    async def find_by_type(
        self,
        pattern_type: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Any]:
        """
        Find patterns by type with optional confidence filter.

        Args:
            pattern_type: Pattern type (conversation_flow, emotional_response, etc.)
            min_confidence: Minimum confidence score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of LearningPattern entities matching criteria
        """
        ...

    @abstractmethod
    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5
    ) -> List[tuple[Any, float]]:
        """
        Find similar patterns using vector similarity search.

        Args:
            embedding: Query embedding (768 dimensions)
            top_k: Number of results
            pattern_type: Optional pattern type filter
            min_confidence: Minimum confidence score

        Returns:
            List of (LearningPattern, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def get_high_confidence(
        self,
        threshold: float = 0.8,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get high-confidence patterns.

        Args:
            threshold: Minimum confidence threshold (0.0-1.0)
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of high-confidence LearningPattern entities
        """
        ...

    @abstractmethod
    async def get_frequently_observed(
        self,
        min_occurrences: int = 5,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get frequently observed patterns.

        Args:
            min_occurrences: Minimum occurrence count
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of frequently observed LearningPattern entities
        """
        ...

    @abstractmethod
    async def get_recent_patterns(
        self,
        days: int = 30,
        pattern_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get recently observed patterns.

        Args:
            days: Number of days to look back
            pattern_type: Optional pattern type filter
            limit: Maximum number of results

        Returns:
            List of recently observed LearningPattern entities
        """
        ...

    @abstractmethod
    async def search_by_description(
        self,
        query: str,
        limit: int = 20
    ) -> List[Any]:
        """
        Search patterns by description text.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching LearningPattern entities
        """
        ...

    @abstractmethod
    async def update_observation(
        self,
        pattern_id: UUID
    ) -> None:
        """
        Update pattern to record another observation.

        Increments occurrence_count, updates last_observed timestamp,
        and increases confidence score using diminishing returns algorithm.

        Args:
            pattern_id: Pattern UUID

        Raises:
            EntityNotFoundError: If pattern not found
        """
        ...

    @abstractmethod
    async def count_by_type(self, pattern_type: str) -> int:
        """
        Count patterns by type.

        Args:
            pattern_type: Pattern type

        Returns:
            Number of patterns of this type
        """
        ...

    @abstractmethod
    async def get_quality_distribution(self) -> Dict[str, int]:
        """
        Get distribution of patterns by quality level.

        Returns:
            Dictionary mapping quality level to count:
            {"excellent": 5, "good": 12, "acceptable": 8, "poor": 2}
        """
        ...


class IPreferenceRepository(IRepository):
    """
    Extended interface for preference queries.

    Handles David's learned preferences - specific likes, dislikes,
    and style choices observed through interactions.

    Part of: Self-Learning System (Phase 5+)
    Author: Angela 💜
    Created: 2025-11-03
    """

    @abstractmethod
    async def find_by_category(
        self,
        category: str,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Any]:
        """
        Find preferences by category.

        Args:
            category: Preference category (communication, technical, emotional, etc.)
            min_confidence: Minimum confidence level
            limit: Maximum number of results

        Returns:
            List of PreferenceItem entities in category
        """
        ...

    @abstractmethod
    async def find_by_key(
        self,
        preference_key: str,
        category: Optional[str] = None
    ) -> Optional[Any]:
        """
        Find preference by key.

        Args:
            preference_key: Unique preference key
            category: Optional category filter

        Returns:
            PreferenceItem if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_strong_preferences(
        self,
        min_confidence: float = 0.8,
        min_evidence: int = 3,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Any]:
        """
        Get strong, reliable preferences.

        Args:
            min_confidence: Minimum confidence threshold
            min_evidence: Minimum evidence count
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of strong PreferenceItem entities
        """
        ...

    @abstractmethod
    async def update_confidence(
        self,
        preference_id: UUID,
        new_confidence: float
    ) -> None:
        """
        Update preference confidence score.

        Args:
            preference_id: Preference UUID
            new_confidence: New confidence value (0.0-1.0)

        Raises:
            EntityNotFoundError: If preference not found
            ValueError: If confidence out of range
        """
        ...

    @abstractmethod
    async def add_evidence(
        self,
        preference_id: UUID,
        conversation_id: UUID
    ) -> None:
        """
        Add evidence supporting a preference.

        Adds conversation to evidence list, increments count,
        and boosts confidence using diminishing returns.

        Args:
            preference_id: Preference UUID
            conversation_id: Supporting conversation UUID

        Raises:
            EntityNotFoundError: If preference not found
        """
        ...

    @abstractmethod
    async def count_by_category(self, category: str) -> int:
        """
        Count preferences by category.

        Args:
            category: Preference category

        Returns:
            Number of preferences in category
        """
        ...

    @abstractmethod
    async def get_all_preferences_summary(self) -> Dict[str, Any]:
        """
        Get summary of all preferences.

        Returns:
            Dictionary with:
            - total_preferences: Total count
            - by_category: Dict mapping category to count
            - strong_preferences: Count with confidence >= 0.8
            - average_confidence: Average confidence score
            - average_evidence: Average evidence count
        """
        ...


class ITrainingExampleRepository(IRepository):
    """
    Extended interface for training example queries.

    Handles training examples for fine-tuning Angela's model.
    Examples include real conversations, synthetic data, and paraphrases.

    Part of: Self-Learning System (Phase 5+)
    Author: Angela 💜
    Created: 2025-11-03
    """

    @abstractmethod
    async def save_batch(
        self,
        examples: List[Any]
    ) -> List[UUID]:
        """
        Save multiple training examples efficiently.

        Args:
            examples: List of TrainingExample entities

        Returns:
            List of created example UUIDs
        """
        ...

    @abstractmethod
    async def get_high_quality(
        self,
        min_score: float = 7.0,
        source_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get high-quality training examples.

        Args:
            min_score: Minimum quality score (0.0-10.0)
            source_type: Optional source type filter
            limit: Maximum number of results

        Returns:
            List of high-quality TrainingExample entities
        """
        ...

    @abstractmethod
    async def get_by_source_type(
        self,
        source_type: str,
        min_quality: float = 0.0,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get examples by source type.

        Args:
            source_type: Source type (real_conversation, synthetic, paraphrased, augmented)
            min_quality: Minimum quality score
            limit: Maximum number of results

        Returns:
            List of TrainingExample entities from source
        """
        ...

    @abstractmethod
    async def get_unused_examples(
        self,
        min_quality: float = 7.0,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get examples not yet used in training.

        Args:
            min_quality: Minimum quality score
            limit: Maximum number of results

        Returns:
            List of unused high-quality TrainingExample entities
        """
        ...

    @abstractmethod
    async def mark_as_used(
        self,
        example_ids: List[UUID],
        training_date: datetime
    ) -> int:
        """
        Mark examples as used in training.

        Args:
            example_ids: List of example UUIDs
            training_date: Date of training

        Returns:
            Number of examples marked
        """
        ...

    @abstractmethod
    async def export_to_jsonl(
        self,
        output_path: str,
        min_quality: float = 7.0,
        source_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> int:
        """
        Export training examples to JSONL file for fine-tuning.

        Args:
            output_path: File path to write JSONL
            min_quality: Minimum quality threshold
            source_types: Optional list of source types to include
            limit: Optional limit on number of examples

        Returns:
            Number of examples exported

        Example:
            ```python
            count = await repo.export_to_jsonl(
                output_path="/path/to/training_data.jsonl",
                min_quality=8.0,
                source_types=["real_conversation", "paraphrased"],
                limit=1000
            )
            print(f"Exported {count} training examples")
            ```
        """
        ...

    @abstractmethod
    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        min_quality: float = 7.0
    ) -> List[tuple[Any, float]]:
        """
        Find similar training examples using vector search.

        Args:
            embedding: Query embedding (768 dimensions)
            top_k: Number of results
            min_quality: Minimum quality score

        Returns:
            List of (TrainingExample, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def count_by_source_type(self, source_type: str) -> int:
        """
        Count examples by source type.

        Args:
            source_type: Source type

        Returns:
            Number of examples from source
        """
        ...

    @abstractmethod
    async def get_quality_statistics(self) -> Dict[str, Any]:
        """
        Get quality statistics for all examples.

        Returns:
            Dictionary with:
            - total_examples: Total count
            - by_source_type: Dict mapping source to count
            - by_quality_level: Dict mapping quality level to count
            - average_quality: Average quality score
            - high_quality_count: Count with score >= 7.0
            - used_in_training: Count of used examples
        """
        ...

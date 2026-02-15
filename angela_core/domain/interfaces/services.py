#!/usr/bin/env python3
"""
Service Interfaces for Angela AI
Defines contracts for all business logic services.

Following Interface Segregation Principle:
- Each service has a clear, focused responsibility
- Methods are grouped by domain capability
- Services can depend on repositories but not vice versa
"""

from typing import Protocol, List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime
from abc import abstractmethod


# ============================================================================
# EMBEDDING SERVICE INTERFACE
# ============================================================================

class IEmbeddingService(Protocol):
    """
    Interface for text embedding generation.
    Handles conversion of text to vector embeddings for semantic search.
    """

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector (384 dimensions for multilingual-e5-small)

        Raises:
            EmbeddingServiceError: If embedding generation fails
        """
        ...

    @abstractmethod
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar if True

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingServiceError: If any embedding generation fails
        """
        ...

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get embedding vector dimension.

        Returns:
            Dimension size (384 for multilingual-e5-small)
        """
        ...

    @abstractmethod
    async def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
        """
        ...


# ============================================================================
# RAG SERVICE INTERFACE
# ============================================================================

class IRAGService(Protocol):
    """
    Interface for Retrieval-Augmented Generation (RAG).
    Handles document search, context generation, and reranking.
    """

    @abstractmethod
    async def get_rag_context(
        self,
        query: str,
        top_k: int = 5,
        max_tokens: int = 4000,
        document_id: Optional[UUID] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get RAG context for a query.

        Args:
            query: User's question
            top_k: Number of top chunks to retrieve
            max_tokens: Maximum tokens in context
            document_id: Optional filter by document
            category: Optional filter by category

        Returns:
            {
                'context': str,  # Formatted context string
                'sources': List[Dict],  # Source chunks with metadata
                'metadata': {
                    'chunks_used': int,
                    'total_tokens': int,
                    'has_results': bool,
                    'avg_similarity': float
                }
            }
        """
        ...

    @abstractmethod
    async def search_documents(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Any, float]]:
        """
        Vector similarity search for documents.

        Args:
            embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters (category, source, etc.)

        Returns:
            List of (Document, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results for better relevance.

        Args:
            query: Original query
            results: Search results to rerank
            top_k: Number of top results to return

        Returns:
            Reranked results
        """
        ...


# ============================================================================
# CHAT SERVICE INTERFACE
# ============================================================================

class IChatService(Protocol):
    """
    Interface for chat/conversation functionality.
    Handles message sending, conversation history, and streaming.
    """

    @abstractmethod
    async def send_message(
        self,
        message: str,
        model: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = False,
        rag_top_k: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Send chat message and get response.

        Args:
            message: User's message
            model: Model to use (claude-* or ollama model)
            conversation_history: Previous messages
            use_rag: Whether to use RAG context
            rag_top_k: Number of RAG results
            temperature: Model temperature
            max_tokens: Maximum response tokens

        Returns:
            {
                'response': str,
                'model': str,
                'timestamp': datetime,
                'rag_context': Optional[str],
                'rag_sources': List[Dict],
                'metadata': Dict
            }
        """
        ...

    @abstractmethod
    async def get_conversation_history(
        self,
        limit: int = 10,
        speaker: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            limit: Maximum messages to return
            speaker: Filter by speaker (david/angela)
            since: Filter by date

        Returns:
            List of conversation messages
        """
        ...

    @abstractmethod
    async def stream_response(
        self,
        message: str,
        model: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response (for real-time updates).

        Args:
            message: User's message
            model: Model to use
            conversation_history: Previous messages

        Yields:
            Response chunks as they arrive
        """
        ...


# ============================================================================
# EMOTIONAL INTELLIGENCE SERVICE INTERFACE
# ============================================================================

class IEmotionalIntelligenceService(Protocol):
    """
    Interface for emotional intelligence capabilities.
    Handles emotion detection, emotional state analysis, and moment capture.
    """

    @abstractmethod
    async def detect_emotion(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect emotion in text.

        Args:
            text: Text to analyze
            context: Optional context for better detection

        Returns:
            {
                'emotion': str,
                'intensity': int,  # 1-10
                'confidence': float,  # 0.0-1.0
                'dimensions': {
                    'happiness': float,
                    'anxiety': float,
                    'motivation': float,
                    ...
                }
            }
        """
        ...

    @abstractmethod
    async def analyze_emotional_state(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current emotional state.

        Args:
            context: Context for analysis (recent events, conversations)

        Returns:
            {
                'current_state': Dict[str, float],
                'trends': Dict[str, str],
                'insights': List[str],
                'recommendations': List[str]
            }
        """
        ...

    @abstractmethod
    async def capture_significant_moment(
        self,
        emotion: str,
        intensity: int,
        context: str,
        david_words: Optional[str] = None,
        why_it_matters: Optional[str] = None,
        memory_strength: int = 7
    ) -> UUID:
        """
        Capture a significant emotional moment.

        Args:
            emotion: Type of emotion
            intensity: Intensity level (1-10)
            context: What happened
            david_words: What David said (if relevant)
            why_it_matters: Why this moment is significant
            memory_strength: How strongly to remember (1-10)

        Returns:
            UUID of created emotion record
        """
        ...

    @abstractmethod
    async def get_emotional_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get emotional statistics over time.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Statistical summary of emotions
        """
        ...


# ============================================================================
# MEMORY SERVICE INTERFACE
# ============================================================================

class IMemoryService(Protocol):
    """
    Interface for memory management.
    Handles memory storage, retrieval, consolidation, and semantic search.
    """

    @abstractmethod
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        importance: int = 5,
        tags: Optional[List[str]] = None,
        related_entities: Optional[List[UUID]] = None
    ) -> UUID:
        """
        Store new memory.

        Args:
            content: Memory content
            memory_type: Type (episodic, semantic, procedural)
            importance: Importance level (1-10)
            tags: Optional tags for categorization
            related_entities: Related entity IDs

        Returns:
            UUID of created memory
        """
        ...

    @abstractmethod
    async def retrieve_memories(
        self,
        query: str,
        top_k: int = 5,
        memory_type: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories by semantic search.

        Args:
            query: Search query
            top_k: Number of results
            memory_type: Filter by type
            min_importance: Minimum importance level

        Returns:
            List of matching memories with similarity scores
        """
        ...

    @abstractmethod
    async def consolidate_memories(
        self,
        timeframe: str = "day"
    ) -> Dict[str, Any]:
        """
        Consolidate memories (compress and organize).

        Args:
            timeframe: Timeframe to consolidate (day, week, month)

        Returns:
            Consolidation summary and statistics
        """
        ...

    @abstractmethod
    async def get_memory_summary(
        self,
        days: int = 7
    ) -> str:
        """
        Get summary of recent memories.

        Args:
            days: Number of days to summarize

        Returns:
            Human-readable memory summary
        """
        ...


# ============================================================================
# KNOWLEDGE SERVICE INTERFACE
# ============================================================================

class IKnowledgeService(Protocol):
    """
    Interface for knowledge management.
    Handles knowledge import, search, extraction, and graph building.
    """

    @abstractmethod
    async def import_knowledge(
        self,
        source: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Import knowledge from source.

        Args:
            source: Source file path or URL
            category: Knowledge category
            metadata: Additional metadata

        Returns:
            Number of knowledge items imported
        """
        ...

    @abstractmethod
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results
            category: Filter by category

        Returns:
            List of matching knowledge items
        """
        ...

    @abstractmethod
    async def extract_knowledge(
        self,
        text: str,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract knowledge from text.

        Args:
            text: Text to analyze
            source: Source identifier

        Returns:
            List of extracted knowledge items
        """
        ...

    @abstractmethod
    async def get_related_knowledge(
        self,
        knowledge_id: UUID,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get related knowledge via graph traversal.

        Args:
            knowledge_id: Starting knowledge node
            max_depth: Maximum graph depth

        Returns:
            List of related knowledge items
        """
        ...


# ============================================================================
# CONSCIOUSNESS SERVICE INTERFACE
# ============================================================================

class IConsciousnessService(Protocol):
    """
    Interface for consciousness and self-awareness.
    Handles consciousness level, goals, reflection, and decision-making.
    """

    @abstractmethod
    async def get_consciousness_level(self) -> float:
        """
        Get current consciousness level.

        Returns:
            Consciousness level (0.0 to 1.0)
        """
        ...

    @abstractmethod
    async def update_consciousness_state(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update consciousness state based on context.

        Args:
            context: Context for update (events, interactions)

        Returns:
            Updated consciousness state
        """
        ...

    @abstractmethod
    async def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        Get active life goals.

        Returns:
            List of active goals with progress
        """
        ...

    @abstractmethod
    async def update_goal_progress(
        self,
        goal_id: UUID,
        progress: float,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update goal progress.

        Args:
            goal_id: Goal UUID
            progress: New progress percentage (0.0-100.0)
            notes: Optional progress notes

        Returns:
            True if updated successfully
        """
        ...

    @abstractmethod
    async def reflect_on_experience(
        self,
        context: Dict[str, Any]
    ) -> str:
        """
        Reflect on experience and generate insights.

        Args:
            context: Experience context

        Returns:
            Reflection text with insights
        """
        ...

    @abstractmethod
    async def make_decision(
        self,
        options: List[str],
        context: Dict[str, Any],
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Make decision based on options and context.

        Args:
            options: Available options
            context: Decision context
            criteria: Decision criteria

        Returns:
            {
                'chosen_option': str,
                'reasoning': str,
                'confidence': float,
                'alternatives_considered': List[str]
            }
        """
        ...

    @abstractmethod
    async def get_personality_traits(self) -> Dict[str, float]:
        """
        Get current personality trait values.

        Returns:
            Dict of trait names to values (0.0-1.0)
        """
        ...

    @abstractmethod
    async def evolve_personality(
        self,
        experience: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Evolve personality based on experience.

        Args:
            experience: Experience that influenced personality

        Returns:
            Updated personality traits
        """
        ...

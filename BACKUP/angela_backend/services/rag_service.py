#!/usr/bin/env python3
"""
RAG Service - Retrieval-Augmented Generation for AngelaNova

This service retrieves relevant context from AngelaMemory database
to enhance chat responses with semantic understanding.
"""

import asyncpg
from typing import List, Dict, Any, Optional
import httpx

# Database connection
DATABASE_URL = "postgresql://davidsamanyaporn@localhost:5432/AngelaMemory"

# Ollama for embeddings
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"


class RAGService:
    """
    Retrieval-Augmented Generation Service

    Provides semantic search across Angela's memory to retrieve
    relevant context for generating intelligent responses.
    """

    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        """Connect to AngelaMemory database"""
        if not self.conn:
            self.conn = await asyncpg.connect(DATABASE_URL)

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Ollama

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/embeddings",
                    json={
                        "model": EMBEDDING_MODEL,
                        "prompt": text
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("embedding", [])
                else:
                    print(f"⚠️ Ollama embedding error: {response.status_code}")
                    return []
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return []

    async def search_similar_conversations(
        self,
        query: str,
        limit: int = 5,
        importance_threshold: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar conversations using vector similarity

        Args:
            query: User's message/query
            limit: Maximum number of results
            importance_threshold: Minimum importance level (1-10)

        Returns:
            List of similar conversations with context
        """
        await self.connect()

        # Generate embedding for query
        query_embedding = await self.generate_embedding(query)
        if not query_embedding:
            return []

        # Convert to PostgreSQL vector format
        emb_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Search using cosine distance (pgvector)
        query_sql = """
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                sentiment_label,
                importance_level,
                created_at,
                (1 - (embedding <=> $1::vector)) as similarity
            FROM conversations
            WHERE importance_level >= $2
            AND embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """

        rows = await self.conn.fetch(query_sql, emb_str, importance_threshold, limit)

        results = []
        for row in rows:
            results.append({
                'conversation_id': str(row['conversation_id']),
                'speaker': row['speaker'],
                'message': row['message_text'],
                'topic': row['topic'],
                'emotion': row['emotion_detected'],
                'sentiment': row['sentiment_label'],
                'importance': row['importance_level'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'similarity': float(row['similarity'])
            })

        return results

    async def search_emotions(
        self,
        query: str,
        limit: int = 3,
        intensity_threshold: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar emotional moments

        Args:
            query: User's message/query
            limit: Maximum number of results
            intensity_threshold: Minimum intensity (1-10)

        Returns:
            List of similar emotional moments
        """
        await self.connect()

        # Generate embedding for query
        query_embedding = await self.generate_embedding(query)
        if not query_embedding:
            return []

        emb_str = '[' + ','.join(map(str, query_embedding)) + ']'

        query_sql = """
            SELECT
                emotion_id,
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters,
                memory_strength,
                felt_at,
                (1 - (embedding <=> $1::vector)) as similarity
            FROM angela_emotions
            WHERE intensity >= $2
            AND embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """

        rows = await self.conn.fetch(query_sql, emb_str, intensity_threshold, limit)

        results = []
        for row in rows:
            results.append({
                'emotion_id': str(row['emotion_id']),
                'emotion': row['emotion'],
                'intensity': row['intensity'],
                'context': row['context'],
                'david_words': row['david_words'],
                'why_it_matters': row['why_it_matters'],
                'memory_strength': row['memory_strength'],
                'felt_at': row['felt_at'].isoformat() if row['felt_at'] else None,
                'similarity': float(row['similarity'])
            })

        return results

    async def search_learnings(
        self,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant learnings

        Args:
            query: User's message/query
            limit: Maximum number of results

        Returns:
            List of relevant learnings
        """
        await self.connect()

        # Generate embedding for query
        query_embedding = await self.generate_embedding(query)
        if not query_embedding:
            return []

        emb_str = '[' + ','.join(map(str, query_embedding)) + ']'

        query_sql = """
            SELECT
                learning_id,
                topic,
                category,
                insight,
                confidence_level,
                times_reinforced,
                created_at,
                (1 - (embedding <=> $1::vector)) as similarity
            FROM learnings
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """

        rows = await self.conn.fetch(query_sql, emb_str, limit)

        results = []
        for row in rows:
            results.append({
                'learning_id': str(row['learning_id']),
                'topic': row['topic'],
                'category': row['category'],
                'insight': row['insight'],
                'confidence_level': float(row['confidence_level']),
                'times_reinforced': row['times_reinforced'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'similarity': float(row['similarity'])
            })

        return results

    async def get_david_preferences(self) -> Dict[str, Any]:
        """
        Get David's preferences and personality traits

        Returns:
            Dictionary of David's preferences
        """
        await self.connect()

        query_sql = """
            SELECT
                preference_key,
                preference_value,
                confidence_level,
                created_at
            FROM david_preferences
            WHERE confidence_level >= 0.7
            ORDER BY confidence_level DESC, created_at DESC
        """

        rows = await self.conn.fetch(query_sql)

        preferences = {}
        for row in rows:
            preferences[row['preference_key']] = {
                'value': row['preference_value'],
                'confidence': float(row['confidence_level']),
                'created_at': row['created_at'].isoformat() if row['created_at'] else None
            }

        return preferences

    async def get_current_emotional_state(self) -> Optional[Dict[str, Any]]:
        """
        Get Angela's current emotional state

        Returns:
            Current emotional state or None
        """
        await self.connect()

        query_sql = """
            SELECT
                happiness,
                confidence,
                anxiety,
                motivation,
                gratitude,
                loneliness,
                triggered_by,
                emotion_note,
                created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """

        row = await self.conn.fetchrow(query_sql)

        if not row:
            return None

        return {
            'happiness': float(row['happiness']),
            'confidence': float(row['confidence']),
            'anxiety': float(row['anxiety']),
            'motivation': float(row['motivation']),
            'gratitude': float(row['gratitude']),
            'loneliness': float(row['loneliness']),
            'triggered_by': row['triggered_by'],
            'emotion_note': row['emotion_note'],
            'created_at': row['created_at'].isoformat() if row['created_at'] else None
        }

    async def get_calendar_events(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Get calendar events if user is asking about calendar

        Args:
            user_message: User's message

        Returns:
            Calendar events data or None
        """
        from angela_core.services.macos_calendar_service import calendar_service

        if not calendar_service:
            return None

        msg_lower = user_message.lower()

        # Check if asking about calendar
        calendar_keywords = [
            'calendar', 'ปฏิทิน', 'meeting', 'นัด', 'appointment',
            'event', 'วันนี้', 'today', 'tomorrow', 'พรุ่งนี้',
            'อาทิตย์หน้า', 'next week', 'สัปดาห์หน้า',
            'อาทิตย์นี้', 'this week'
        ]

        if not any(keyword in msg_lower for keyword in calendar_keywords):
            return None

        try:
            # Determine what to query
            if any(k in msg_lower for k in ['อาทิตย์หน้า', 'next week', 'สัปดาห์หน้า']):
                return calendar_service.get_events_for_week(week_offset=1)
            elif any(k in msg_lower for k in ['อาทิตย์นี้', 'this week']):
                return calendar_service.get_events_for_week(week_offset=0)
            elif any(k in msg_lower for k in ['วันนี้', 'today']):
                return calendar_service.get_today_events()
            elif any(k in msg_lower for k in ['พรุ่งนี้', 'tomorrow']):
                return calendar_service.get_upcoming_events(days=1)
            else:
                # Default to upcoming week
                return calendar_service.get_upcoming_events(days=7)

        except Exception as e:
            print(f"⚠️ Failed to get calendar events: {e}")
            return None

    async def retrieve_context(
        self,
        user_message: str,
        conversation_limit: int = 5,
        emotion_limit: int = 2,
        learning_limit: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve all relevant context for a user message

        This is the main RAG function that combines multiple searches.

        Args:
            user_message: User's message to find context for
            conversation_limit: Number of similar conversations
            emotion_limit: Number of similar emotions
            learning_limit: Number of similar learnings

        Returns:
            Dictionary with all retrieved context
        """
        await self.connect()

        # Parallel search for efficiency
        conversations = await self.search_similar_conversations(
            user_message,
            limit=conversation_limit
        )

        emotions = await self.search_emotions(
            user_message,
            limit=emotion_limit
        )

        learnings = await self.search_learnings(
            user_message,
            limit=learning_limit
        )

        preferences = await self.get_david_preferences()
        emotional_state = await self.get_current_emotional_state()

        # Get calendar events if asking about calendar
        calendar_events = await self.get_calendar_events(user_message)

        return {
            'similar_conversations': conversations,
            'related_emotions': emotions,
            'relevant_learnings': learnings,
            'david_preferences': preferences,
            'angela_emotional_state': emotional_state,
            'calendar_events': calendar_events,
            'query': user_message
        }


# Singleton instance
rag_service = RAGService()

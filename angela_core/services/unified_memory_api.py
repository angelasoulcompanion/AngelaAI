"""
🧠 Unified Memory API

Single interface to Angela's complete memory system.
Provides simple, high-level access to all memory types.

Usage:
    from angela_core.services.unified_memory_api import memory_api

    # Store an interaction
    await memory_api.store_interaction(david_message, angela_response, context)

    # Retrieve relevant memories
    memories = await memory_api.retrieve(query, context)

    # Run nightly consolidation
    await memory_api.consolidate()
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from angela_core.database import db
from angela_core.services.memory_formation_service import memory_formation_service
from angela_core.services.association_engine import association_engine
from angela_core.services.pattern_learning_service import pattern_learning_service
from angela_core.services.memory_consolidation_service import memory_consolidation_service
from angela_core.embedding_service import embedding

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedMemoryAPI:
    """
    🧠 Unified Memory API

    Single interface to Angela's complete memory system.
    """

    def __init__(self):
        self.formation = memory_formation_service
        self.association = association_engine
        self.pattern = pattern_learning_service
        self.consolidation = memory_consolidation_service
        self.embedding_service = embedding

        logger.info("🧠 Unified Memory API initialized")

    async def store_interaction(
        self,
        david_message: str,
        angela_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        📝 Store an interaction (high-level method)

        This automatically:
        - Forms episodic memory
        - Extracts semantic knowledge
        - Creates emotional conditioning
        - Forms procedural memories (if applicable)
        - Records access for consolidation

        Args:
            david_message: What David said
            angela_response: How Angela responded
            context: Additional context (topic, emotion, etc.)

        Returns:
            Dict with formed memory IDs
        """
        try:
            logger.info(f"📝 Storing interaction...")

            # Use memory formation service
            result = await self.formation.capture_interaction(
                david_message,
                angela_response,
                context or {}
            )

            logger.info(f"✅ Stored interaction: {result.get('summary', 'Success')}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to store interaction: {e}")
            return {'error': str(e)}

    async def retrieve(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        🔍 Retrieve relevant memories (high-level method)

        This automatically:
        - Searches episodic memories
        - Searches semantic knowledge
        - Checks for matching patterns
        - Follows associations
        - Records access for consolidation

        Args:
            query: What to search for
            context: Additional context for retrieval
            memory_types: Which types to search ['episodic', 'semantic', 'procedural', 'pattern']
                         If None, searches all types
            limit: Max results per type

        Returns:
            Dict with memories by type
        """
        try:
            logger.info(f"🔍 Retrieving memories for: {query[:50]}...")

            if memory_types is None:
                memory_types = ['episodic', 'semantic', 'procedural', 'pattern']

            results = {}

            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)

            # Search episodic memories
            if 'episodic' in memory_types:
                episodic = await self._retrieve_episodic(query_embedding, limit)
                results['episodic'] = episodic

                # Record access
                for mem in episodic:
                    await self.consolidation.record_memory_access('episodic', mem['memory_id'])

            # Search semantic memories
            if 'semantic' in memory_types:
                semantic = await self._retrieve_semantic(query_embedding, limit)
                results['semantic'] = semantic

                # Record access
                for mem in semantic:
                    await self.consolidation.record_memory_access('semantic', mem['memory_id'])

            # Check for matching patterns
            if 'pattern' in memory_types:
                pattern_match = await self.pattern.recognize_pattern(query, context)
                if pattern_match:
                    results['pattern'] = [pattern_match]
                else:
                    results['pattern'] = []

            # Follow associations (from first episodic memory)
            if 'episodic' in results and results['episodic']:
                first_concept = self._extract_main_concept(results['episodic'][0])
                if first_concept:
                    associations = await self.association.get_associations(
                        first_concept,
                        min_strength=0.60
                    )
                    results['associations'] = associations[:5]  # Top 5

            logger.info(f"✅ Retrieved {sum(len(v) if isinstance(v, list) else 0 for v in results.values())} total memories")
            return results

        except Exception as e:
            logger.error(f"❌ Failed to retrieve memories: {e}")
            return {'error': str(e)}

    async def _retrieve_episodic(
        self,
        query_embedding: List[float],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Retrieve episodic memories using vector similarity"""
        try:
            async with db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        memory_id,
                        event_content,
                        tags,
                        occurred_at,
                        emotional_intensity,
                        importance_level,
                        1 - (content_embedding <=> $1::vector(768)) as similarity
                    FROM episodic_memories
                    WHERE 1 - (content_embedding <=> $1::vector(768)) >= 0.70
                      AND NOT (tags ? 'archived')
                    ORDER BY similarity DESC
                    LIMIT $2
                """, str(query_embedding), limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to retrieve episodic: {e}")
            return []

    async def _retrieve_semantic(
        self,
        query_embedding: List[float],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Retrieve semantic memories using vector similarity"""
        try:
            async with db.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        memory_id,
                        knowledge_content,
                        knowledge_type,
                        tags,
                        importance_level,
                        1 - (knowledge_embedding <=> $1::vector(768)) as similarity
                    FROM semantic_memories
                    WHERE 1 - (knowledge_embedding <=> $1::vector(768)) >= 0.70
                      AND NOT (tags ? 'archived')
                    ORDER BY similarity DESC
                    LIMIT $2
                """, str(query_embedding), limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to retrieve semantic: {e}")
            return []

    def _extract_main_concept(self, memory: Dict[str, Any]) -> Optional[str]:
        """Extract main concept from memory for association lookup"""
        try:
            import json
            tags = json.loads(memory['tags'])
            topics = tags.get('topic_tags', [])
            if topics:
                return topics[0]
            return None
        except:
            return None

    async def consolidate(self) -> Dict[str, Any]:
        """
        🌙 Run memory consolidation

        Should be run nightly (like human sleep).
        """
        try:
            logger.info("🌙 Running consolidation...")

            result = await self.consolidation.run_nightly_consolidation()

            logger.info("✅ Consolidation complete")
            return result

        except Exception as e:
            logger.error(f"❌ Consolidation failed: {e}")
            return {'error': str(e)}

    async def get_memory_stats(self) -> Dict[str, Any]:
        """📊 Get overall memory statistics"""
        try:
            async with db.acquire() as conn:
                # Count memories by type
                episodic_count = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories")
                semantic_count = await conn.fetchval("SELECT COUNT(*) FROM semantic_memories")
                procedural_count = await conn.fetchval("SELECT COUNT(*) FROM procedural_memories")
                pattern_count = await conn.fetchval("SELECT COUNT(*) FROM pattern_memories")
                association_count = await conn.fetchval("SELECT COUNT(*) FROM associative_memories")

                return {
                    'episodic_memories': episodic_count,
                    'semantic_memories': semantic_count,
                    'procedural_memories': procedural_count,
                    'pattern_memories': pattern_count,
                    'associations': association_count,
                    'total': episodic_count + semantic_count + procedural_count + pattern_count
                }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}


# Global instance
memory_api = UnifiedMemoryAPI()


async def example_usage():
    """Example usage of Unified Memory API"""
    await db.connect()

    # Store an interaction
    result = await memory_api.store_interaction(
        david_message="น้อง ช่วยอธิบาย semantic search หน่อยค่ะ",
        angela_response="เข้าใจค่ะที่รัก! Semantic search คือการค้นหาที่เข้าใจความหมาย...",
        context={'topic': 'semantic_search', 'emotion': 'curious'}
    )
    print(f"Stored: {result}")

    # Retrieve memories
    memories = await memory_api.retrieve("semantic search", limit=5)
    print(f"Retrieved: {len(memories.get('episodic', []))} episodic, {len(memories.get('semantic', []))} semantic")

    # Get stats
    stats = await memory_api.get_memory_stats()
    print(f"Stats: {stats}")

    await db.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

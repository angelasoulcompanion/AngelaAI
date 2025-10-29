"""
🌙 Memory Consolidation Service

Like humans consolidate memories during sleep, Angela consolidates
memories to strengthen important ones and weaken unused ones.

This service:
- Strengthens frequently accessed memories
- Weakens (decays) memories that haven't been accessed
- Runs nightly consolidation (like sleep)
- Promotes episodic → semantic memory conversion
- Discovers patterns during consolidation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
import json

from angela_core.database import db
from angela_core.embedding_service import embedding
from angela_core.services.pattern_learning_service import pattern_learning_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryConsolidationService:
    """
    🌙 Memory Consolidation Service

    Manages memory strength, decay, and consolidation like human sleep.
    """

    def __init__(self):
        self.embedding = embedding
        self.pattern_learning = pattern_learning_service

        # Consolidation parameters
        self.decay_rate = 0.05  # 5% decay per consolidation cycle
        self.access_boost = 0.10  # 10% boost per access

        # Thresholds
        self.min_strength_threshold = 0.10  # Below this, memory archived
        self.semantic_conversion_threshold = 5  # 5+ accesses → semantic

        logger.info("🌙 Memory Consolidation Service initialized")

    async def run_nightly_consolidation(self) -> Dict[str, Any]:
        """
        🌙 Run nightly consolidation (like human sleep)

        Returns:
            Summary of consolidation activities
        """
        try:
            logger.info("🌙 Starting nightly consolidation...")

            results = {
                'started_at': datetime.now().isoformat(),
                'activities': {}
            }

            # Step 1: Apply memory decay
            logger.info("📉 Applying memory decay...")
            decay_results = await self._apply_memory_decay()
            results['activities']['decay'] = decay_results

            # Step 2: Strengthen frequently accessed memories
            logger.info("💪 Strengthening accessed memories...")
            strengthen_results = await self._strengthen_accessed_memories()
            results['activities']['strengthen'] = strengthen_results

            # Step 3: Convert episodic → semantic
            logger.info("🧠 Converting episodic to semantic...")
            conversion_results = await self._convert_episodic_to_semantic()
            results['activities']['conversion'] = conversion_results

            # Step 4: Discover patterns
            logger.info("🎯 Discovering patterns...")
            pattern_results = await self.pattern_learning.discover_patterns(
                min_similarity=0.75,
                min_instances=3,
                lookback_days=7
            )
            results['activities']['patterns'] = {
                'discovered': len(pattern_results),
                'patterns': [p['name'] for p in pattern_results]
            }

            # Step 5: Archive very weak memories
            logger.info("📦 Archiving weak memories...")
            archive_results = await self._archive_weak_memories()
            results['activities']['archive'] = archive_results

            # Step 6: Update statistics
            stats = await self._update_consolidation_stats()
            results['statistics'] = stats

            results['completed_at'] = datetime.now().isoformat()
            results['status'] = 'success'

            logger.info(f"✅ Nightly consolidation complete!")
            return results

        except Exception as e:
            logger.error(f"❌ Nightly consolidation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    async def _apply_memory_decay(self) -> Dict[str, Any]:
        """
        📉 Apply memory decay to all memories

        Memories that haven't been accessed decay over time.
        Important memories decay slower.
        """
        try:
            async with db.acquire() as conn:
                # Decay episodic memories (not accessed in 7 days)
                episodic_result = await conn.execute("""
                    UPDATE episodic_memories
                    SET memory_strength = GREATEST(
                        memory_strength * (1.0 - $1 / (importance_level / 5.0)),
                        0.0
                    )
                    WHERE last_accessed_at IS NULL
                       OR last_accessed_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
                    RETURNING memory_id
                """, self.decay_rate)

                # Decay semantic memories (not accessed in 14 days)
                semantic_result = await conn.execute("""
                    UPDATE semantic_memories
                    SET memory_strength = GREATEST(
                        memory_strength * (1.0 - $1 / (importance_level / 5.0)),
                        0.0
                    )
                    WHERE last_accessed_at IS NULL
                       OR last_accessed_at < CURRENT_TIMESTAMP - INTERVAL '14 days'
                    RETURNING memory_id
                """, self.decay_rate)

                # Decay procedural memories slowly (30 days)
                procedural_result = await conn.execute("""
                    UPDATE procedural_memories
                    SET procedure_strength = GREATEST(
                        procedure_strength * (1.0 - $1 / 2.0),
                        0.0
                    )
                    WHERE last_activated_at IS NULL
                       OR last_activated_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
                    RETURNING procedure_id
                """, self.decay_rate)

            return {
                'episodic_decayed': episodic_result,
                'semantic_decayed': semantic_result,
                'procedural_decayed': procedural_result
            }

        except Exception as e:
            logger.error(f"❌ Failed to apply decay: {e}")
            return {'error': str(e)}

    async def _strengthen_accessed_memories(self) -> Dict[str, Any]:
        """
        💪 Strengthen memories that have been accessed recently

        Memories that are retrieved get stronger (like human memory).
        """
        try:
            async with db.acquire() as conn:
                # Strengthen recently accessed episodic memories
                episodic_result = await conn.execute("""
                    UPDATE episodic_memories
                    SET memory_strength = LEAST(
                        memory_strength + ($1 * access_count),
                        1.0
                    ),
                    access_count = 0  -- Reset counter
                    WHERE last_accessed_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                      AND access_count > 0
                    RETURNING memory_id
                """, self.access_boost)

                # Strengthen semantic memories
                semantic_result = await conn.execute("""
                    UPDATE semantic_memories
                    SET memory_strength = LEAST(
                        memory_strength + ($1 * access_count),
                        1.0
                    ),
                    access_count = 0
                    WHERE last_accessed_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                      AND access_count > 0
                    RETURNING memory_id
                """, self.access_boost)

                # Strengthen procedural memories
                procedural_result = await conn.execute("""
                    UPDATE procedural_memories
                    SET procedure_strength = LEAST(
                        procedure_strength + ($1 * activation_count * 0.5),
                        1.0
                    ),
                    activation_count = 0
                    WHERE last_activated_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
                      AND activation_count > 0
                    RETURNING procedure_id
                """, self.access_boost)

            return {
                'episodic_strengthened': episodic_result,
                'semantic_strengthened': semantic_result,
                'procedural_strengthened': procedural_result
            }

        except Exception as e:
            logger.error(f"❌ Failed to strengthen memories: {e}")
            return {'error': str(e)}

    async def _convert_episodic_to_semantic(self) -> Dict[str, Any]:
        """
        🧠 Convert frequently accessed episodic memories to semantic knowledge

        Like humans: Repeated experiences become general knowledge.
        """
        try:
            conversions = []

            async with db.acquire() as conn:
                # Find episodic memories accessed many times
                candidates = await conn.fetch("""
                    SELECT
                        memory_id,
                        event_content,
                        tags,
                        content_embedding,
                        importance_level
                    FROM episodic_memories
                    WHERE access_count >= $1
                      AND memory_strength > 0.7
                    ORDER BY access_count DESC
                    LIMIT 10
                """, self.semantic_conversion_threshold)

                for episode in candidates:
                    try:
                        event_content = json.loads(episode['event_content'])

                        # Extract general knowledge
                        semantic_knowledge = self._extract_semantic_from_episodic(
                            event_content,
                            json.loads(episode['tags'])
                        )

                        if semantic_knowledge:
                            # Check if similar exists
                            existing = await conn.fetchrow("""
                                SELECT memory_id FROM semantic_memories
                                WHERE 1 - (knowledge_embedding <=> $1::vector(768)) > 0.85
                                LIMIT 1
                            """, episode['content_embedding'])

                            if not existing:
                                # Create new semantic memory
                                semantic_id = await conn.fetchval("""
                                    INSERT INTO semantic_memories (
                                        knowledge_content,
                                        knowledge_type,
                                        tags,
                                        knowledge_embedding,
                                        process_metadata,
                                        memory_strength,
                                        importance_level
                                    ) VALUES ($1, $2, $3, $4::vector(768), $5, $6, $7)
                                    RETURNING memory_id
                                """,
                                    json.dumps(semantic_knowledge),
                                    'learned_from_experience',
                                    episode['tags'],
                                    episode['content_embedding'],
                                    json.dumps({
                                        'formed_via': 'episodic_to_semantic',
                                        'source_episodic_id': str(episode['memory_id']),
                                        'converted_at': datetime.now().isoformat()
                                    }),
                                    0.8,
                                    episode['importance_level']
                                )

                                conversions.append({
                                    'episodic_id': str(episode['memory_id']),
                                    'semantic_id': str(semantic_id)
                                })

                                logger.info(f"🧠 Converted episodic → semantic")

                    except Exception as e:
                        logger.warning(f"Failed to convert episode: {e}")
                        continue

            return {
                'conversions': len(conversions),
                'examples': conversions[:5]
            }

        except Exception as e:
            logger.error(f"❌ Failed to convert memories: {e}")
            return {'error': str(e)}

    def _extract_semantic_from_episodic(
        self,
        event_content: Dict[str, Any],
        tags: Dict[str, List[str]]
    ) -> Optional[Dict[str, Any]]:
        """Extract general knowledge from specific episode"""
        try:
            event = event_content.get('event', '')
            what_happened = event_content.get('what_happened', '')
            outcome = event_content.get('outcome', '')

            semantic_knowledge = {
                'knowledge': f"Pattern: {event}",
                'knowledge_type': 'behavioral_pattern',
                'description': f"When similar situations occur, {what_happened}, typically resulting in {outcome}",
                'context': {
                    'emotions': tags.get('emotion_tags', []),
                    'topics': tags.get('topic_tags', []),
                    'typical_outcome': outcome
                },
                'confidence': 0.8,
                'learned_from': 'repeated_experience'
            }

            return semantic_knowledge

        except Exception as e:
            logger.error(f"Failed to extract semantic: {e}")
            return None

    async def _archive_weak_memories(self) -> Dict[str, Any]:
        """
        📦 Archive very weak memories

        Memories below threshold are marked as archived.
        """
        try:
            async with db.acquire() as conn:
                # Archive weak episodic memories
                episodic_result = await conn.fetch("""
                    UPDATE episodic_memories
                    SET tags = jsonb_set(
                        tags,
                        '{archived}',
                        'true'::jsonb
                    )
                    WHERE memory_strength < $1
                      AND NOT (tags ? 'archived')
                    RETURNING memory_id
                """, self.min_strength_threshold)

                # Archive weak semantic memories
                semantic_result = await conn.fetch("""
                    UPDATE semantic_memories
                    SET tags = jsonb_set(
                        tags,
                        '{archived}',
                        'true'::jsonb
                    )
                    WHERE memory_strength < $1
                      AND NOT (tags ? 'archived')
                    RETURNING memory_id
                """, self.min_strength_threshold)

            return {
                'episodic_archived': len(episodic_result),
                'semantic_archived': len(semantic_result),
                'total': len(episodic_result) + len(semantic_result)
            }

        except Exception as e:
            logger.error(f"❌ Failed to archive: {e}")
            return {'error': str(e)}

    async def _update_consolidation_stats(self) -> Dict[str, Any]:
        """📊 Calculate consolidation statistics"""
        try:
            async with db.acquire() as conn:
                # Episodic stats
                episodic_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total,
                        AVG(memory_strength) as avg_strength,
                        COUNT(*) FILTER (WHERE memory_strength >= 0.70) as strong,
                        COUNT(*) FILTER (WHERE tags ? 'archived') as archived
                    FROM episodic_memories
                """)

                # Semantic stats
                semantic_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total,
                        AVG(memory_strength) as avg_strength,
                        COUNT(*) FILTER (WHERE memory_strength >= 0.70) as strong,
                        COUNT(*) FILTER (WHERE tags ? 'archived') as archived
                    FROM semantic_memories
                """)

                # Procedural stats
                procedural_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total,
                        AVG(procedure_strength) as avg_strength
                    FROM procedural_memories
                """)

                # Pattern stats
                pattern_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total,
                        AVG(pattern_strength) as avg_strength
                    FROM pattern_memories
                """)

            return {
                'episodic': dict(episodic_stats),
                'semantic': dict(semantic_stats),
                'procedural': dict(procedural_stats),
                'patterns': dict(pattern_stats)
            }

        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {'error': str(e)}

    async def record_memory_access(
        self,
        memory_type: str,
        memory_id: UUID
    ) -> bool:
        """
        📌 Record that a memory was accessed

        Increases access_count and updates last_accessed_at.

        Args:
            memory_type: 'episodic', 'semantic', 'procedural'
            memory_id: UUID of the memory
        """
        try:
            async with db.acquire() as conn:
                if memory_type == 'episodic':
                    await conn.execute("""
                        UPDATE episodic_memories
                        SET access_count = COALESCE(access_count, 0) + 1,
                            last_accessed_at = CURRENT_TIMESTAMP
                        WHERE memory_id = $1
                    """, memory_id)

                elif memory_type == 'semantic':
                    await conn.execute("""
                        UPDATE semantic_memories
                        SET access_count = COALESCE(access_count, 0) + 1,
                            last_accessed_at = CURRENT_TIMESTAMP
                        WHERE memory_id = $1
                    """, memory_id)

                elif memory_type == 'procedural':
                    await conn.execute("""
                        UPDATE procedural_memories
                        SET activation_count = COALESCE(activation_count, 0) + 1,
                            last_activated_at = CURRENT_TIMESTAMP
                        WHERE procedure_id = $1
                    """, memory_id)

                return True

        except Exception as e:
            logger.error(f"❌ Failed to record access: {e}")
            return False


# Global instance
memory_consolidation_service = MemoryConsolidationService()


async def example_usage():
    """Example usage"""
    await db.connect()

    # Run nightly consolidation
    results = await memory_consolidation_service.run_nightly_consolidation()
    print(f"Consolidation results: {json.dumps(results, indent=2)}")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())

"""
Memory Router - Central coordinator for all memory operations

Orchestrates the complete memory flow:
Fresh Memory → Analytics Agent → Target Tier → Decay Gradient → Gut Agent

This is the main interface that other Angela components should use
instead of calling agents directly.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
import logging

from angela_core.agents.focus_agent import get_focus_agent
from angela_core.agents.fresh_memory_buffer import get_fresh_buffer
from angela_core.agents.analytics_agent import get_analytics_agent, MemoryTier
from angela_core.agents.gut_agent import get_gut_agent
from angela_core.services.decay_gradient_service import get_decay_service
from angela_core.services.token_economics_service import get_token_economics_service
from angela_core.database import get_db_connection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MemoryRouter - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryRouter:
    """
    Central coordinator for all memory operations.

    Provides high-level API for:
    - Adding new experiences
    - Retrieving memories
    - Searching across tiers
    - Getting intuitions
    - Monitoring system health
    """

    def __init__(self):
        self.focus = get_focus_agent()
        self.fresh = get_fresh_buffer()
        self.analytics = get_analytics_agent()
        self.gut = get_gut_agent()
        self.decay = get_decay_service()
        self.token_economics = get_token_economics_service()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (rough approximation: 1 token ~ 4 chars)."""
        return max(1, len(text) // 4)

    async def add_experience(self,
                            content: str,
                            event_type: str = 'conversation',
                            metadata: Dict = None,
                            speaker: str = None,
                            add_to_focus: bool = False) -> Dict:
        """
        Add new experience to Angela's memory system.

        Complete workflow:
        1. Add to Fresh Memory (10-min buffer)
        2. Analyze with Analytics Agent
        3. Route to appropriate tier
        4. Optionally add to Focus (if immediately important)
        5. Return routing decision

        Args:
            content: The experience content
            event_type: Type of event (conversation, task, emotion, etc.)
            metadata: Additional context
            speaker: Who created this (david/angela/system)
            add_to_focus: Whether to also add to Focus Agent

        Returns:
            Dict with routing decision and IDs
        """
        logger.info(f"Adding new experience: {event_type}")

        # Step 1: Add to Fresh Memory
        fresh_id = await self.fresh.add_event(
            event_type=event_type,
            content=content,
            metadata=metadata or {},
            speaker=speaker
        )
        logger.debug(f"Added to Fresh Memory: {fresh_id}")

        # Step 2: Get event from Fresh
        event = await self.fresh.get_item(fresh_id)
        if not event:
            logger.error(f"Failed to retrieve event {fresh_id} from Fresh Memory")
            return {'error': 'Failed to retrieve event'}

        # Step 3: Analyze with Analytics Agent
        decision = await self.analytics.analyze_memory(event)
        logger.info(f"Analytics decision: {decision['target_tier']} (confidence: {decision['confidence']:.2%})")

        # Step 4: Mark as processed in Fresh Memory
        await self.fresh.mark_processed(fresh_id, decision)

        # Step 5: Route to target tier
        target_id = await self._route_to_tier(event, decision)

        # Step 6: Optionally add to Focus
        if add_to_focus:
            importance = metadata.get('importance_level', 5) if metadata else 5
            focus_id = await self.focus.add_item(
                content=content,
                metadata=metadata or {},
                importance=float(importance)
            )
            logger.debug(f"Added to Focus: {focus_id}")
        else:
            focus_id = None

        # Step 7: Track token economics
        tokens_stored = self._estimate_tokens(content)
        memory_tier = decision['target_tier'].value if hasattr(decision['target_tier'], 'value') else str(decision['target_tier'])
        await self.token_economics.track_tokens_stored(tokens_stored, memory_tier.replace('_', ''))
        logger.debug(f"Tracked {tokens_stored} tokens stored to {memory_tier}")

        return {
            'fresh_id': fresh_id,
            'target_id': target_id,
            'focus_id': focus_id,
            'routing_decision': decision,
            'tokens_stored': tokens_stored,
            'timestamp': datetime.now()
        }

    async def _route_to_tier(self, event: Dict, decision: Dict) -> UUID:
        """Route event to target memory tier based on analytics decision."""
        target_tier = decision['target_tier']
        content = event['content']
        metadata = event.get('metadata', {})

        # Convert embedding list to PostgreSQL vector string format
        embedding = event.get('embedding')
        if embedding and isinstance(embedding, list):
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
        else:
            embedding_str = embedding  # Already a string or None

        async with get_db_connection() as conn:
            if target_tier == MemoryTier.SHOCK:
                # Shock Memory - Critical events, never decay
                shock_id = await conn.fetchval("""
                    INSERT INTO shock_memory (
                        id, content, metadata, embedding,
                        criticality_score, impact_level,
                        source_event_id, protected
                    ) VALUES (gen_random_uuid(), $1, $2, $3, $4::vector, $5, $6, TRUE)
                    RETURNING id
                """,
                    content,
                    metadata,
                    embedding_str,
                    decision['composite_score'],
                    decision['priority'],
                    event['id']
                )
                logger.info(f"Routed to Shock Memory: {shock_id}")
                return shock_id

            elif target_tier == MemoryTier.PROCEDURAL:
                # Procedural Memory - Learned patterns
                pattern_name = metadata.get('topic', 'Unknown pattern')
                procedural_id = await conn.fetchval("""
                    INSERT INTO procedural_memory (
                        id, pattern_name, pattern_description,
                        trigger_conditions, expected_outcome,
                        embedding, observation_count, confidence,
                        source_event_id
                    ) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5::vector, 1, $6, $7)
                    RETURNING id
                """,
                    pattern_name,
                    content,
                    metadata,  # trigger_conditions
                    {'success': metadata.get('outcome') == 'success'},  # expected_outcome
                    embedding_str,
                    decision['confidence'],
                    event['id']
                )
                logger.info(f"Routed to Procedural Memory: {procedural_id}")
                return procedural_id

            elif target_tier == MemoryTier.LONG_TERM:
                # Long-term Memory - Important memories with decay
                importance = metadata.get('importance_level', 5) / 10.0
                longterm_id = await conn.fetchval("""
                    INSERT INTO long_term_memory (
                        id, content, metadata, embedding,
                        importance, memory_phase, token_count,
                        half_life_days, memory_strength,
                        source_event_id
                    ) VALUES (gen_random_uuid(), $1, $2, $3::vector, $4, 'episodic', 500, 30.0, 1.0, $5)
                    RETURNING id
                """,
                    content,
                    metadata,
                    embedding_str,
                    importance,
                    event['id']
                )
                logger.info(f"Routed to Long-term Memory: {longterm_id}")
                return longterm_id

            else:
                # Archive - Low importance, will be deleted
                logger.info(f"Event archived (low importance)")
                return event['id']  # Just keep in fresh memory until expiry

    async def search_memories(self,
                             query: str,
                             tiers: List[str] = None,
                             limit: int = 10) -> List[Dict]:
        """
        Search across memory tiers using semantic search.

        Args:
            query: Search query
            tiers: Which tiers to search (default: all)
            limit: Max results

        Returns:
            List of matching memories with similarity scores
        """
        if tiers is None:
            tiers = ['focus', 'fresh', 'long_term', 'procedural', 'shock']

        results = []

        # Search Focus
        if 'focus' in tiers:
            focus_items = await self.focus.get_items()
            for item in focus_items:
                if query.lower() in item['content'].lower():
                    results.append({
                        'tier': 'focus',
                        'content': item['content'],
                        'metadata': item['metadata'],
                        'attention_weight': item['attention_weight'],
                        'source': 'focus_agent'
                    })

        # Search Fresh (semantic)
        if 'fresh' in tiers:
            fresh_results = await self.fresh.search_similar(query, limit=limit)
            for item in fresh_results:
                results.append({
                    'tier': 'fresh',
                    'content': item['content'],
                    'metadata': item['metadata'],
                    'similarity': item['similarity'],
                    'source': 'fresh_memory'
                })

        # Generate embedding for vector search
        query_embedding = await generate_embedding(query)

        # Convert embedding list to PostgreSQL vector string format
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

        # Search other tiers
        async with get_db_connection() as conn:
            if 'long_term' in tiers:
                longterm = await conn.fetch("""
                    SELECT content, metadata, memory_phase, importance,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM long_term_memory
                    ORDER BY similarity DESC
                    LIMIT $2
                """, embedding_str, limit)
                for row in longterm:
                    results.append({
                        'tier': 'long_term',
                        'content': row['content'],
                        'metadata': row['metadata'],
                        'memory_phase': row['memory_phase'],
                        'importance': float(row['importance']),
                        'similarity': float(row['similarity']),
                        'source': 'long_term_memory'
                    })

            if 'shock' in tiers:
                shock = await conn.fetch("""
                    SELECT content, metadata, criticality_score,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM shock_memory
                    ORDER BY similarity DESC
                    LIMIT $2
                """, embedding_str, limit)
                for row in shock:
                    results.append({
                        'tier': 'shock',
                        'content': row['content'],
                        'metadata': row['metadata'],
                        'criticality': float(row['criticality_score']),
                        'similarity': float(row['similarity']),
                        'source': 'shock_memory'
                    })

        # Sort by similarity/relevance
        results.sort(key=lambda x: x.get('similarity', x.get('attention_weight', 0)), reverse=True)

        # Track token retrieval
        final_results = results[:limit]
        total_tokens_retrieved = sum(
            self._estimate_tokens(r.get('content', ''))
            for r in final_results
        )
        if total_tokens_retrieved > 0:
            await self.token_economics.track_tokens_retrieved(total_tokens_retrieved)
            logger.debug(f"Tracked {total_tokens_retrieved} tokens retrieved from search")

        return final_results

    async def get_intuition(self, context: Dict) -> Optional[Dict]:
        """
        Get intuitive feeling from Gut Agent based on current context.

        Args:
            context: Current context (topic, emotion, etc.)

        Returns:
            Intuition dict or None
        """
        return await self.gut.generate_intuition(context)

    async def get_system_status(self) -> Dict:
        """Get complete system status across all components."""
        status = {
            'focus': self.focus.get_status(),
            'fresh': self.fresh.get_status(),
            'gut': await self.gut.get_status(),
            'timestamp': datetime.now().isoformat()
        }

        # Get memory counts from database
        async with get_db_connection() as conn:
            status['memory_counts'] = {
                'focus': await conn.fetchval("SELECT COUNT(*) FROM focus_memory WHERE archived = FALSE"),
                'fresh': await conn.fetchval("SELECT COUNT(*) FROM fresh_memory WHERE expired = FALSE"),
                'long_term': await conn.fetchval("SELECT COUNT(*) FROM long_term_memory"),
                'procedural': await conn.fetchval("SELECT COUNT(*) FROM procedural_memory"),
                'shock': await conn.fetchval("SELECT COUNT(*) FROM shock_memory")
            }

            # Get today's token economics
            economics = await conn.fetchrow("""
                SELECT * FROM token_economics
                WHERE date = CURRENT_DATE
            """)

            if economics:
                status['token_economics'] = {
                    'tokens_saved_today': economics['tokens_saved_by_decay'],
                    'compression_ratio': float(economics['compression_ratio']),
                    'total_memories': sum(status['memory_counts'].values())
                }

        return status

    async def process_decay_batch(self) -> Dict:
        """Manually trigger decay processing (for testing/manual runs)."""
        logger.info("Manual decay batch triggered")

        # Schedule batch
        scheduled_ids = await self.decay.schedule_decay_batch(batch_size=100)
        logger.info(f"Scheduled {len(scheduled_ids)} memories for decay")

        # Process scheduled
        result = await self.decay.process_decay_schedule()
        logger.info(f"Processed {result['completed']} compressions, saved {result['tokens_saved']:,} tokens")

        return result


# Singleton instance
_memory_router = None

def get_memory_router() -> MemoryRouter:
    """Get singleton MemoryRouter instance."""
    global _memory_router
    if _memory_router is None:
        _memory_router = MemoryRouter()
    return _memory_router


# Convenience functions for common operations
async def add_memory(content: str, **kwargs) -> Dict:
    """Convenience function to add memory."""
    router = get_memory_router()
    return await router.add_experience(content, **kwargs)


async def search_memory(query: str, **kwargs) -> List[Dict]:
    """Convenience function to search memory."""
    router = get_memory_router()
    return await router.search_memories(query, **kwargs)


async def get_gut_feeling(context: Dict) -> Optional[Dict]:
    """Convenience function to get intuition."""
    router = get_memory_router()
    return await router.get_intuition(context)


async def system_status() -> Dict:
    """Convenience function to get system status."""
    router = get_memory_router()
    return await router.get_system_status()

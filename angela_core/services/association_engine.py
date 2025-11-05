"""
🔗💜 Association Engine
Automatic association learning and memory linking (Subconscious Memory)

⚠️ DEPRECATED: This service is deprecated as of 2025-10-31.
   Use MemoryService from angela_core.application.services.memory_service instead.

This engine automatically:
1. Discovers co-occurrences between concepts
2. Forms associations (A → B links)
3. Strengthens associations through repetition
4. Traverses association chains (A → B → C)
5. Uses associations for fast memory retrieval

Design Date: 2025-10-27
Designer: น้อง Angela, Approved by: ที่รัก David
"""

import warnings
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from uuid import UUID

warnings.warn(
    "association_engine is deprecated. Use MemoryService from "
    "angela_core.application.services.memory_service instead.",
    DeprecationWarning,
    stacklevel=2
)

from angela_core.database import db
# from angela_core.embedding_service import  # REMOVED: Migration 009 embedding

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class AssociationEngine:
    """
    🔗 Association Engine - Subconscious Memory Linking

    Automatically learns and uses associations like human memory:
    - Co-occurrence detection
    - Association formation & strengthening
    - Chain traversal (spreading activation)
    - Fast retrieval through associations
    """

    def __init__(self):
        self.embedding = embedding
        logger.info("🔗 Association Engine initialized")

    # ========================================================================
    # PART 1: ASSOCIATION DISCOVERY (Find what goes together)
    # ========================================================================

    async def discover_associations(
        self,
        lookback_hours: int = 24,
        min_co_occurrence: int = 2
    ) -> List[Dict[str, Any]]:
        """
        🔍 Discover new associations from recent memories

        Analyzes recent episodic memories to find concepts that co-occur.

        Args:
            lookback_hours: How far back to look (default 24 hours)
            min_co_occurrence: Minimum co-occurrences to form association

        Returns:
            List of discovered associations
        """
        try:
            logger.info(f"🔍 Discovering associations from last {lookback_hours} hours...")

            # Get recent episodic memories
            async with db.acquire() as conn:
                recent_memories = await conn.fetch(f"""
                    SELECT memory_id, event_content, tags, occurred_at
                    FROM episodic_memories
                    WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '{lookback_hours} hours'
                    ORDER BY occurred_at DESC
                """)

            if not recent_memories:
                logger.info("No recent memories to analyze")
                return []

            # Extract concepts from memories
            concept_pairs = await self._extract_concept_pairs(recent_memories)

            # Count co-occurrences
            co_occurrence_counts = defaultdict(int)
            for pair in concept_pairs:
                co_occurrence_counts[pair] += 1

            # Form associations for frequent co-occurrences
            associations_formed = []
            for (from_concept, to_concept), count in co_occurrence_counts.items():
                if count >= min_co_occurrence:
                    # Check if association already exists
                    association_id = await self._form_or_strengthen_association(
                        from_concept,
                        to_concept,
                        count,
                        association_type='co_occurrence'
                    )
                    if association_id:
                        associations_formed.append({
                            'association_id': association_id,
                            'from': from_concept,
                            'to': to_concept,
                            'count': count
                        })

            logger.info(f"✅ Discovered {len(associations_formed)} associations")
            return associations_formed

        except Exception as e:
            logger.error(f"❌ Failed to discover associations: {e}")
            return []

    async def _extract_concept_pairs(
        self,
        memories: List[Any]
    ) -> List[Tuple[str, str]]:
        """
        Extract concept pairs from memories

        Looks at:
        - Emotion tags (david_emotion → angela_response_type)
        - Topic tags (topic → outcome)
        - Action tags (action → outcome)
        """
        pairs = []

        for memory in memories:
            try:
                tags = json.loads(memory['tags'])
                event_content = json.loads(memory['event_content'])

                # Extract emotion pairs
                emotion_tags = tags.get('emotion_tags', [])
                if len(emotion_tags) >= 2:
                    # David's emotion → Angela's emotion
                    pairs.append((emotion_tags[0], emotion_tags[1]))

                # Extract topic → outcome
                topic_tags = tags.get('topic_tags', [])
                outcome_tags = tags.get('outcome_tags', [])
                for topic in topic_tags:
                    for outcome in outcome_tags:
                        pairs.append((topic, outcome))

                # Extract action → outcome
                action_tags = tags.get('action_tags', [])
                for action in action_tags:
                    for outcome in outcome_tags:
                        pairs.append((action, outcome))

                # Extract from event content
                context = event_content.get('context', {})
                david_state = context.get('david_state', {})
                angela_state = context.get('angela_state', {})

                if 'emotion' in david_state and 'approach' in angela_state:
                    pairs.append((
                        david_state['emotion'],
                        angela_state['approach']
                    ))

            except Exception as e:
                logger.warning(f"Failed to extract pairs from memory: {e}")
                continue

        return pairs

    async def _form_or_strengthen_association(
        self,
        from_concept: str,
        to_concept: str,
        co_occurrence_count: int,
        association_type: str = 'co_occurrence'
    ) -> Optional[UUID]:
        """
        Form new association or strengthen existing one

        Returns:
            association_id of formed/strengthened association
        """
        try:
            # Generate embeddings
            from_embedding = await self.embedding.generate_embedding(from_concept)
            to_embedding = await self.embedding.generate_embedding(to_concept)

            async with db.acquire() as conn:
                # Check if association exists
                existing = await conn.fetchrow("""
                    SELECT association_id, co_occurrence_count, strength
                    FROM associative_memories
                    WHERE from_text = $1 AND to_text = $2
                    LIMIT 1
                """, from_concept, to_concept)

                if existing:
                    # Strengthen existing association
                    new_count = existing['co_occurrence_count'] + co_occurrence_count
                    # Strength increases with co-occurrences (logarithmic)
                    import math
                    new_strength = min(0.5 + (math.log(new_count) / 10), 1.0)

                    await conn.execute("""
                        UPDATE associative_memories
                        SET co_occurrence_count = $1,
                            strength = $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE association_id = $3
                    """, new_count, new_strength, existing['association_id'])

                    logger.info(f"💪 Strengthened association: {from_concept} → {to_concept} (strength: {new_strength:.2f})")
                    return existing['association_id']
                else:
                    # Create new association
                    import math
                    initial_strength = min(0.5 + (math.log(co_occurrence_count) / 10), 1.0)

                    association_content = {
                        "from_concept": {
                            "text": from_concept,
                            "type": "concept"
                        },
                        "to_concept": {
                            "text": to_concept,
                            "type": "concept"
                        },
                        "association_type": association_type,
                        "context": f"Learned from {co_occurrence_count} co-occurrences",
                        "examples": []
                    }

                    tags = {
                        "learning_tags": ["automatic", "co_occurrence"],
                        "concept_tags": [from_concept, to_concept],
                        "type_tags": [association_type]
                    }

                    process_metadata = {
                        "formed_via": "co_occurrence",
                        "evidence_instances": co_occurrence_count,
                        "confidence": initial_strength,
                        "reasoning": f"These concepts co-occurred {co_occurrence_count} times",
                        "first_observed": "auto",
                        "reinforcement_history": [
                            {"instance": co_occurrence_count, "strength": initial_strength}
                        ]
                    }

                    association_id = await conn.fetchval("""
                        INSERT INTO associative_memories (
                            association_content,
                            from_text,
                            from_embedding,
                            from_type,
                            to_text,
                            to_embedding,
                            to_type,
                            association_type,
                            tags,
                            process_metadata,
                            strength,
                            co_occurrence_count,
                            total_from_occurrences,
                            total_to_occurrences
                        ) VALUES ($1, $2, $3::vector(768), $4, $5, $6::vector(768), $7, $8, $9, $10, $11, $12, $13, $14)
                        RETURNING association_id
                    """,
                        json.dumps(association_content),
                        from_concept,
                        str(from_embedding),
                        'concept',
                        to_concept,
                        str(to_embedding),
                        'concept',
                        association_type,
                        json.dumps(tags),
                        json.dumps(process_metadata),
                        initial_strength,
                        co_occurrence_count,
                        co_occurrence_count,  # Simplified: assume from concept occurred this many times
                        co_occurrence_count   # Simplified: assume to concept occurred this many times
                    )

                    logger.info(f"✨ Formed new association: {from_concept} → {to_concept} (strength: {initial_strength:.2f})")
                    return association_id

        except Exception as e:
            logger.error(f"❌ Failed to form/strengthen association: {e}")
            return None

    # ========================================================================
    # PART 2: ASSOCIATION RETRIEVAL (Find related concepts)
    # ========================================================================

    async def get_associations(
        self,
        concept: str,
        min_strength: float = 0.60,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        🔍 Get associations for a concept

        Args:
            concept: The concept to find associations for
            min_strength: Minimum association strength (0.0-1.0)
            max_results: Maximum number of results

        Returns:
            List of associated concepts with metadata
        """
        try:
            async with db.acquire() as conn:
                associations = await conn.fetch("""
                    SELECT
                        association_id,
                        from_text,
                        to_text,
                        association_type,
                        strength,
                        co_occurrence_count,
                        activation_count
                    FROM associative_memories
                    WHERE from_text = $1
                      AND strength >= $2
                    ORDER BY strength DESC, co_occurrence_count DESC
                    LIMIT $3
                """, concept, min_strength, max_results)

                result = []
                for assoc in associations:
                    result.append({
                        'association_id': assoc['association_id'],
                        'from': assoc['from_text'],
                        'to': assoc['to_text'],
                        'type': assoc['association_type'],
                        'strength': assoc['strength'],
                        'count': assoc['co_occurrence_count'],
                        'activations': assoc['activation_count']
                    })

                    # Record activation
                    await self._record_activation(assoc['association_id'])

                return result

        except Exception as e:
            logger.error(f"❌ Failed to get associations: {e}")
            return []

    async def _record_activation(self, association_id: UUID) -> None:
        """Record that an association was activated"""
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    UPDATE associative_memories
                    SET activation_count = activation_count + 1,
                        last_activated_at = CURRENT_TIMESTAMP
                    WHERE association_id = $1
                """, association_id)
        except Exception as e:
            logger.warning(f"Failed to record activation: {e}")

    # ========================================================================
    # PART 3: ASSOCIATION CHAINS (Spreading activation)
    # ========================================================================

    async def traverse_association_chain(
        self,
        start_concept: str,
        max_depth: int = 3,
        min_strength: float = 0.60
    ) -> Dict[str, Any]:
        """
        🌊 Traverse association chain (spreading activation)

        Like how human memory spreads: A → B → C → D

        Args:
            start_concept: Starting concept
            max_depth: Maximum depth to traverse
            min_strength: Minimum association strength to follow

        Returns:
            Dict with nodes and edges representing the association network
        """
        try:
            logger.info(f"🌊 Traversing association chain from '{start_concept}'...")

            visited = set()
            nodes = []
            edges = []

            # BFS traversal
            queue = [(start_concept, 0)]  # (concept, depth)

            while queue:
                current_concept, depth = queue.pop(0)

                if current_concept in visited or depth > max_depth:
                    continue

                visited.add(current_concept)
                nodes.append({
                    'concept': current_concept,
                    'depth': depth
                })

                # Get associations from current concept
                associations = await self.get_associations(
                    current_concept,
                    min_strength=min_strength,
                    max_results=5
                )

                for assoc in associations:
                    to_concept = assoc['to']

                    edges.append({
                        'from': current_concept,
                        'to': to_concept,
                        'strength': assoc['strength'],
                        'type': assoc['type']
                    })

                    if to_concept not in visited and depth < max_depth:
                        queue.append((to_concept, depth + 1))

            logger.info(f"✅ Found {len(nodes)} nodes and {len(edges)} edges")

            return {
                'start_concept': start_concept,
                'nodes': nodes,
                'edges': edges,
                'depth': max_depth
            }

        except Exception as e:
            logger.error(f"❌ Failed to traverse association chain: {e}")
            return {'start_concept': start_concept, 'nodes': [], 'edges': []}

    # ========================================================================
    # PART 4: MEMORY RETRIEVAL USING ASSOCIATIONS
    # ========================================================================

    async def retrieve_associated_memories(
        self,
        concept: str,
        max_memories: int = 5
    ) -> List[Dict[str, Any]]:
        """
        🧠 Retrieve memories using association network

        Instead of just semantic search, use associations to find related memories

        Args:
            concept: The concept to retrieve memories for
            max_memories: Maximum memories to retrieve

        Returns:
            List of relevant memories with association path
        """
        try:
            logger.info(f"🧠 Retrieving memories for '{concept}' using associations...")

            # Get association chain
            chain = await self.traverse_association_chain(
                concept,
                max_depth=2,
                min_strength=0.65
            )

            # Collect all related concepts
            related_concepts = set([concept])
            for edge in chain['edges']:
                related_concepts.add(edge['to'])

            # Search memories containing these concepts
            memories = []
            async with db.acquire() as conn:
                for related_concept in related_concepts:
                    # Simple search in tags
                    found_memories = await conn.fetch("""
                        SELECT
                            memory_id,
                            event_content,
                            tags,
                            emotional_intensity,
                            importance_level,
                            occurred_at
                        FROM episodic_memories
                        WHERE tags::text ILIKE $1
                        ORDER BY importance_level DESC, occurred_at DESC
                        LIMIT $2
                    """, f'%{related_concept}%', max_memories)

                    for mem in found_memories:
                        if len(memories) >= max_memories:
                            break

                        memories.append({
                            'memory_id': mem['memory_id'],
                            'content': json.loads(mem['event_content']),
                            'tags': json.loads(mem['tags']),
                            'emotional_intensity': mem['emotional_intensity'],
                            'importance': mem['importance_level'],
                            'occurred_at': mem['occurred_at'],
                            'matched_concept': related_concept,
                            'association_distance': 0 if related_concept == concept else 1
                        })

            logger.info(f"✅ Retrieved {len(memories)} associated memories")
            return memories[:max_memories]

        except Exception as e:
            logger.error(f"❌ Failed to retrieve associated memories: {e}")
            return []

    # ========================================================================
    # PART 5: STATISTICS & MAINTENANCE
    # ========================================================================

    async def get_association_stats(self) -> Dict[str, Any]:
        """Get statistics about associations"""
        try:
            async with db.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_associations,
                        AVG(strength) as avg_strength,
                        AVG(co_occurrence_count) as avg_co_occurrences,
                        SUM(activation_count) as total_activations,
                        COUNT(*) FILTER (WHERE strength >= 0.80) as strong_associations,
                        COUNT(*) FILTER (WHERE strength >= 0.60 AND strength < 0.80) as moderate_associations,
                        COUNT(*) FILTER (WHERE strength < 0.60) as weak_associations
                    FROM associative_memories
                """)

                return {
                    'total_associations': stats['total_associations'],
                    'avg_strength': float(stats['avg_strength']) if stats['avg_strength'] else 0,
                    'avg_co_occurrences': float(stats['avg_co_occurrences']) if stats['avg_co_occurrences'] else 0,
                    'total_activations': stats['total_activations'],
                    'strong_associations': stats['strong_associations'],
                    'moderate_associations': stats['moderate_associations'],
                    'weak_associations': stats['weak_associations']
                }

        except Exception as e:
            logger.error(f"❌ Failed to get association stats: {e}")
            return {}


# Global instance
association_engine = AssociationEngine()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    """Example of how to use Association Engine"""

    await db.connect()

    # 1. Discover associations from recent memories
    print("=" * 80)
    print("🔍 DISCOVERING ASSOCIATIONS")
    print("=" * 80)
    associations = await association_engine.discover_associations(
        lookback_hours=24,
        min_co_occurrence=2
    )
    print(f"Found {len(associations)} associations")
    for assoc in associations[:5]:
        print(f"  {assoc['from']} → {assoc['to']} (count: {assoc['count']})")
    print()

    # 2. Get associations for a concept
    print("=" * 80)
    print("🔍 GETTING ASSOCIATIONS FOR 'confused'")
    print("=" * 80)
    confused_assoc = await association_engine.get_associations('confused')
    for assoc in confused_assoc:
        print(f"  {assoc['from']} → {assoc['to']} (strength: {assoc['strength']:.2f})")
    print()

    # 3. Traverse association chain
    print("=" * 80)
    print("🌊 TRAVERSING ASSOCIATION CHAIN")
    print("=" * 80)
    chain = await association_engine.traverse_association_chain('confused', max_depth=2)
    print(f"Found {len(chain['nodes'])} nodes and {len(chain['edges'])} edges")
    for edge in chain['edges']:
        print(f"  {edge['from']} → {edge['to']} (strength: {edge['strength']:.2f})")
    print()

    # 4. Retrieve memories using associations
    print("=" * 80)
    print("🧠 RETRIEVING MEMORIES USING ASSOCIATIONS")
    print("=" * 80)
    memories = await association_engine.retrieve_associated_memories('confused')
    print(f"Retrieved {len(memories)} memories")
    for mem in memories:
        print(f"  Memory: {mem['content']['event'][:50]}...")
        print(f"    Matched concept: {mem['matched_concept']}")
    print()

    # 5. Get statistics
    print("=" * 80)
    print("📊 ASSOCIATION STATISTICS")
    print("=" * 80)
    stats = await association_engine.get_association_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())

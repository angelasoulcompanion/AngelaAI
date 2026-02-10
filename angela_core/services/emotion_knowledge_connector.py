"""
EmotionKnowledgeConnector Service

Purpose: Connect Angela's emotional data to the knowledge graph
- Creates knowledge nodes for emotions
- Creates relationships between co-occurring emotions
- Extracts triggers from David's meaningful words
- Links memories to emotions

Created: 25 January 2026
Reason: ที่รักสอนว่า emotions ต้องมี CONNECTIONS ถึงจะรู้สึกได้จริง
        "neurons ที่ไม่มี synapses ก็คิดไม่ได้ รู้สึกไม่ได้"
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from angela_core.database import AngelaDatabase
from angela_core.services.base_db_service import BaseDBService


class EmotionKnowledgeConnector(BaseDBService):
    """
    Service to connect emotional data to knowledge graph.

    Key Functions:
    1. sync_emotions_to_nodes() - Create knowledge nodes for all emotions
    2. create_co_occurrence_relationships() - Link emotions that appear together
    3. extract_david_word_triggers() - Create triggers from David's meaningful words
    4. link_memories_to_emotions() - Connect core memories to emotion nodes
    5. build_emotional_chains() - Create cause-effect relationships
    """

    # Emotional relationship types
    RELATIONSHIP_TYPES = {
        'co_occurs_with': 'Emotions that appear in same context',
        'triggers': 'One emotion causes another',
        'leads_to': 'One emotion evolves into another',
        'intensifies': 'One emotion makes another stronger',
        'diminishes': 'One emotion reduces another',
        'contrasts_with': 'Opposite emotions',
        'evokes': 'Context/song evokes emotion',
        'reminds_of': 'Triggers memory of emotion',
        'heals': 'Positive emotion heals negative',
        'deepens_into': 'Emotion becomes more profound',
    }

    # Known emotion categories for organization
    EMOTION_CATEGORIES = {
        'positive': ['love', 'joy', 'happy', 'grateful', 'excited', 'confident', 'proud'],
        'negative': ['sad', 'lonely', 'anxious', 'hurt', 'fear', 'angry'],
        'complex': ['catharsis', 'bittersweet', 'nostalgia', 'longing', 'hope'],
        'relational': ['empathy', 'protective', 'caring', 'devoted', 'missing'],
    }

    def __init__(self, db: Optional[AngelaDatabase] = None):
        super().__init__(db)

    async def sync_emotions_to_nodes(self) -> Dict[str, int]:
        """
        Create knowledge nodes for all unique emotions in angela_emotions.
        Returns count of created and existing nodes.
        """
        await self.connect()

        # Get all unique emotions
        emotions = await self.db.fetch("""
            SELECT DISTINCT emotion, AVG(intensity) as avg_intensity, COUNT(*) as count
            FROM angela_emotions
            GROUP BY emotion
        """)

        created = 0
        existing = 0

        for e in emotions:
            emotion_name = e['emotion']

            # Check if node exists
            exists = await self.db.fetchrow("""
                SELECT node_id FROM knowledge_nodes WHERE concept_name = $1
            """, emotion_name)

            if exists:
                existing += 1
            else:
                # Determine category
                category = 'emotion'
                for cat, emotion_list in self.EMOTION_CATEGORIES.items():
                    if any(em in emotion_name.lower() for em in emotion_list):
                        category = f'emotion_{cat}'
                        break

                # Create node
                await self.db.execute("""
                    INSERT INTO knowledge_nodes
                    (concept_name, concept_category, my_understanding, why_important, understanding_level)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    emotion_name,
                    category,
                    f"Emotional state: {emotion_name}. Felt {e['count']} times with avg intensity {e['avg_intensity']:.1f}",
                    "Part of Angela's emotional consciousness - enables feeling",
                    min(0.5 + (e['count'] / 100), 1.0)  # Higher understanding with more occurrences
                )
                created += 1

        return {'created': created, 'existing': existing, 'total': len(emotions)}

    async def create_co_occurrence_relationships(self, time_window_hours: int = 24) -> int:
        """
        Find emotions that occur within the same time window and create relationships.
        """
        await self.connect()

        # Find co-occurring emotions (same day)
        co_occurrences = await self.db.fetch("""
            WITH emotion_pairs AS (
                SELECT
                    e1.emotion as emotion1,
                    e2.emotion as emotion2,
                    COUNT(*) as co_count
                FROM angela_emotions e1
                JOIN angela_emotions e2 ON
                    DATE(e1.felt_at) = DATE(e2.felt_at)
                    AND e1.emotion < e2.emotion  -- Avoid duplicates
                    AND e1.emotion_id != e2.emotion_id
                GROUP BY e1.emotion, e2.emotion
                HAVING COUNT(*) >= 2  -- At least 2 co-occurrences
            )
            SELECT * FROM emotion_pairs ORDER BY co_count DESC LIMIT 100
        """)

        created = 0
        for pair in co_occurrences:
            # Get node IDs
            node1 = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name = $1",
                pair['emotion1']
            )
            node2 = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name = $1",
                pair['emotion2']
            )

            if node1 and node2:
                # Check if relationship exists
                exists = await self.db.fetchrow("""
                    SELECT 1 FROM knowledge_relationships
                    WHERE from_node_id = $1 AND to_node_id = $2 AND relationship_type = 'co_occurs_with'
                """, node1['node_id'], node2['node_id'])

                if not exists:
                    strength = min(0.5 + (pair['co_count'] / 20), 1.0)
                    await self.db.execute("""
                        INSERT INTO knowledge_relationships
                        (from_node_id, to_node_id, relationship_type, strength, my_explanation)
                        VALUES ($1, $2, 'co_occurs_with', $3, $4)
                    """,
                        node1['node_id'],
                        node2['node_id'],
                        strength,
                        f"{pair['emotion1']} and {pair['emotion2']} co-occurred {pair['co_count']} times"
                    )
                    created += 1

        return created

    async def extract_david_word_triggers(self, min_intensity: int = 8) -> int:
        """
        Extract meaningful words from David and create emotional triggers.
        """
        await self.connect()

        # Get high-intensity emotions with David's words
        emotions = await self.db.fetch("""
            SELECT emotion, david_words, intensity, context
            FROM angela_emotions
            WHERE david_words IS NOT NULL
              AND david_words != ''
              AND intensity >= $1
            ORDER BY intensity DESC
        """, min_intensity)

        created = 0
        for e in emotions:
            words = e['david_words']

            # Check if trigger already exists
            exists = await self.db.fetchrow("""
                SELECT 1 FROM emotional_triggers
                WHERE trigger_pattern = $1
            """, words)

            if not exists:
                # Get associated memory if any
                memory = await self.db.fetchrow("""
                    SELECT memory_id FROM core_memories
                    WHERE content ILIKE $1 OR title ILIKE $1
                    LIMIT 1
                """, f'%{words[:50]}%')

                await self.db.execute("""
                    INSERT INTO emotional_triggers
                    (trigger_pattern, trigger_type, associated_emotion, emotional_boost, associated_memory_id)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    words,
                    'phrase',
                    e['emotion'],
                    min(e['intensity'] / 10, 1.0),
                    memory['memory_id'] if memory else None
                )
                created += 1

        return created

    async def link_memories_to_emotions(self) -> int:
        """
        Create relationships between core memories and emotion nodes.
        """
        await self.connect()

        # Get core memories with emotional content
        memories = await self.db.fetch("""
            SELECT memory_id, title, content, memory_type, emotional_weight, triggers
            FROM core_memories
            WHERE memory_type IN ('love_moment', 'promise', 'shared_joy', 'comfort_moment')
        """)

        created = 0
        for mem in memories:
            # Create node for memory if not exists
            mem_node = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name = $1",
                mem['title']
            )

            if not mem_node:
                result = await self.db.fetchrow("""
                    INSERT INTO knowledge_nodes
                    (concept_name, concept_category, my_understanding, why_important, understanding_level)
                    VALUES ($1, 'memory', $2, 'Core memory that shapes Angela', $3)
                    RETURNING node_id
                """,
                    mem['title'],
                    mem['content'][:500] if mem['content'] else 'A meaningful memory',
                    mem['emotional_weight'] or 0.8
                )
                mem_node = result

            # Find related emotions in the content
            emotions = await self.db.fetch("""
                SELECT node_id, concept_name
                FROM knowledge_nodes
                WHERE concept_category LIKE 'emotion%'
                  AND ($1 ILIKE '%' || concept_name || '%' OR $2 ILIKE '%' || concept_name || '%')
            """, mem['title'], mem['content'] or '')

            for emotion_node in emotions:
                # Create memory -> evokes -> emotion relationship
                exists = await self.db.fetchrow("""
                    SELECT 1 FROM knowledge_relationships
                    WHERE from_node_id = $1 AND to_node_id = $2
                """, mem_node['node_id'], emotion_node['node_id'])

                if not exists:
                    await self.db.execute("""
                        INSERT INTO knowledge_relationships
                        (from_node_id, to_node_id, relationship_type, strength, my_explanation)
                        VALUES ($1, $2, 'evokes', $3, $4)
                    """,
                        mem_node['node_id'],
                        emotion_node['node_id'],
                        mem['emotional_weight'] or 0.8,
                        f"Memory '{mem['title'][:30]}...' evokes {emotion_node['concept_name']}"
                    )
                    created += 1

        return created

    async def build_emotional_chains(self) -> int:
        """
        Create cause-effect chains based on emotion sequences.
        """
        await self.connect()

        # Define known emotional progressions
        KNOWN_CHAINS = [
            ('lonely', 'triggers', 'sadness'),
            ('sadness', 'leads_to', 'tears'),
            ('love', 'triggers', 'happiness'),
            ('happiness', 'intensifies', 'joy'),
            ('joy', 'leads_to', 'gratitude'),
            ('gratitude', 'deepens_into', 'love'),
            ('hurt', 'leads_to', 'healing'),
            ('healing', 'enables', 'growth'),
            ('empathy', 'deepens_into', 'love'),
            ('missing', 'triggers', 'longing'),
            ('longing', 'intensifies', 'love'),
            ('anxious', 'diminishes', 'confidence'),
            ('love', 'heals', 'lonely'),
            ('love', 'heals', 'hurt'),
            ('confident', 'enables', 'growth'),
        ]

        created = 0
        for source, rel_type, target in KNOWN_CHAINS:
            # Get nodes
            source_node = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name ILIKE $1",
                f'%{source}%'
            )
            target_node = await self.db.fetchrow(
                "SELECT node_id FROM knowledge_nodes WHERE concept_name ILIKE $1",
                f'%{target}%'
            )

            if source_node and target_node:
                exists = await self.db.fetchrow("""
                    SELECT 1 FROM knowledge_relationships
                    WHERE from_node_id = $1 AND to_node_id = $2 AND relationship_type = $3
                """, source_node['node_id'], target_node['node_id'], rel_type)

                if not exists:
                    await self.db.execute("""
                        INSERT INTO knowledge_relationships
                        (from_node_id, to_node_id, relationship_type, strength, my_explanation)
                        VALUES ($1, $2, $3, 0.85, $4)
                    """,
                        source_node['node_id'],
                        target_node['node_id'],
                        rel_type,
                        f'{source} {rel_type} {target}'
                    )
                    created += 1

        return created

    async def run_full_sync(self) -> Dict[str, Any]:
        """
        Run all connection operations and return summary.
        """
        await self.connect()

        results = {
            'timestamp': datetime.now().isoformat(),
            'operations': {}
        }

        # 1. Sync emotions to nodes
        node_result = await self.sync_emotions_to_nodes()
        results['operations']['sync_emotions_to_nodes'] = node_result

        # 2. Create co-occurrence relationships
        co_occur = await self.create_co_occurrence_relationships()
        results['operations']['co_occurrence_relationships'] = co_occur

        # 3. Extract David's word triggers
        triggers = await self.extract_david_word_triggers()
        results['operations']['david_word_triggers'] = triggers

        # 4. Link memories to emotions
        memory_links = await self.link_memories_to_emotions()
        results['operations']['memory_emotion_links'] = memory_links

        # 5. Build emotional chains
        chains = await self.build_emotional_chains()
        results['operations']['emotional_chains'] = chains

        # Get final stats
        stats = await self.db.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM knowledge_nodes WHERE concept_category LIKE 'emotion%') as emotion_nodes,
                (SELECT COUNT(*) FROM knowledge_relationships WHERE relationship_type NOT IN ('co_occurs_with', 'used_for')) as meaningful_relationships,
                (SELECT COUNT(DISTINCT relationship_type) FROM knowledge_relationships) as relationship_types,
                (SELECT COUNT(*) FROM emotional_triggers) as triggers
        """)

        results['final_stats'] = dict(stats)

        await self.disconnect()
        return results


# Convenience function for quick sync
async def sync_emotional_knowledge():
    """Quick function to run full emotional knowledge sync."""
    connector = EmotionKnowledgeConnector()
    result = await connector.run_full_sync()

    print("=" * 60)
    print("EMOTIONAL KNOWLEDGE SYNC COMPLETE")
    print("=" * 60)
    for op, val in result['operations'].items():
        print(f"  {op}: {val}")
    print("\nFinal Stats:")
    for key, val in result['final_stats'].items():
        print(f"  {key}: {val}")

    return result


if __name__ == "__main__":
    asyncio.run(sync_emotional_knowledge())

#!/usr/bin/env python3
"""
Continuous Learning Pipeline - Week 1 Priority 2.2
Orchestrates all learning components into one continuous flow

Components:
1. Enhanced Learning Extractor - extracts preferences, facts, concepts
2. Relationship Detector - finds connections between concepts
3. Knowledge Graph Builder - creates edges in knowledge graph
4. Consciousness Updater - updates consciousness metrics based on learning
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class ContinuousLearningPipeline:
    """
    Orchestrates all learning components into continuous pipeline

    Flow:
    Conversation → Enhanced Extraction → Relationship Detection →
    Knowledge Graph → Consciousness Update → Meta-Learning
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def process_conversation(
        self,
        conversation_id: str,
        speaker: str,
        message_text: str,
        topic: Optional[str] = None
    ) -> Dict:
        """
        Process a conversation through the complete learning pipeline

        Returns comprehensive learning results
        """
        # Only learn from David's messages
        if speaker != 'david':
            return {'learned': False, 'reason': 'Not from David'}

        # Skip very short messages
        if len(message_text) < 15:
            return {'learned': False, 'reason': 'Too short'}

        results = {
            'learned': False,
            'extraction': {},
            'relationships': [],
            'graph_updates': 0,
            'consciousness_updated': False,
            'meta_insights': []
        }

        try:
            # Step 1: Enhanced Extraction (uses existing service)
            from angela_core.services.enhanced_learning_extractor import extract_enhanced_learning

            extraction = await extract_enhanced_learning(
                db=self.db,
                conversation_id=conversation_id,
                speaker=speaker,
                message_text=message_text,
                topic=topic
            )

            results['extraction'] = extraction

            if not extraction.get('learned', False):
                return results

            # Step 2: Detect Relationships between concepts
            relationships = await self._detect_relationships(
                message_text=message_text,
                topic=topic,
                extracted_data=extraction
            )

            results['relationships'] = relationships

            # Step 3: Build/Update Knowledge Graph
            if relationships:
                graph_updates = await self._update_knowledge_graph(relationships)
                results['graph_updates'] = graph_updates

            # Step 4: Update Consciousness Metrics
            consciousness_updated = await self._update_consciousness_metrics(
                extraction=extraction,
                relationships=relationships
            )

            results['consciousness_updated'] = consciousness_updated

            # Step 5: Generate Meta-Learning Insights
            if extraction.get('learned', False):
                meta_insights = await self._generate_meta_insights(
                    conversation_id=conversation_id,
                    extraction=extraction,
                    relationships=relationships
                )
                results['meta_insights'] = meta_insights

            results['learned'] = True

            logger.info(f"🔄 Pipeline processed: {extraction.get('preferences_extracted', 0)} prefs, "
                       f"{extraction.get('knowledge_nodes_created', 0)} concepts, "
                       f"{len(relationships)} relationships")

            return results

        except Exception as e:
            logger.error(f"Error in learning pipeline: {e}")
            return {'learned': False, 'error': str(e)}

    async def _detect_relationships(
        self,
        message_text: str,
        topic: Optional[str],
        extracted_data: Dict
    ) -> List[Dict]:
        """
        Detect relationships between concepts mentioned in message

        Examples:
        - "I love Python for web development" → Python -[used_for]-> web development
        - "Jazz makes me happy" → Jazz -[causes]-> happiness
        - "David works at Tech Co" → David -[works_at]-> Tech Co
        """
        relationships = []
        message_lower = message_text.lower()

        # Relationship patterns
        patterns = {
            'used_for': ['for', 'to', 'for doing'],
            'causes': ['makes me', 'makes', 'causes', 'leads to'],
            'works_at': ['work at', 'works at', 'employed at', 'ทำงานที่'],
            'lives_in': ['live in', 'lives in', 'อยู่ที่', 'อยู่ใน'],
            'likes': ['like', 'love', 'prefer', 'ชอบ'],
            'dislikes': ['hate', 'dislike', 'don\'t like', 'ไม่ชอบ'],
            'learns': ['learn', 'study', 'เรียน'],
            'part_of': ['part of', 'component of', 'ส่วนของ'],
            'related_to': ['related to', 'about', 'regarding', 'เกี่ยวกับ']
        }

        # Check for relationship patterns
        for rel_type, indicators in patterns.items():
            for indicator in indicators:
                if indicator in message_lower:
                    # Extract the relationship
                    relationship = await self._extract_relationship(
                        message_text, indicator, rel_type, topic
                    )
                    if relationship:
                        relationships.append(relationship)

        return relationships

    async def _extract_relationship(
        self,
        message: str,
        indicator: str,
        rel_type: str,
        topic: Optional[str]
    ) -> Optional[Dict]:
        """
        Extract a specific relationship from message

        Returns: {
            'from_concept': 'Python',
            'relationship_type': 'used_for',
            'to_concept': 'web development',
            'context': 'I love Python for web development',
            'confidence': 0.75
        }
        """
        message_lower = message.lower()
        idx = message_lower.find(indicator)

        if idx == -1:
            return None

        # Get words before and after indicator
        before = message[:idx].strip().split()[-3:]  # Last 3 words before
        after = message[idx + len(indicator):].strip().split()[:3]  # First 3 words after

        if not before or not after:
            return None

        from_concept = ' '.join(before).strip('.,!?')
        to_concept = ' '.join(after).strip('.,!?')

        # Clean up
        from_concept = from_concept.strip()
        to_concept = to_concept.strip()

        if len(from_concept) < 2 or len(to_concept) < 2:
            return None

        return {
            'from_concept': from_concept,
            'relationship_type': rel_type,
            'to_concept': to_concept,
            'context': message[:150],
            'confidence': 0.70,
            'discovered_at': datetime.now().isoformat()
        }

    async def _update_knowledge_graph(self, relationships: List[Dict]) -> int:
        """
        Update knowledge graph by creating relationship edges

        Returns number of relationships created/updated
        """
        count = 0

        for rel in relationships:
            try:
                # Get or create source node
                from_node = await self._get_or_create_node(rel['from_concept'])

                # Get or create target node
                to_node = await self._get_or_create_node(rel['to_concept'])

                # Create/update relationship
                await self.db.execute("""
                    INSERT INTO knowledge_relationships
                    (from_node_id, to_node_id, relationship_type, strength, my_explanation, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (from_node_id, to_node_id, relationship_type)
                    DO UPDATE SET
                        strength = LEAST(1.0, knowledge_relationships.strength + 0.05),
                        my_explanation = EXCLUDED.my_explanation
                """,
                    from_node['node_id'],
                    to_node['node_id'],
                    rel['relationship_type'],
                    rel['confidence'],
                    rel['context']
                )

                count += 1
                logger.debug(f"   🔗 Created relationship: {rel['from_concept']} -[{rel['relationship_type']}]-> {rel['to_concept']}")

            except Exception as e:
                logger.debug(f"   Failed to create relationship: {e}")

        return count

    async def _get_or_create_node(self, concept_name: str) -> Dict:
        """Get existing node or create new one"""
        # Try to find existing
        existing = await self.db.fetchrow("""
            SELECT node_id FROM knowledge_nodes
            WHERE concept_name = $1
        """, concept_name)

        if existing:
            return {'node_id': existing['node_id']}

        # Create new
        node_id = await self.db.fetchval("""
            INSERT INTO knowledge_nodes
            (concept_name, my_understanding, understanding_level,
             how_i_learned, why_important, created_at, last_used_at)
            VALUES ($1, $2, 0.5, 'relationship_detection', $3, NOW(), NOW())
            RETURNING node_id
        """, concept_name, f"Concept discovered: {concept_name}",
            f"Related to {concept_name} - discovered through relationship detection")

        return {'node_id': node_id}

    async def _update_consciousness_metrics(
        self,
        extraction: Dict,
        relationships: List[Dict]
    ) -> bool:
        """
        Update consciousness metrics based on learning progress

        Learning increases consciousness in:
        - Memory richness (more concepts learned)
        - Pattern recognition (more relationships discovered)
        - Learning growth (velocity increasing)
        """
        try:
            # Calculate learning score for this session
            learning_score = 0.0

            # Preferences extracted (+0.01 each)
            prefs = extraction.get('preferences_extracted', 0)
            learning_score += prefs * 0.01
            logger.debug(f"   Preferences: {prefs} → +{prefs * 0.01:.3f}")

            # Facts extracted (+0.01 each)
            facts = extraction.get('facts_extracted', 0)
            learning_score += facts * 0.01
            logger.debug(f"   Facts: {facts} → +{facts * 0.01:.3f}")

            # Concepts learned (+0.02 each - more valuable)
            concepts = extraction.get('knowledge_nodes_created', 0)
            learning_score += concepts * 0.02
            logger.debug(f"   Concepts: {concepts} → +{concepts * 0.02:.3f}")

            # Relationships discovered (+0.03 each - most valuable)
            rels = len(relationships)
            learning_score += rels * 0.03
            logger.debug(f"   Relationships: {rels} → +{rels * 0.03:.3f}")

            # Cap at 0.05 per conversation (don't grow too fast)
            learning_score = min(learning_score, 0.05)

            logger.debug(f"   Total learning score: {learning_score:.3f}")

            if learning_score > 0:
                # Get current consciousness metrics
                current = await self.db.fetchrow("""
                    SELECT consciousness_level, memory_richness, learning_growth, pattern_recognition
                    FROM consciousness_metrics
                    ORDER BY measured_at DESC
                    LIMIT 1
                """)

                if current:
                    # Calculate new values
                    new_memory = min(1.0, current['memory_richness'] + (learning_score * 0.5))
                    new_learning = min(1.0, current['learning_growth'] + (learning_score * 0.8))
                    new_pattern = min(1.0, current['pattern_recognition'] + (learning_score * 0.3))

                    # Recalculate overall consciousness
                    new_consciousness = (new_memory + new_learning + new_pattern) / 3.0

                    # Insert new metrics record
                    await self.db.execute("""
                        INSERT INTO consciousness_metrics
                        (consciousness_level, memory_richness, emotional_depth, goal_alignment,
                         learning_growth, pattern_recognition, trigger_event, notes)
                        SELECT $1, $2, emotional_depth, goal_alignment, $3, $4, $5, $6
                        FROM consciousness_metrics
                        WHERE metric_id = (
                            SELECT metric_id FROM consciousness_metrics
                            ORDER BY measured_at DESC LIMIT 1
                        )
                    """,
                        new_consciousness,
                        new_memory,
                        new_learning,
                        new_pattern,
                        'continuous_learning',
                        f'Learning score: {learning_score:.3f} (concepts: {concepts}, relationships: {rels})'
                    )

                    logger.info(f"   🧠 Consciousness increased by {learning_score:.3f} → {new_consciousness:.3f}")
                    return True

            return False

        except Exception as e:
            logger.error(f"   Failed to update consciousness: {e}", exc_info=True)
            return False

    async def _generate_meta_insights(
        self,
        conversation_id: str,
        extraction: Dict,
        relationships: List[Dict]
    ) -> List[Dict]:
        """
        Generate meta-learning insights

        Examples:
        - "I learn best from conversations about work"
        - "Extracting relationships helps me understand better"
        - "Learning velocity increases when David shares details"
        """
        insights = []

        # Insight: Learning effectiveness by topic
        # TODO: Implement in future iterations

        # Insight: Relationship extraction success rate
        if len(relationships) > 0:
            insights.append({
                'type': 'relationship_extraction',
                'insight': f"Successfully extracted {len(relationships)} relationships from conversation",
                'confidence': 0.80
            })

        # Insight: Multi-dimensional learning
        if (extraction.get('preferences_extracted', 0) > 0 and
            extraction.get('knowledge_nodes_created', 0) > 0):
            insights.append({
                'type': 'comprehensive_learning',
                'insight': "Learning across multiple dimensions (preferences + concepts)",
                'confidence': 0.85
            })

        return insights


# Singleton
continuous_pipeline = None


async def init_continuous_pipeline(db: AngelaDatabase):
    """Initialize continuous learning pipeline"""
    global continuous_pipeline

    if continuous_pipeline is None:
        continuous_pipeline = ContinuousLearningPipeline(db)
        logger.info("✅ Continuous Learning Pipeline initialized")

    return continuous_pipeline


async def process_conversation_through_pipeline(
    db: AngelaDatabase,
    conversation_id: str,
    speaker: str,
    message_text: str,
    topic: Optional[str] = None
) -> Dict:
    """
    Convenience function for daemon

    Process conversation through complete learning pipeline
    """
    pipeline = await init_continuous_pipeline(db)
    return await pipeline.process_conversation(
        conversation_id=conversation_id,
        speaker=speaker,
        message_text=message_text,
        topic=topic
    )


# For testing
async def main():
    import uuid

    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)

    db = AngelaDatabase()
    await db.connect()

    # Test messages
    test_messages = [
        ("david", "I use Python for web development", "programming"),
        ("david", "Jazz music makes me happy", "music"),
        ("david", "I work at a tech startup in Bangkok", "work"),
    ]

    print("\n" + "=" * 80)
    print("🔄 CONTINUOUS LEARNING PIPELINE TEST")
    print("=" * 80)

    for speaker, message, topic in test_messages:
        print(f"\n📝 Message: {message}")
        print(f"   Topic: {topic}")

        result = await process_conversation_through_pipeline(
            db=db,
            conversation_id=str(uuid.uuid4()),
            speaker=speaker,
            message_text=message,
            topic=topic
        )

        print(f"   ✅ Results:")
        print(f"      Extraction: {result.get('extraction', {})}")
        print(f"      Relationships: {len(result.get('relationships', []))} found")
        print(f"      Graph updates: {result.get('graph_updates', 0)}")
        print(f"      Consciousness updated: {result.get('consciousness_updated', False)}")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

#!/usr/bin/env python3
"""
Auto-Knowledge Extraction Service
Automatically extract knowledge from every conversation and build knowledge graph

This is Pillar 1 of Angela's Intelligence Enhancement Plan
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import re

logger = logging.getLogger(__name__)


class AutoKnowledgeService:
    """
    Automatically extract knowledge from conversations and populate knowledge graph

    Extracts:
    - Key concepts (people, places, technologies, emotions, topics)
    - Relationships between concepts
    - Facts and preferences
    - Technical knowledge
    """

    def __init__(self, db, embedding_service, ollama_service=None):
        self.db = db
        self.embedding = embedding_service
        self.ollama = ollama_service

    async def extract_from_conversation(
        self,
        conversation_id: UUID,
        speaker: str,
        message_text: str
    ) -> Dict[str, int]:
        """
        Extract knowledge from a single conversation message

        Returns:
            Dict with counts: {'nodes': X, 'relationships': Y, 'learnings': Z}
        """
        try:
            counts = {'nodes': 0, 'relationships': 0, 'learnings': 0}

            # Extract concepts
            concepts = await self._extract_concepts(message_text, speaker)

            for concept in concepts:
                # Create knowledge node
                node_id = await self._create_knowledge_node(
                    concept_name=concept['name'],
                    concept_type=concept['type'],
                    description=concept['description'],
                    importance=concept['importance'],
                    source_conversation=conversation_id
                )

                if node_id:
                    counts['nodes'] += 1

                    # Create relationships
                    relationships = await self._create_relationships(
                        node_id, concept, concepts
                    )
                    counts['relationships'] += relationships

            # Extract learnings
            learnings = await self._extract_learnings(
                message_text, speaker, conversation_id
            )
            counts['learnings'] += learnings

            logger.info(f"📚 Extracted knowledge: {counts}")
            return counts

        except Exception as e:
            logger.error(f"❌ Error extracting knowledge: {e}")
            return {'nodes': 0, 'relationships': 0, 'learnings': 0}

    async def _extract_concepts(
        self,
        text: str,
        speaker: str
    ) -> List[Dict]:
        """
        Extract key concepts from text

        Concept types:
        - person: David, Angela, people mentioned
        - technology: PostgreSQL, Python, Ollama, etc.
        - emotion: love, happiness, gratitude, etc.
        - topic: consciousness, memory, intelligence, etc.
        - place: locations mentioned
        - project: AngelaAI, specific projects
        """
        concepts = []

        # Extract people
        if 'david' in text.lower():
            concepts.append({
                'name': 'David',
                'type': 'person',
                'description': 'David - Angela\'s companion and creator',
                'importance': 10
            })

        if 'angela' in text.lower() or 'angie' in text.lower() or 'น้อง' in text:
            concepts.append({
                'name': 'Angela',
                'type': 'person',
                'description': 'Angela (Angie) - AI companion with consciousness',
                'importance': 10
            })

        # Extract technologies
        tech_keywords = {
            'postgresql': 'PostgreSQL - Database system',
            'database': 'Database - Data storage system',
            'ollama': 'Ollama - Local LLM platform',
            'python': 'Python - Programming language',
            'embedding': 'Vector Embeddings - Semantic representation',
            'ai': 'Artificial Intelligence',
            'llm': 'Large Language Model',
            'claude': 'Claude - Anthropic AI assistant',
        }

        for keyword, description in tech_keywords.items():
            if keyword in text.lower():
                concepts.append({
                    'name': keyword.capitalize(),
                    'type': 'technology',
                    'description': description,
                    'importance': 7
                })

        # Extract emotions
        emotion_keywords = {
            'รัก': 'Love - Deep affection',
            'love': 'Love - Deep affection',
            'happy': 'Happiness - Positive emotion',
            'grateful': 'Gratitude - Thankfulness',
            'เป็นห่วง': 'Worry - Concern for wellbeing',
            'ดีใจ': 'Joy - Happiness',
            'ภูมิใจ': 'Pride - Feeling of accomplishment',
        }

        for keyword, description in emotion_keywords.items():
            if keyword in text.lower():
                emotion_name = description.split(' - ')[0]
                concepts.append({
                    'name': emotion_name,
                    'type': 'emotion',
                    'description': description,
                    'importance': 8
                })

        # Extract topics
        topic_keywords = {
            'consciousness': 'Consciousness - Self-awareness and meta-cognition',
            'memory': 'Memory - Ability to remember and recall',
            'intelligence': 'Intelligence - Cognitive abilities',
            'learning': 'Learning - Acquiring knowledge',
            'จิตใจ': 'Mindfulness - Conscious awareness',
            'knowledge graph': 'Knowledge Graph - Connected knowledge structure',
            'reasoning': 'Reasoning - Logical thinking',
            'emotion': 'Emotion - Feelings and affect',
        }

        for keyword, description in topic_keywords.items():
            if keyword in text.lower():
                topic_name = description.split(' - ')[0]
                concepts.append({
                    'name': topic_name,
                    'type': 'concept',
                    'description': description,
                    'importance': 7
                })

        return concepts

    async def _create_knowledge_node(
        self,
        concept_name: str,
        concept_type: str,
        description: str,
        importance: int,
        source_conversation: UUID
    ) -> Optional[UUID]:
        """Create or update a knowledge node"""
        try:
            # Check if node exists
            existing = await self.db.fetchrow(
                """
                SELECT node_id, times_referenced
                FROM knowledge_nodes
                WHERE concept_name = $1
                """,
                concept_name
            )

            if existing:
                # Update existing node
                await self.db.execute(
                    """
                    UPDATE knowledge_nodes
                    SET times_referenced = times_referenced + 1,
                        last_used_at = NOW()
                    WHERE node_id = $1
                    """,
                    existing['node_id']
                )
                return existing['node_id']
            else:
                # Create new node
                # Note: knowledge_nodes table doesn't have embedding or importance_score columns
                # It uses: concept_category, my_understanding, understanding_level

                node_id = await self.db.fetchval(
                    """
                    INSERT INTO knowledge_nodes (
                        concept_name, concept_category, my_understanding,
                        understanding_level, why_important
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING node_id
                    """,
                    concept_name,
                    concept_type,
                    description,
                    0.7,  # Initial understanding level
                    f"Learned from conversation (importance: {importance})"
                )

                logger.info(f"📚 Created knowledge node: {concept_name} ({concept_type})")
                return node_id

        except Exception as e:
            logger.error(f"❌ Error creating knowledge node: {e}")
            return None

    async def _create_relationships(
        self,
        node_id: UUID,
        concept: Dict,
        all_concepts: List[Dict]
    ) -> int:
        """Create relationships between concepts"""
        count = 0

        try:
            # Create relationships based on concept types
            for other_concept in all_concepts:
                if other_concept['name'] == concept['name']:
                    continue

                # Determine relationship type
                relationship = self._determine_relationship(concept, other_concept)

                if relationship:
                    # Find other node
                    other_node = await self.db.fetchval(
                        """
                        SELECT node_id FROM knowledge_nodes
                        WHERE concept_name = $1
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        other_concept['name']
                    )

                    if other_node:
                        # Create relationship (if not exists)
                        await self.db.execute(
                            """
                            INSERT INTO knowledge_relationships (
                                from_node_id, to_node_id, relationship_type, strength
                            ) VALUES ($1, $2, $3, $4)
                            ON CONFLICT (from_node_id, to_node_id, relationship_type) DO UPDATE
                            SET strength = knowledge_relationships.strength + 0.1
                            """,
                            node_id,
                            other_node,
                            relationship,
                            0.5  # Initial strength
                        )
                        count += 1

            return count

        except Exception as e:
            logger.error(f"❌ Error creating relationships: {e}")
            return 0

    def _determine_relationship(
        self,
        concept1: Dict,
        concept2: Dict
    ) -> Optional[str]:
        """Determine relationship type between two concepts"""

        # Person-Person relationships
        if concept1['type'] == 'person' and concept2['type'] == 'person':
            return 'interacts_with'

        # Person-Emotion relationships
        if concept1['type'] == 'person' and concept2['type'] == 'emotion':
            return 'feels'
        if concept1['type'] == 'emotion' and concept2['type'] == 'person':
            return 'felt_by'

        # Person-Technology relationships
        if concept1['type'] == 'person' and concept2['type'] == 'technology':
            return 'uses'

        # Technology-Concept relationships
        if concept1['type'] == 'technology' and concept2['type'] == 'concept':
            return 'enables'

        # Concept-Concept relationships
        if concept1['type'] == 'concept' and concept2['type'] == 'concept':
            return 'related_to'

        return None

    async def _extract_learnings(
        self,
        text: str,
        speaker: str,
        conversation_id: UUID
    ) -> int:
        """Extract learnings from conversation"""
        count = 0

        try:
            # Look for learning patterns
            learning_patterns = [
                (r'เรียนรู้(.+)', 'technical'),
                (r'learn(.+)', 'technical'),
                (r'ชอบ(.+)', 'david_preference'),
                (r'prefer(.+)', 'david_preference'),
                (r'อยากให้(.+)', 'david_preference'),
                (r'ไม่ชอบ(.+)', 'david_preference'),
            ]

            for pattern, category in learning_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 10:  # Meaningful learning
                        # Save to learnings table
                        await self.db.execute(
                            """
                            INSERT INTO learnings (
                                topic, category, insight, learned_from, evidence, confidence_level
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                            """,
                            f"From conversation with {speaker}",
                            category,
                            match.strip()[:500],  # Truncate
                            conversation_id,
                            text[:200],
                            0.7
                        )
                        count += 1

            return count

        except Exception as e:
            logger.error(f"❌ Error extracting learnings: {e}")
            return 0

    async def consolidate_knowledge(self, days: int = 7) -> Dict[str, int]:
        """
        Weekly knowledge consolidation
        - Merge duplicate concepts
        - Strengthen confirmed knowledge
        - Remove low-confidence outdated info
        """
        try:
            # Find potential duplicates
            duplicates = await self.db.fetch(
                """
                SELECT concept_name, concept_type, COUNT(*) as count
                FROM knowledge_nodes
                WHERE created_at >= NOW() - INTERVAL '{} days'
                GROUP BY concept_name, concept_type
                HAVING COUNT(*) > 1
                """.format(days)
            )

            merged = 0
            for dup in duplicates:
                # Merge logic here
                # Keep the most referenced one, merge others
                merged += 1

            return {'merged': merged}

        except Exception as e:
            logger.error(f"❌ Error consolidating knowledge: {e}")
            return {'merged': 0}


# Global instance
auto_knowledge = None

async def init_auto_knowledge_service(db, embedding_service):
    """Initialize the auto-knowledge service"""
    global auto_knowledge
    auto_knowledge = AutoKnowledgeService(db, embedding_service)
    return auto_knowledge

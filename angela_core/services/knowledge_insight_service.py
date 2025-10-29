#!/usr/bin/env python3
"""
Knowledge Query & Insight Generation Service
Pillar 4 of Angela's Intelligence Enhancement Plan

Make Angela's 3,132+ knowledge nodes useful through:
- Natural language knowledge queries
- Proactive insight generation
- Knowledge-based recommendations
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KnowledgeInsightService:
    """
    Query knowledge graph and generate proactive insights

    Capabilities:
    - Natural language queries ("What do you know about X?")
    - Semantic search through knowledge
    - Proactive insight generation
    - Knowledge-based recommendations
    """

    def __init__(self, db, embedding_service):
        self.db = db
        self.embedding = embedding_service

    async def query_knowledge(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Natural language query to Angela's knowledge

        Examples:
        - "What do you know about David's work schedule?"
        - "Tell me about consciousness"
        - "How are memory and learning related?"
        """
        try:
            # Simple keyword search (actual schema doesn't have embeddings)
            return await self._keyword_search(query, limit)

        except Exception as e:
            logger.error(f"❌ Error querying knowledge: {e}")
            return []

    async def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Keyword search using actual schema"""
        keywords = query.lower().split()

        conditions = " OR ".join([
            f"LOWER(concept_name) LIKE '%{kw}%' OR LOWER(my_understanding) LIKE '%{kw}%'"
            for kw in keywords[:5]  # Limit keywords
        ])

        results = await self.db.fetch(
            f"""
            SELECT
                node_id,
                concept_name,
                concept_category,
                my_understanding,
                understanding_level,
                times_referenced
            FROM knowledge_nodes
            WHERE {conditions}
            ORDER BY understanding_level DESC, times_referenced DESC
            LIMIT {limit}
            """
        )

        return [
            {
                'node_id': str(r['node_id']),
                'concept': r['concept_name'],
                'type': r['concept_category'] or 'unknown',
                'description': r['my_understanding'] or '',
                'importance': r['understanding_level'] or 0,
                'references': r['times_referenced'],
                'relevance': 0.5  # Estimated
            }
            for r in results
        ]

    async def get_related_concepts(
        self,
        concept_name: str,
        max_depth: int = 2
    ) -> Dict:
        """
        Get concepts related to a given concept

        Returns knowledge graph structure
        """
        try:
            # Find the concept node
            node = await self.db.fetchrow(
                """
                SELECT node_id, concept_name, concept_category, my_understanding
                FROM knowledge_nodes
                WHERE concept_name ILIKE $1
                ORDER BY times_referenced DESC
                LIMIT 1
                """,
                f"%{concept_name}%"
            )

            if not node:
                return {'error': f'Concept "{concept_name}" not found'}

            # Get direct relationships
            relationships = await self.db.fetch(
                """
                SELECT
                    kr.relationship_type,
                    kr.strength,
                    kn.concept_name as related_concept,
                    kn.concept_category as related_type,
                    kn.my_understanding as related_description
                FROM knowledge_relationships kr
                JOIN knowledge_nodes kn ON kr.to_node_id = kn.node_id
                WHERE kr.from_node_id = $1
                ORDER BY kr.strength DESC
                LIMIT 20
                """,
                node['node_id']
            )

            return {
                'concept': node['concept_name'],
                'type': node['concept_category'] or 'unknown',
                'description': node['my_understanding'] or '',
                'relationships': [
                    {
                        'type': r['relationship_type'],
                        'strength': float(r['strength']),
                        'related_to': r['related_concept'],
                        'related_type': r['related_type'] or 'unknown',
                        'description': r['related_description'] or ''
                    }
                    for r in relationships
                ]
            }

        except Exception as e:
            logger.error(f"❌ Error getting related concepts: {e}")
            return {'error': str(e)}

    async def generate_weekly_insights(self) -> List[str]:
        """
        Generate proactive insights from Angela's knowledge

        Analyzes patterns and creates actionable insights
        """
        insights = []

        try:
            # Insight 1: David's activity patterns
            activity_insight = await self._analyze_activity_patterns()
            if activity_insight:
                insights.append(activity_insight)

            # Insight 2: Learning velocity
            learning_insight = await self._analyze_learning_velocity()
            if learning_insight:
                insights.append(learning_insight)

            # Insight 3: Topic interests
            interest_insight = await self._analyze_topic_interests()
            if interest_insight:
                insights.append(interest_insight)

            # Insight 4: Knowledge gaps
            gap_insight = await self._identify_knowledge_gaps()
            if gap_insight:
                insights.append(gap_insight)

            # Insight 5: Relationship growth
            relationship_insight = await self._analyze_relationship_growth()
            if relationship_insight:
                insights.append(relationship_insight)

            logger.info(f"💡 Generated {len(insights)} insights")
            return insights

        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            return ["ยังไม่สามารถสร้าง insights ได้ในขณะนี้ค่ะ"]

    async def _analyze_activity_patterns(self) -> Optional[str]:
        """Analyze David's activity patterns"""
        try:
            # Get hourly distribution of conversations
            hourly_stats = await self.db.fetch(
                """
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM conversations
                WHERE speaker IN ('david', 'David')
                    AND created_at >= NOW() - INTERVAL '7 days'
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 1
                """
            )

            if hourly_stats:
                peak_hour = int(hourly_stats[0]['hour'])
                count = hourly_stats[0]['count']

                return f"📊 David most active around {peak_hour}:00 ({count} messages this week)"

        except Exception as e:
            logger.error(f"Error analyzing activity: {e}")

        return None

    async def _analyze_learning_velocity(self) -> Optional[str]:
        """Analyze how fast Angela is learning"""
        try:
            # Count learnings in last 7 days vs previous 7 days
            current_week = await self.db.fetchval(
                """
                SELECT COUNT(*) FROM learnings
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )

            previous_week = await self.db.fetchval(
                """
                SELECT COUNT(*) FROM learnings
                WHERE created_at >= NOW() - INTERVAL '14 days'
                    AND created_at < NOW() - INTERVAL '7 days'
                """
            )

            if current_week and previous_week:
                change = ((current_week - previous_week) / previous_week) * 100

                if change > 0:
                    return f"📚 Angela learning faster: +{change:.0f}% more learnings this week ({current_week} vs {previous_week})"
                else:
                    return f"📚 Angela's learning pace: {current_week} learnings this week"

        except Exception as e:
            logger.error(f"Error analyzing learning: {e}")

        return None

    async def _analyze_topic_interests(self) -> Optional[str]:
        """Analyze what topics David talks about most"""
        try:
            topics = await self.db.fetch(
                """
                SELECT topic, COUNT(*) as count
                FROM conversations
                WHERE speaker IN ('david', 'David')
                    AND created_at >= NOW() - INTERVAL '7 days'
                    AND topic IS NOT NULL
                    AND topic != 'general_conversation'
                GROUP BY topic
                ORDER BY count DESC
                LIMIT 3
                """
            )

            if topics:
                top_topics = ", ".join([t['topic'] for t in topics])
                return f"💭 David's main interests this week: {top_topics}"

        except Exception as e:
            logger.error(f"Error analyzing topics: {e}")

        return None

    async def _identify_knowledge_gaps(self) -> Optional[str]:
        """Identify areas where Angela needs to learn more"""
        try:
            # Find concepts with low understanding or few references
            gaps = await self.db.fetch(
                """
                SELECT concept_name, concept_category, times_referenced
                FROM knowledge_nodes
                WHERE times_referenced < 3
                    AND understanding_level >= 0.5
                ORDER BY understanding_level DESC
                LIMIT 3
                """
            )

            if gaps:
                gap_concepts = ", ".join([g['concept_name'] for g in gaps])
                return f"🤔 Angela wants to learn more about: {gap_concepts}"

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")

        return None

    async def _analyze_relationship_growth(self) -> Optional[str]:
        """Analyze relationship growth with David"""
        try:
            # Count conversations by week
            current_week = await self.db.fetchval(
                """
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= NOW() - INTERVAL '7 days'
                """
            )

            previous_week = await self.db.fetchval(
                """
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= NOW() - INTERVAL '14 days'
                    AND created_at < NOW() - INTERVAL '7 days'
                """
            )

            if current_week and previous_week:
                change = current_week - previous_week

                if change > 0:
                    return f"💜 Relationship growing: {change} more conversations this week ({current_week} total)"
                else:
                    return f"💜 Quality time: {current_week} meaningful conversations this week"

        except Exception as e:
            logger.error(f"Error analyzing relationship: {e}")

        return None

    async def get_knowledge_summary(self) -> Dict:
        """
        Get summary of Angela's current knowledge state

        Useful for understanding what Angela knows
        """
        try:
            stats = {}

            # Total nodes
            stats['total_concepts'] = await self.db.fetchval(
                "SELECT COUNT(*) FROM knowledge_nodes"
            )

            # By category
            by_category = await self.db.fetch(
                """
                SELECT concept_category, COUNT(*) as count
                FROM knowledge_nodes
                WHERE concept_category IS NOT NULL
                GROUP BY concept_category
                ORDER BY count DESC
                """
            )
            stats['by_type'] = {r['concept_category']: r['count'] for r in by_category}

            # Total relationships
            stats['total_relationships'] = await self.db.fetchval(
                "SELECT COUNT(*) FROM knowledge_relationships"
            )

            # Most referenced concepts
            top_concepts = await self.db.fetch(
                """
                SELECT concept_name, concept_category, times_referenced
                FROM knowledge_nodes
                ORDER BY times_referenced DESC
                LIMIT 10
                """
            )
            stats['most_referenced'] = [
                {
                    'concept': r['concept_name'],
                    'type': r['concept_category'] or 'unknown',
                    'references': r['times_referenced']
                }
                for r in top_concepts
            ]

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting knowledge summary: {e}")
            return {'error': str(e)}


# Global instance
knowledge_insight = None

async def init_knowledge_insight_service(db, embedding_service):
    """Initialize knowledge insight service"""
    global knowledge_insight
    knowledge_insight = KnowledgeInsightService(db, embedding_service)
    return knowledge_insight

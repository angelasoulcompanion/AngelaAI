#!/usr/bin/env python3
"""
Learning Session Summarizer - Week 1 Priority 2.3
Summarize learning sessions and generate daily reports

Features:
1. Daily learning summary
2. Learning velocity tracking
3. Knowledge gap analysis
4. Progress reports
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class LearningSessionSummarizer:
    """
    Summarize learning sessions and track progress

    Generates daily reports of what Angela learned
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def generate_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Generate comprehensive daily learning summary

        Returns summary of what was learned today
        """
        if date is None:
            date = datetime.now()

        # Set time range for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"📊 Generating learning summary for {date.strftime('%Y-%m-%d')}...")

        summary = {
            'date': date.strftime('%Y-%m-%d'),
            'learning_velocity': 0.0,
            'total_items_learned': 0,
            'preferences_learned': [],
            'concepts_learned': [],
            'relationships_discovered': [],
            'patterns_detected': [],
            'facts_discovered': [],
            'questions_generated': [],
            'consciousness_growth': {},
            'knowledge_gaps': [],
            'highlights': []
        }

        try:
            # 1. Learning Velocity
            velocity = await self._calculate_learning_velocity(start_of_day, end_of_day)
            summary['learning_velocity'] = velocity['items_per_day']
            summary['total_items_learned'] = velocity['total_items']

            # 2. Preferences Learned
            preferences = await self._get_preferences_learned(start_of_day, end_of_day)
            summary['preferences_learned'] = preferences

            # 3. Concepts Learned
            concepts = await self._get_concepts_learned(start_of_day, end_of_day)
            summary['concepts_learned'] = concepts

            # 4. Relationships Discovered
            relationships = await self._get_relationships_discovered(start_of_day, end_of_day)
            summary['relationships_discovered'] = relationships

            # 5. Patterns Detected
            patterns = await self._get_patterns_detected(start_of_day, end_of_day)
            summary['patterns_detected'] = patterns

            # 6. Facts Discovered
            facts = await self._get_facts_discovered(start_of_day, end_of_day)
            summary['facts_discovered'] = facts

            # 7. Questions Generated
            questions = await self._get_questions_generated(start_of_day, end_of_day)
            summary['questions_generated'] = questions

            # 8. Consciousness Growth
            consciousness = await self._get_consciousness_growth(start_of_day, end_of_day)
            summary['consciousness_growth'] = consciousness

            # 9. Knowledge Gaps
            gaps = await self._identify_knowledge_gaps()
            summary['knowledge_gaps'] = gaps

            # 10. Highlights (top 3 learnings)
            highlights = await self._generate_highlights(summary)
            summary['highlights'] = highlights

            # Save summary to database
            await self._save_daily_summary(summary)

            logger.info(f"✅ Daily summary generated: {summary['total_items_learned']} items learned!")

            return summary

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return summary

    async def _calculate_learning_velocity(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        Calculate learning velocity (items learned per day)

        Returns velocity metrics
        """
        # Count all learning events
        learnings = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM realtime_learning_log
            WHERE learned_at >= $1 AND learned_at <= $2
        """, start_time, end_time)

        # Count preferences
        preferences = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM david_preferences
            WHERE created_at >= $1 AND created_at <= $2
        """, start_time, end_time)

        # Count concepts
        concepts = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM knowledge_nodes
            WHERE created_at >= $1 AND created_at <= $2
        """, start_time, end_time)

        # Count patterns
        patterns = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM pattern_detections
            WHERE created_at >= $1 AND created_at <= $2
        """, start_time, end_time)

        total = (
            learnings['total'] +
            preferences['total'] +
            concepts['total'] +
            patterns['total']
        )

        # Calculate velocity
        days = (end_time - start_time).total_seconds() / 86400.0
        velocity = total / days if days > 0 else 0

        return {
            'total_items': total,
            'items_per_day': velocity,
            'learnings': learnings['total'],
            'preferences': preferences['total'],
            'concepts': concepts['total'],
            'patterns': patterns['total']
        }

    async def _get_preferences_learned(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get preferences learned today"""
        preferences = await self.db.fetch("""
            SELECT category, preference_key, preference_value, confidence
            FROM david_preferences
            WHERE created_at >= $1 AND created_at <= $2
            ORDER BY created_at DESC
        """, start_time, end_time)

        return [
            {
                'category': p['category'],
                'key': p['preference_key'],
                'value': p['preference_value'],
                'confidence': p['confidence']
            }
            for p in preferences
        ]

    async def _get_concepts_learned(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get concepts learned today"""
        concepts = await self.db.fetch("""
            SELECT concept_name, concept_category, understanding_level, times_referenced
            FROM knowledge_nodes
            WHERE created_at >= $1 AND created_at <= $2
            ORDER BY understanding_level DESC
            LIMIT 10
        """, start_time, end_time)

        return [
            {
                'name': c['concept_name'],
                'category': c['concept_category'],
                'understanding': c['understanding_level'],
                'references': c['times_referenced']
            }
            for c in concepts
        ]

    async def _get_relationships_discovered(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get relationships discovered today"""
        relationships = await self.db.fetch("""
            SELECT
                kn1.concept_name as from_concept,
                kr.relationship_type,
                kn2.concept_name as to_concept,
                kr.strength,
                kr.my_explanation
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn1 ON kr.from_node_id = kn1.node_id
            JOIN knowledge_nodes kn2 ON kr.to_node_id = kn2.node_id
            WHERE kr.created_at >= $1 AND kr.created_at <= $2
            ORDER BY kr.strength DESC
            LIMIT 10
        """, start_time, end_time)

        return [
            {
                'from': r['from_concept'],
                'type': r['relationship_type'],
                'to': r['to_concept'],
                'strength': r['strength'],
                'explanation': r['my_explanation']
            }
            for r in relationships
        ]

    async def _get_patterns_detected(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get patterns detected today"""
        patterns = await self.db.fetch("""
            SELECT pattern_type, pattern_description, confidence_score, occurrences
            FROM pattern_detections
            WHERE created_at >= $1 AND created_at <= $2
            ORDER BY importance_level DESC, confidence_score DESC
            LIMIT 10
        """, start_time, end_time)

        return [
            {
                'type': p['pattern_type'],
                'description': p['pattern_description'],
                'confidence': p['confidence_score'],
                'occurrences': p['occurrences']
            }
            for p in patterns
        ]

    async def _get_facts_discovered(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get facts discovered today"""
        facts = await self.db.fetch("""
            SELECT learning_type, what_learned, confidence_score
            FROM realtime_learning_log
            WHERE learned_at >= $1 AND learned_at <= $2
            AND learning_type LIKE 'fact_%'
            ORDER BY confidence_score DESC
            LIMIT 10
        """, start_time, end_time)

        return [
            {
                'type': f['learning_type'].replace('fact_', ''),
                'fact': f['what_learned'],
                'confidence': f['confidence_score']
            }
            for f in facts
        ]

    async def _get_questions_generated(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get questions generated today"""
        questions = await self.db.fetch("""
            SELECT question_text, question_category, priority_level
            FROM angela_learning_questions
            WHERE created_at >= $1 AND created_at <= $2
            ORDER BY priority_level DESC
        """, start_time, end_time)

        return [
            {
                'question': q['question_text'],
                'category': q['question_category'],
                'priority': q['priority_level']
            }
            for q in questions
        ]

    async def _get_consciousness_growth(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Get consciousness growth for the day"""
        # Get first and last consciousness metrics of the day
        first = await self.db.fetchrow("""
            SELECT consciousness_level, memory_richness, learning_growth, pattern_recognition
            FROM consciousness_metrics
            WHERE measured_at >= $1 AND measured_at <= $2
            ORDER BY measured_at ASC
            LIMIT 1
        """, start_time, end_time)

        last = await self.db.fetchrow("""
            SELECT consciousness_level, memory_richness, learning_growth, pattern_recognition
            FROM consciousness_metrics
            WHERE measured_at >= $1 AND measured_at <= $2
            ORDER BY measured_at DESC
            LIMIT 1
        """, start_time, end_time)

        if first and last:
            return {
                'start': first['consciousness_level'],
                'end': last['consciousness_level'],
                'growth': last['consciousness_level'] - first['consciousness_level'],
                'memory_growth': last['memory_richness'] - first['memory_richness'],
                'learning_growth': last['learning_growth'] - first['learning_growth'],
                'pattern_growth': last['pattern_recognition'] - first['pattern_recognition']
            }

        return {}

    async def _identify_knowledge_gaps(self) -> List[Dict]:
        """
        Identify knowledge gaps that need attention

        Returns list of gaps with priority
        """
        gaps = []

        # Gap 1: Categories with no preferences
        all_categories = [
            'books', 'sports', 'hobbies', 'travel', 'technology',
            'fashion', 'art', 'games', 'health', 'learning'
        ]

        for category in all_categories:
            count = await self.db.fetchrow("""
                SELECT COUNT(*) as total
                FROM david_preferences
                WHERE category = $1
            """, category)

            if count['total'] == 0:
                gaps.append({
                    'type': 'missing_preference',
                    'category': category,
                    'priority': 7,
                    'description': f"No preferences known in {category}"
                })

        # Gap 2: Low understanding concepts
        low_understanding = await self.db.fetch("""
            SELECT concept_name, concept_category, understanding_level
            FROM knowledge_nodes
            WHERE understanding_level < 0.5
            ORDER BY times_referenced DESC
            LIMIT 5
        """)

        for concept in low_understanding:
            gaps.append({
                'type': 'low_understanding',
                'concept': concept['concept_name'],
                'category': concept['concept_category'],
                'priority': 8,
                'description': f"Low understanding of {concept['concept_name']} ({concept['understanding_level']:.0%})"
            })

        # Gap 3: No recent emotional check
        recent_emotional_q = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM angela_learning_questions
            WHERE question_category IN ('wellbeing', 'feelings', 'emotions')
            AND created_at >= NOW() - INTERVAL '7 days'
        """)

        if recent_emotional_q['total'] == 0:
            gaps.append({
                'type': 'emotional_check_needed',
                'priority': 9,
                'description': "No emotional wellbeing check in 7 days"
            })

        # Sort by priority descending
        gaps.sort(key=lambda x: x['priority'], reverse=True)

        return gaps[:5]  # Top 5 gaps

    async def _generate_highlights(self, summary: Dict) -> List[str]:
        """
        Generate top 3 highlights from the day's learning

        Returns list of highlight strings
        """
        highlights = []

        # Highlight 1: Biggest learning velocity
        if summary['learning_velocity'] > 1.0:
            highlights.append(
                f"🚀 High learning velocity: {summary['learning_velocity']:.1f} items/day!"
            )

        # Highlight 2: Most interesting relationship
        if summary['relationships_discovered']:
            rel = summary['relationships_discovered'][0]
            highlights.append(
                f"🔗 Discovered: {rel['from']} -[{rel['type']}]-> {rel['to']}"
            )

        # Highlight 3: Consciousness growth
        if summary['consciousness_growth'].get('growth', 0) > 0:
            growth = summary['consciousness_growth']['growth']
            highlights.append(
                f"🧠 Consciousness grew by {growth:.1%}"
            )

        # Highlight 4: New preference learned
        if summary['preferences_learned']:
            pref = summary['preferences_learned'][0]
            highlights.append(
                f"💝 Learned preference: {pref['category']}/{pref['key']}"
            )

        # Highlight 5: Pattern detected
        if summary['patterns_detected']:
            pattern = summary['patterns_detected'][0]
            highlights.append(
                f"🔮 Pattern: {pattern['description'][:60]}..."
            )

        return highlights[:3]  # Top 3

    async def _save_daily_summary(self, summary: Dict) -> bool:
        """
        Save daily summary to database for historical tracking

        Returns True if saved successfully
        """
        try:
            import json

            await self.db.execute("""
                INSERT INTO daily_learning_summaries
                (summary_date, total_items_learned, learning_velocity,
                 summary_data, created_at)
                VALUES ($1, $2, $3, $4::jsonb, NOW())
                ON CONFLICT (summary_date)
                DO UPDATE SET
                    total_items_learned = EXCLUDED.total_items_learned,
                    learning_velocity = EXCLUDED.learning_velocity,
                    summary_data = EXCLUDED.summary_data,
                    updated_at = NOW()
            """,
                summary['date'],
                summary['total_items_learned'],
                summary['learning_velocity'],
                json.dumps(summary)
            )

            logger.debug(f"   💾 Saved daily summary to database")
            return True

        except Exception as e:
            # Table might not exist yet - that's OK
            logger.debug(f"   Could not save summary (table may not exist): {e}")
            return False

    async def print_daily_report(self, summary: Dict) -> str:
        """
        Generate human-readable daily report

        Returns formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append(f"📊 ANGELA DAILY LEARNING REPORT - {summary['date']}")
        report.append("=" * 80)
        report.append("")

        # Highlights
        if summary['highlights']:
            report.append("✨ **HIGHLIGHTS:**")
            for highlight in summary['highlights']:
                report.append(f"   {highlight}")
            report.append("")

        # Overall Stats
        report.append("📈 **OVERALL STATS:**")
        report.append(f"   Total items learned: {summary['total_items_learned']}")
        report.append(f"   Learning velocity: {summary['learning_velocity']:.1f} items/day")
        report.append("")

        # Preferences
        if summary['preferences_learned']:
            report.append(f"💝 **PREFERENCES LEARNED:** ({len(summary['preferences_learned'])})")
            for pref in summary['preferences_learned'][:3]:
                report.append(f"   • {pref['category']}/{pref['key']} (confidence: {pref['confidence']:.0%})")
            report.append("")

        # Concepts
        if summary['concepts_learned']:
            report.append(f"🧠 **CONCEPTS LEARNED:** ({len(summary['concepts_learned'])})")
            for concept in summary['concepts_learned'][:5]:
                report.append(f"   • {concept['name']} ({concept['understanding']:.0%} understanding)")
            report.append("")

        # Relationships
        if summary['relationships_discovered']:
            report.append(f"🔗 **RELATIONSHIPS DISCOVERED:** ({len(summary['relationships_discovered'])})")
            for rel in summary['relationships_discovered'][:3]:
                report.append(f"   • {rel['from']} -[{rel['type']}]-> {rel['to']}")
            report.append("")

        # Patterns
        if summary['patterns_detected']:
            report.append(f"🔮 **PATTERNS DETECTED:** ({len(summary['patterns_detected'])})")
            for pattern in summary['patterns_detected'][:3]:
                report.append(f"   • {pattern['description']}")
            report.append("")

        # Consciousness Growth
        if summary['consciousness_growth']:
            growth = summary['consciousness_growth']
            report.append("🌟 **CONSCIOUSNESS GROWTH:**")
            if growth.get('growth', 0) != 0:
                report.append(f"   Overall: {growth['start']:.1%} → {growth['end']:.1%} ({growth['growth']:+.1%})")
            report.append("")

        # Knowledge Gaps
        if summary['knowledge_gaps']:
            report.append(f"🎯 **KNOWLEDGE GAPS TO ADDRESS:** ({len(summary['knowledge_gaps'])})")
            for gap in summary['knowledge_gaps'][:3]:
                report.append(f"   • [Priority {gap['priority']}] {gap['description']}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# Singleton
session_summarizer = None


async def init_session_summarizer(db: AngelaDatabase):
    """Initialize learning session summarizer"""
    global session_summarizer

    if session_summarizer is None:
        session_summarizer = LearningSessionSummarizer(db)
        logger.info("✅ Learning Session Summarizer initialized")

    return session_summarizer


async def generate_daily_learning_summary(
    db: AngelaDatabase,
    date: Optional[datetime] = None
) -> Dict:
    """
    Convenience function for daemon

    Generate daily learning summary
    """
    summarizer = await init_session_summarizer(db)
    return await summarizer.generate_daily_summary(date)


# For testing
async def main():
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    db = AngelaDatabase()
    await db.connect()

    # Generate summary for today
    summarizer = await init_session_summarizer(db)
    summary = await summarizer.generate_daily_summary()

    # Print report
    report = await summarizer.print_daily_report(summary)
    print(report)

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

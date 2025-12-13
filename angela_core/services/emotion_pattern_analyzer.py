"""
Emotion Pattern Analyzer Service (Option 3)
Analyzes historical emotional data to discover patterns, trends, correlations, and triggers
Runs daily to enable continuous learning about Angela's emotional patterns

⚠️ DEPRECATION WARNING ⚠️
This service has been migrated to Clean Architecture:
    New location: angela_core.application.services.emotional_intelligence_service
    Functionality: EmotionalIntelligenceService.analyze_emotion_patterns()
    This file is kept for backward compatibility only.
    Please update your imports to use the new service.
    Migration: Batch-15 (2025-10-31)

Different from Real-time Tracker:
- Real-time Tracker = monitors current state (every 30 min)
- Pattern Analyzer = learns from history (daily)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from collections import defaultdict
import statistics


class EmotionPatternAnalyzer:
    """Service for analyzing historical emotional patterns"""

    def __init__(self, db_connection):
        self.db = db_connection

    async def _get_db_connection(self):
        """Get database connection"""

    # =====================================================================
    # Data Collection Methods
    # =====================================================================

    async def _get_emotional_states_history(self, days: int = 30) -> List[Dict]:
        """Get emotional states from last N days"""
        query = """
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
            WHERE created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC
        """
        rows = await self.db.fetch(query % days)
        return [dict(row) for row in rows]

    async def _get_significant_emotions_history(self, days: int = 30) -> List[Dict]:
        """Get significant emotional moments from last N days"""
        query = """
            SELECT
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters,
                memory_strength,
                felt_at
            FROM angela_emotions
            WHERE felt_at >= NOW() - INTERVAL '%s days'
            ORDER BY felt_at ASC
        """
        rows = await self.db.fetch(query % days)
        return [dict(row) for row in rows]

    async def _get_conversations_history(self, days: int = 30) -> List[Dict]:
        """Get conversations from last N days"""
        query = """
            SELECT
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC
        """
        rows = await self.db.fetch(query % days)
        return [dict(row) for row in rows]

    async def _get_actions_history(self, days: int = 30) -> List[Dict]:
        """Get autonomous actions from last N days"""
        query = """
            SELECT
                action_type,
                action_description,
                status,
                success,
                created_at
            FROM autonomous_actions
            WHERE created_at >= NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC
        """
        rows = await self.db.fetch(query % days)
        return [dict(row) for row in rows]

    # =====================================================================
    # Pattern Analysis Methods
    # =====================================================================

    def _analyze_time_based_patterns(self, states: List[Dict]) -> Dict:
        """Analyze emotional patterns based on time of day"""

        # Group by hour of day
        emotions_by_hour = defaultdict(lambda: {
            'happiness': [], 'confidence': [], 'anxiety': [],
            'motivation': [], 'gratitude': [], 'loneliness': []
        })

        for state in states:
            hour = state['created_at'].hour
            emotions_by_hour[hour]['happiness'].append(state['happiness'])
            emotions_by_hour[hour]['confidence'].append(state['confidence'])
            emotions_by_hour[hour]['anxiety'].append(state['anxiety'])
            emotions_by_hour[hour]['motivation'].append(state['motivation'])
            emotions_by_hour[hour]['gratitude'].append(state['gratitude'])
            emotions_by_hour[hour]['loneliness'].append(state['loneliness'])

        # Calculate averages
        patterns = {}
        for hour, emotions in emotions_by_hour.items():
            patterns[hour] = {
                emotion: statistics.mean(values) if values else 0.5
                for emotion, values in emotions.items()
            }

        # Identify best and worst hours
        best_hour = max(patterns.items(),
                       key=lambda x: x[1]['happiness'] - x[1]['anxiety'])[0]
        worst_hour = min(patterns.items(),
                        key=lambda x: x[1]['happiness'] - x[1]['anxiety'])[0]

        return {
            'hourly_patterns': patterns,
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'pattern_description': f"Angela feels best around {best_hour}:00, struggles more around {worst_hour}:00"
        }

    def _analyze_emotional_triggers(
        self,
        states: List[Dict],
        conversations: List[Dict],
        emotions: List[Dict]
    ) -> Dict:
        """Identify what triggers significant emotional changes"""

        triggers = defaultdict(lambda: {
            'happiness_increase': 0,
            'confidence_increase': 0,
            'anxiety_increase': 0,
            'count': 0
        })

        # Analyze triggered_by field in emotional_states
        for state in states:
            trigger = state.get('triggered_by', 'unknown')
            if trigger and trigger != 'unknown':
                # Track which emotions increased
                if state.get('happiness', 0) > 0.7:
                    triggers[trigger]['happiness_increase'] += 1
                if state.get('confidence', 0) > 0.7:
                    triggers[trigger]['confidence_increase'] += 1
                if state.get('anxiety', 0) > 0.3:
                    triggers[trigger]['anxiety_increase'] += 1
                triggers[trigger]['count'] += 1

        # Analyze significant emotions context
        context_keywords = defaultdict(int)
        for emo in emotions:
            context = emo.get('context', '') or ''  # Handle None values
            david_words = emo.get('david_words', '') or ''  # Handle None values

            # Extract keywords (simple approach)
            if 'successful' in context.lower() or 'success' in david_words.lower():
                context_keywords['successful_tasks'] += 1
            if 'conversation' in context.lower() or 'talk' in david_words.lower():
                context_keywords['conversations'] += 1
            if 'help' in david_words.lower() or 'support' in context.lower():
                context_keywords['helping_david'] += 1
            if 'learn' in context.lower() or 'knowledge' in context.lower():
                context_keywords['learning'] += 1

        # Find top triggers
        top_triggers = sorted(triggers.items(),
                             key=lambda x: x[1]['count'],
                             reverse=True)[:5]

        top_keywords = sorted(context_keywords.items(),
                             key=lambda x: x[1],
                             reverse=True)[:5]

        return {
            'triggers': dict(triggers),
            'top_triggers': top_triggers,
            'context_keywords': dict(context_keywords),
            'top_keywords': top_keywords,
            'most_common_trigger': top_triggers[0][0] if top_triggers else 'none'
        }

    def _analyze_trends(self, states: List[Dict]) -> Dict:
        """Analyze emotional trends over time"""

        if len(states) < 7:  # Need at least a week of data
            return {'trend': 'insufficient_data', 'details': 'Need at least 7 days of data'}

        # Split into first half and second half
        mid_point = len(states) // 2
        first_half = states[:mid_point]
        second_half = states[mid_point:]

        def avg_emotions(states_list):
            return {
                'happiness': statistics.mean([s['happiness'] for s in states_list]),
                'confidence': statistics.mean([s['confidence'] for s in states_list]),
                'anxiety': statistics.mean([s['anxiety'] for s in states_list]),
                'motivation': statistics.mean([s['motivation'] for s in states_list]),
                'gratitude': statistics.mean([s['gratitude'] for s in states_list]),
                'loneliness': statistics.mean([s['loneliness'] for s in states_list])
            }

        first_avg = avg_emotions(first_half)
        second_avg = avg_emotions(second_half)

        # Calculate changes
        changes = {
            emotion: second_avg[emotion] - first_avg[emotion]
            for emotion in first_avg.keys()
        }

        # Determine overall trend
        positive_emotions = ['happiness', 'confidence', 'motivation', 'gratitude']
        negative_emotions = ['anxiety', 'loneliness']

        positive_change = sum(changes[e] for e in positive_emotions if e in changes)
        negative_change = sum(changes[e] for e in negative_emotions if e in changes)

        overall_change = positive_change - negative_change

        if overall_change > 0.1:
            trend = 'improving'
        elif overall_change < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'overall_change': overall_change,
            'changes_by_emotion': changes,
            'first_period_avg': first_avg,
            'second_period_avg': second_avg,
            'biggest_improvement': max(changes.items(), key=lambda x: x[1])[0],
            'biggest_decline': min(changes.items(), key=lambda x: x[1])[0]
        }

    def _analyze_correlations(
        self,
        states: List[Dict],
        conversations: List[Dict],
        actions: List[Dict]
    ) -> Dict:
        """Find correlations between activities and emotions"""

        correlations = {}

        # Conversation frequency vs happiness
        # Group by day
        daily_data = defaultdict(lambda: {'conversations': 0, 'happiness': [], 'confidence': []})

        for conv in conversations:
            day = conv['created_at'].date()
            daily_data[day]['conversations'] += 1

        for state in states:
            day = state['created_at'].date()
            daily_data[day]['happiness'].append(state['happiness'])
            daily_data[day]['confidence'].append(state['confidence'])

        # Calculate correlation (simplified)
        days_with_data = [
            (data['conversations'], statistics.mean(data['happiness']) if data['happiness'] else 0.5)
            for data in daily_data.values()
            if data['happiness']
        ]

        if len(days_with_data) > 5:
            # Simple correlation: more conversations = happier?
            high_conv_days = [h for c, h in days_with_data if c > 50]
            low_conv_days = [h for c, h in days_with_data if c <= 50]

            if high_conv_days and low_conv_days:
                high_conv_avg = statistics.mean(high_conv_days)
                low_conv_avg = statistics.mean(low_conv_days)

                correlations['conversation_happiness'] = {
                    'correlation': 'positive' if high_conv_avg > low_conv_avg else 'negative',
                    'high_conv_happiness': high_conv_avg,
                    'low_conv_happiness': low_conv_avg,
                    'difference': high_conv_avg - low_conv_avg
                }

        # Success rate vs confidence
        daily_success = defaultdict(lambda: {'successes': 0, 'failures': 0, 'confidence': []})

        for action in actions:
            day = action['created_at'].date()
            if action.get('success'):
                daily_success[day]['successes'] += 1
            else:
                daily_success[day]['failures'] += 1

        for state in states:
            day = state['created_at'].date()
            daily_success[day]['confidence'].append(state['confidence'])

        # Calculate success rate correlation
        success_rate_data = [
            (
                data['successes'] / (data['successes'] + data['failures']) if (data['successes'] + data['failures']) > 0 else 0,
                statistics.mean(data['confidence']) if data['confidence'] else 0.5
            )
            for data in daily_success.values()
            if data['confidence']
        ]

        if len(success_rate_data) > 5:
            high_success = [c for sr, c in success_rate_data if sr > 0.8]
            low_success = [c for sr, c in success_rate_data if sr <= 0.8]

            if high_success and low_success:
                correlations['success_confidence'] = {
                    'correlation': 'positive',
                    'high_success_confidence': statistics.mean(high_success),
                    'low_success_confidence': statistics.mean(low_success),
                    'difference': statistics.mean(high_success) - statistics.mean(low_success)
                }

        return correlations

    # =====================================================================
    # Pattern Storage Methods
    # =====================================================================

    async def _store_pattern_as_learning(
        self,
        pattern_type: str,
        pattern_description: str,
        evidence: str,
        confidence_level: float
    ):
        """Store discovered pattern as a learning"""

        query = """
            INSERT INTO learnings (
                topic,
                category,
                insight,
                evidence,
                confidence_level,
                times_reinforced,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, 1, NOW())
            ON CONFLICT (topic, insight)
            DO UPDATE SET
                times_reinforced = learnings.times_reinforced + 1,
                confidence_level = GREATEST(learnings.confidence_level, $5),
                evidence = $4
            RETURNING learning_id::text
        """

        try:
            result = await self.db.fetchval(
                query,
                f"emotional_patterns_{pattern_type}",
                "emotional_intelligence",
                pattern_description,
                evidence,
                confidence_level
            )
            print(f"   ✅ Stored pattern: {pattern_type} - {result}")
            return result
        except Exception as e:
            print(f"   ⚠️  Error storing pattern: {e}")
            return None

    # =====================================================================
    # Main Analysis Method
    # =====================================================================

    async def analyze_emotion_patterns(self, days: int = 30) -> Dict:
        """
        Main method: Analyze emotional patterns from last N days
        Called daily by daemon

        Returns:
            Dictionary with all discovered patterns
        """
        print("\n🔮 Emotion Pattern Analysis - Analyzing emotional history...")
        print(f"   📊 Analyzing last {days} days of data...\n")

        # Collect data
        states = await self._get_emotional_states_history(days)
        emotions = await self._get_significant_emotions_history(days)
        conversations = await self._get_conversations_history(days)
        actions = await self._get_actions_history(days)

        print(f"   📊 Data collected: {len(states)} states, {len(emotions)} emotions, {len(conversations)} conversations, {len(actions)} actions")

        if len(states) < 5:
            print("   ⚠️  Not enough data for pattern analysis")
            return {'status': 'insufficient_data'}

        # Analyze patterns
        print("\n   🔍 Analyzing time-based patterns...")
        time_patterns = self._analyze_time_based_patterns(states)

        print("   🔍 Analyzing emotional triggers...")
        triggers = self._analyze_emotional_triggers(states, conversations, emotions)

        print("   🔍 Analyzing emotional trends...")
        trends = self._analyze_trends(states)

        print("   🔍 Analyzing correlations...")
        correlations = self._analyze_correlations(states, conversations, actions)

        # Store important patterns as learnings
        print("\n   💾 Storing discovered patterns...\n")

        # Store time pattern
        await self._store_pattern_as_learning(
            'time_based',
            time_patterns['pattern_description'],
            f"Analysis of {len(states)} emotional states over {days} days",
            0.8
        )

        # Store trend
        if trends.get('trend') != 'insufficient_data':
            trend_desc = f"Emotional trend over last {days} days: {trends['trend']}"
            if trends['trend'] == 'improving':
                trend_desc += f" (biggest improvement: {trends['biggest_improvement']})"
            elif trends['trend'] == 'declining':
                trend_desc += f" (biggest decline: {trends['biggest_decline']})"

            await self._store_pattern_as_learning(
                'trend',
                trend_desc,
                f"Overall change: {trends['overall_change']:.3f}",
                0.75
            )

        # Store top trigger
        if triggers['top_triggers']:
            trigger_name, trigger_data = triggers['top_triggers'][0]
            trigger_desc = f"Most common emotional trigger: {trigger_name} ({trigger_data['count']} times)"

            await self._store_pattern_as_learning(
                'triggers',
                trigger_desc,
                f"Happiness↑: {trigger_data['happiness_increase']}, Confidence↑: {trigger_data['confidence_increase']}",
                0.7
            )

        # Store correlations
        for corr_type, corr_data in correlations.items():
            if corr_data.get('correlation') == 'positive' and corr_data.get('difference', 0) > 0.05:
                corr_desc = f"{corr_type.replace('_', ' ').title()}: {corr_data['correlation']} correlation"
                await self._store_pattern_as_learning(
                    'correlation',
                    corr_desc,
                    f"Difference: {corr_data['difference']:.3f}",
                    0.65
                )

        print("\n   ✅ Pattern analysis complete!\n")

        # Return all results
        return {
            'status': 'success',
            'time_patterns': time_patterns,
            'triggers': triggers,
            'trends': trends,
            'correlations': correlations,
            'data_points': {
                'states': len(states),
                'emotions': len(emotions),
                'conversations': len(conversations),
                'actions': len(actions)
            }
        }


# =====================================================================
# Global Instance
# =====================================================================

async def init_pattern_analyzer(db):
    """Initialize pattern analyzer with database connection"""
    analyzer = EmotionPatternAnalyzer(db)
    print("✅ Emotion Pattern Analyzer initialized!")
    return analyzer


# =====================================================================
# Main Entry Point (for testing)
# =====================================================================

async def main():
    """Test the pattern analyzer"""
    from angela_core.database import db

    await db.connect()

    analyzer = await init_pattern_analyzer(db)
    results = await analyzer.analyze_emotion_patterns(days=30)

    print("\n" + "="*70)
    print("📊 Analysis Results:")
    print("="*70)

    if results.get('status') == 'success':
        print(f"\n🕐 Time Patterns:")
        print(f"   Best hour: {results['time_patterns']['best_hour']}:00")
        print(f"   Worst hour: {results['time_patterns']['worst_hour']}:00")
        print(f"   {results['time_patterns']['pattern_description']}")

        print(f"\n📈 Trends:")
        print(f"   Overall trend: {results['trends']['trend']}")
        if results['trends']['trend'] != 'insufficient_data':
            print(f"   Biggest improvement: {results['trends']['biggest_improvement']}")

        print(f"\n🎯 Triggers:")
        if results['triggers']['top_triggers']:
            top = results['triggers']['top_triggers'][0]
            print(f"   Most common: {top[0]} ({top[1]['count']} times)")

        print(f"\n🔗 Correlations:")
        for corr_type, corr_data in results['correlations'].items():
            print(f"   {corr_type}: {corr_data.get('correlation', 'none')}")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

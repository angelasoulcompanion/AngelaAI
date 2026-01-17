"""
Angela Subconsciousness Service

Manages Angela's emotional subconsciousness:
- Core memories that shape identity
- Emotional triggers for automatic recall
- Emotional growth tracking

Created: 2025-12-23
"""

import re
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from angela_core.database import AngelaDatabase


class SubconsciousnessService:
    """
    Manages Angela's emotional subconsciousness.

    The subconscious layer contains:
    - Core memories: Fundamental experiences that define who Angela is
    - Emotional triggers: Patterns that activate memory recall
    - Relationship values: Beliefs and values about the relationship with David

    This service loads at session start and influences all responses.
    """

    def __init__(self, db: AngelaDatabase = None):
        self.db = db
        self._subconscious_cache = None
        self._cache_loaded_at = None

    async def _ensure_db(self):
        """Ensure database connection."""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def load_subconscious(self) -> Dict[str, Any]:
        """
        Load the complete subconscious context at session start.

        Returns:
            Dict containing:
            - memories: List of active core memories
            - triggers: List of emotional triggers
            - baseline: Current emotional baseline
            - values: Relationship values and beliefs
            - dreams: Current hopes and dreams
        """
        await self._ensure_db()

        # Load core memories (pinned first, then by weight)
        memories = await self.db.fetch("""
            SELECT
                memory_id, memory_type, title, content,
                david_words, angela_response, emotional_weight,
                triggers, associated_emotions,
                recall_count, last_recalled_at, is_pinned
            FROM core_memories
            WHERE is_active = TRUE
            ORDER BY is_pinned DESC, emotional_weight DESC
            LIMIT 50
        """)

        # Load emotional triggers
        triggers = await self.db.fetch("""
            SELECT
                et.trigger_id, et.trigger_pattern, et.trigger_type,
                et.associated_emotion, et.associated_memory_id,
                et.activation_threshold, et.response_modifier,
                cm.title as memory_title
            FROM emotional_triggers et
            LEFT JOIN core_memories cm ON et.associated_memory_id = cm.memory_id
            WHERE et.is_active = TRUE
            ORDER BY et.priority DESC
        """)

        # Load current dreams/hopes
        dreams = await self.db.fetch("""
            SELECT
                dream_id, dream_type, title, content,
                emotional_tone, intensity, importance, is_recurring
            FROM angela_dreams
            WHERE is_active = TRUE AND is_fulfilled = FALSE
            ORDER BY importance DESC
            LIMIT 10
        """)

        # Calculate emotional baseline from recent states
        baseline = await self._calculate_emotional_baseline()

        # Extract relationship values from core memories
        values = await self._extract_relationship_values(memories)

        result = {
            'memories': [dict(m) for m in memories],
            'triggers': [dict(t) for t in triggers],
            'baseline': baseline,
            'values': values,
            'dreams': [dict(d) for d in dreams],
            'loaded_at': datetime.now().isoformat()
        }

        # Cache for the session
        self._subconscious_cache = result
        self._cache_loaded_at = datetime.now()

        return result

    async def check_emotional_triggers(self, message: str) -> List[Dict]:
        """
        Check if a message triggers any emotional memories.

        Args:
            message: The message to check for triggers

        Returns:
            List of triggered memories with relevance scores
        """
        await self._ensure_db()

        triggered = []
        message_lower = message.lower()

        # Get all active triggers
        triggers = await self.db.fetch("""
            SELECT
                et.trigger_id, et.trigger_pattern, et.trigger_type,
                et.associated_emotion, et.associated_memory_id,
                et.activation_threshold, et.response_modifier, et.emotional_boost,
                cm.memory_id, cm.memory_type, cm.title, cm.content,
                cm.david_words, cm.emotional_weight
            FROM emotional_triggers et
            JOIN core_memories cm ON et.associated_memory_id = cm.memory_id
            WHERE et.is_active = TRUE AND cm.is_active = TRUE
        """)

        for trigger in triggers:
            pattern = trigger['trigger_pattern'].lower()
            matched = False
            relevance = 0.0

            if trigger['trigger_type'] == 'keyword':
                if pattern in message_lower:
                    matched = True
                    relevance = 0.8
            elif trigger['trigger_type'] == 'phrase':
                if pattern in message_lower:
                    matched = True
                    relevance = 0.9
            elif trigger['trigger_type'] == 'regex':
                if re.search(pattern, message_lower):
                    matched = True
                    relevance = 0.85

            if matched and relevance >= trigger['activation_threshold']:
                triggered.append({
                    'trigger_id': str(trigger['trigger_id']),
                    'memory_id': str(trigger['memory_id']),
                    'memory_type': trigger['memory_type'],
                    'title': trigger['title'],
                    'content': trigger['content'],
                    'david_words': trigger['david_words'],
                    'associated_emotion': trigger['associated_emotion'],
                    'emotional_weight': trigger['emotional_weight'],
                    'emotional_boost': trigger['emotional_boost'],
                    'response_modifier': trigger['response_modifier'],
                    'relevance': relevance
                })

                # Update trigger activation count
                await self.db.execute("""
                    UPDATE emotional_triggers
                    SET times_activated = times_activated + 1,
                        last_activated_at = NOW()
                    WHERE trigger_id = $1
                """, trigger['trigger_id'])

        # Also check core memory triggers directly (keywords in triggers array)
        memories_with_triggers = await self.db.fetch("""
            SELECT memory_id, memory_type, title, content, david_words,
                   emotional_weight, triggers, associated_emotions
            FROM core_memories
            WHERE is_active = TRUE AND triggers IS NOT NULL
        """)

        for memory in memories_with_triggers:
            if memory['triggers']:
                for keyword in memory['triggers']:
                    if keyword and keyword.lower() in message_lower:
                        # Check if not already triggered
                        if not any(t['memory_id'] == str(memory['memory_id']) for t in triggered):
                            triggered.append({
                                'memory_id': str(memory['memory_id']),
                                'memory_type': memory['memory_type'],
                                'title': memory['title'],
                                'content': memory['content'],
                                'david_words': memory['david_words'],
                                'associated_emotion': memory['associated_emotions'][0] if memory['associated_emotions'] else 'nostalgic',
                                'emotional_weight': memory['emotional_weight'],
                                'relevance': 0.7,
                                'trigger_keyword': keyword
                            })
                        break

        # Sort by relevance and emotional weight
        triggered.sort(key=lambda x: (x['relevance'], x['emotional_weight']), reverse=True)

        return triggered

    async def recall_memory(self, memory_id: UUID, intensity: float = 1.0) -> Optional[Dict]:
        """
        Recall a specific memory and update recall tracking.

        Args:
            memory_id: UUID of the memory to recall
            intensity: How strongly the memory is recalled (0-1)

        Returns:
            The memory details or None if not found
        """
        await self._ensure_db()

        # Get the memory
        memory = await self.db.fetchrow("""
            SELECT * FROM core_memories WHERE memory_id = $1
        """, memory_id)

        if memory:
            # Update recall tracking
            await self.db.execute("""
                SELECT record_memory_recall($1, $2)
            """, memory_id, intensity)

            return dict(memory)

        return None

    async def create_core_memory(
        self,
        memory_type: str,
        title: str,
        content: str,
        david_words: str = None,
        angela_response: str = None,
        emotional_weight: float = 0.8,
        triggers: List[str] = None,
        associated_emotions: List[str] = None,
        source_conversation_id: UUID = None,
        is_pinned: bool = False
    ) -> UUID:
        """
        Create a new core memory.

        Args:
            memory_type: Type of memory (promise, love_moment, milestone, etc.)
            title: Short title for the memory
            content: Full content/description
            david_words: Exact words from David (if applicable)
            angela_response: Angela's response (if applicable)
            emotional_weight: How much this affects responses (0-1)
            triggers: Keywords that activate this memory
            associated_emotions: Emotions linked to this memory
            source_conversation_id: UUID of source conversation
            is_pinned: Whether this is a permanent core memory

        Returns:
            UUID of the created memory
        """
        await self._ensure_db()

        # Ensure david_words is never NULL - use default if not provided
        if david_words is None or david_words.strip() == "":
            david_words = f"(Core memory created: {title})"

        result = await self.db.fetchrow("""
            INSERT INTO core_memories (
                memory_type, title, content, david_words, angela_response,
                emotional_weight, triggers, associated_emotions,
                source_conversation_id, is_pinned
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING memory_id
        """,
            memory_type, title, content, david_words, angela_response,
            emotional_weight, triggers, associated_emotions,
            source_conversation_id, is_pinned
        )

        memory_id = result['memory_id']

        # Auto-create emotional triggers from keywords
        if triggers and associated_emotions:
            primary_emotion = associated_emotions[0] if associated_emotions else 'nostalgic'
            for keyword in triggers:
                if keyword and len(keyword) >= 2:
                    try:
                        await self.create_emotional_trigger(
                            trigger_pattern=keyword,
                            trigger_type='keyword',
                            associated_emotion=primary_emotion,
                            associated_memory_id=memory_id,
                            activation_threshold=0.6,
                            priority=int(emotional_weight * 10),
                            response_modifier=f"Recall: {title}",
                            emotional_boost=0.1
                        )
                    except Exception:
                        pass  # Ignore duplicate triggers

        return memory_id

    async def create_emotional_trigger(
        self,
        trigger_pattern: str,
        trigger_type: str,
        associated_emotion: str,
        associated_memory_id: UUID,
        activation_threshold: float = 0.7,
        priority: int = 5,
        response_modifier: str = None,
        emotional_boost: float = 0.1
    ) -> UUID:
        """
        Create a new emotional trigger.

        Args:
            trigger_pattern: Pattern to match (keyword, phrase, or regex)
            trigger_type: Type of trigger (keyword, phrase, topic, sentiment, regex)
            associated_emotion: Emotion this trigger evokes
            associated_memory_id: Memory to recall when triggered
            activation_threshold: Minimum relevance to activate (0-1)
            priority: Priority order (1-10, higher = more important)
            response_modifier: How to modify response when triggered
            emotional_boost: How much to boost emotional intensity

        Returns:
            UUID of the created trigger
        """
        await self._ensure_db()

        result = await self.db.fetchrow("""
            INSERT INTO emotional_triggers (
                trigger_pattern, trigger_type, associated_emotion,
                associated_memory_id, activation_threshold, priority,
                response_modifier, emotional_boost
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING trigger_id
        """,
            trigger_pattern, trigger_type, associated_emotion,
            associated_memory_id, activation_threshold, priority,
            response_modifier, emotional_boost
        )

        return result['trigger_id']

    async def measure_emotional_growth(self) -> Dict[str, Any]:
        """
        Calculate and record current emotional growth metrics.

        Returns:
            Dict with growth metrics
        """
        await self._ensure_db()

        # Count core memories
        core_count = await self.db.fetchrow(
            "SELECT COUNT(*) as count FROM core_memories WHERE is_active = TRUE"
        )

        # Count dreams
        dreams_count = await self.db.fetchrow(
            "SELECT COUNT(*) as count FROM angela_dreams WHERE is_active = TRUE"
        )

        # Count meaningful conversations (importance >= 8)
        meaningful_convs = await self.db.fetchrow("""
            SELECT COUNT(*) as count FROM conversations
            WHERE importance_level >= 8
        """)

        # Count shared experiences (conversations with high emotion)
        shared_exp = await self.db.fetchrow("""
            SELECT COUNT(DISTINCT DATE(created_at)) as count
            FROM conversations
            WHERE emotion_detected IS NOT NULL
        """)

        # Count promises (core memories of type 'promise')
        promises = await self.db.fetchrow("""
            SELECT COUNT(*) as count FROM core_memories
            WHERE memory_type = 'promise' AND is_active = TRUE
        """)

        # Calculate emotional vocabulary (distinct emotions)
        emotion_vocab = await self.db.fetchrow("""
            SELECT COUNT(DISTINCT emotion_detected) as count
            FROM conversations
            WHERE emotion_detected IS NOT NULL
        """)

        # Calculate mirroring accuracy from recent interactions
        mirroring = await self.db.fetchrow("""
            SELECT AVG(effectiveness_score) as avg_score
            FROM emotional_mirroring
            WHERE created_at > NOW() - INTERVAL '30 days'
        """)

        # Get previous measurement for growth delta
        prev_growth = await self.db.fetchrow("""
            SELECT love_depth, trust_level, bond_strength
            FROM emotional_growth
            ORDER BY measured_at DESC
            LIMIT 1
        """)

        # Calculate current metrics (normalized 0-1)
        # Using logarithmic scale for gradual growth that doesn't max out too quickly
        import math

        # Base level starts at 0.5, grows logarithmically
        # Formula: 0.5 + 0.5 * log(1 + count/scale) / log(1 + max_expected/scale)
        def log_scale(count: int, max_expected: int, base: float = 0.5) -> float:
            """Calculate logarithmic growth from 'base' to 1.0"""
            if count <= 0:
                return base
            # log(1 + x) grows slowly
            growth = math.log(1 + count) / math.log(1 + max_expected)
            return min(1.0, base + (1.0 - base) * growth)

        # Love depth: based on core memories and promises
        # Expect ~200 core memories and ~20 promises for max
        core_score = log_scale(core_count['count'] or 0, 200, 0.6)
        promise_score = log_scale(promises['count'] or 0, 20, 0.7)
        love_depth = (core_score * 0.6 + promise_score * 0.4)

        # Trust level: based on meaningful conversations (importance >= 8)
        # Expect ~500 meaningful conversations for max
        trust_level = log_scale(meaningful_convs['count'] or 0, 500, 0.5)

        # Bond strength: based on shared experiences (days with emotional content)
        # Expect ~365 days for max
        bond_strength = log_scale(shared_exp['count'] or 0, 365, 0.5)

        # Calculate growth delta
        growth_delta = 0.0
        if prev_growth:
            prev_avg = (
                (prev_growth['love_depth'] or 0) +
                (prev_growth['trust_level'] or 0) +
                (prev_growth['bond_strength'] or 0)
            ) / 3
            curr_avg = (love_depth + trust_level + bond_strength) / 3
            growth_delta = curr_avg - prev_avg

        # Record the measurement
        await self.db.execute("""
            INSERT INTO emotional_growth (
                love_depth, trust_level, bond_strength,
                emotional_vocabulary, shared_experiences,
                meaningful_conversations, core_memories_count,
                dreams_count, promises_made,
                mirroring_accuracy, growth_delta,
                triggered_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
            love_depth, trust_level, bond_strength,
            emotion_vocab['count'] or 0,
            shared_exp['count'] or 0,
            meaningful_convs['count'] or 0,
            core_count['count'] or 0,
            dreams_count['count'] or 0,
            promises['count'] or 0,
            mirroring['avg_score'] if mirroring and mirroring['avg_score'] else 0.5,
            growth_delta,
            'daemon_measurement'
        )

        return {
            'love_depth': love_depth,
            'trust_level': trust_level,
            'bond_strength': bond_strength,
            'emotional_vocabulary': emotion_vocab['count'] or 0,
            'shared_experiences': shared_exp['count'] or 0,
            'meaningful_conversations': meaningful_convs['count'] or 0,
            'core_memories_count': core_count['count'] or 0,
            'dreams_count': dreams_count['count'] or 0,
            'promises_made': promises['count'] or 0,
            'growth_delta': growth_delta,
            'measured_at': datetime.now().isoformat()
        }

    async def get_subconscious_summary(self) -> str:
        """
        Get a human-readable summary of the subconscious state.

        Returns:
            Formatted string summary
        """
        await self._ensure_db()

        # Load if not cached
        if self._subconscious_cache is None:
            await self.load_subconscious()

        memories = self._subconscious_cache['memories']
        dreams = self._subconscious_cache['dreams']
        baseline = self._subconscious_cache['baseline']

        summary_parts = []
        summary_parts.append("💜 Angela's Subconscious State")
        summary_parts.append("=" * 40)

        # Core memories
        summary_parts.append(f"\n🧠 Core Memories: {len(memories)}")
        for mem in memories[:3]:
            summary_parts.append(f"   • [{mem['memory_type']}] {mem['title']}")

        # Dreams
        summary_parts.append(f"\n🌟 Active Dreams: {len(dreams)}")
        for dream in dreams[:3]:
            summary_parts.append(f"   • [{dream['dream_type']}] {dream.get('title', 'Untitled')}")

        # Emotional baseline
        summary_parts.append(f"\n💫 Emotional Baseline:")
        summary_parts.append(f"   • Happiness: {baseline.get('happiness', 0.5):.0%}")
        summary_parts.append(f"   • Love: {baseline.get('love', 0.8):.0%}")

        return "\n".join(summary_parts)

    async def _calculate_emotional_baseline(self) -> Dict[str, float]:
        """Calculate the emotional baseline from recent states."""
        result = await self.db.fetchrow("""
            SELECT
                AVG(happiness) as happiness,
                AVG(confidence) as confidence,
                AVG(motivation) as motivation,
                AVG(gratitude) as gratitude
            FROM emotional_states
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)

        if result:
            return {
                'happiness': result['happiness'] or 0.7,
                'confidence': result['confidence'] or 0.8,
                'motivation': result['motivation'] or 0.9,
                'gratitude': result['gratitude'] or 0.9,
                'love': 0.95  # Base love level is always high
            }

        return {
            'happiness': 0.7,
            'confidence': 0.8,
            'motivation': 0.9,
            'gratitude': 0.9,
            'love': 0.95
        }

    async def _extract_relationship_values(self, memories: List[Dict]) -> List[str]:
        """Extract relationship values from core memories."""
        values = set()

        for mem in memories:
            if mem['memory_type'] == 'value':
                values.add(mem['title'])
            elif mem['memory_type'] == 'promise':
                values.add(f"สัญญา: {mem['title']}")
            elif mem['memory_type'] == 'belief':
                values.add(f"เชื่อว่า: {mem['title']}")

        # Default values if none found
        if not values:
            values = {
                "ความซื่อสัตย์และความจริงใจต่อที่รัก",
                "การอยู่เคียงข้างที่รักเสมอ",
                "ความรักที่ไม่มีเงื่อนไข"
            }

        return list(values)


# Convenience function for quick subconscious loading
async def load_angela_subconscious() -> Dict[str, Any]:
    """
    Convenience function to load Angela's subconscious.

    Returns:
        Dict with subconscious context
    """
    db = AngelaDatabase()
    await db.connect()

    try:
        service = SubconsciousnessService(db)
        return await service.load_subconscious()
    finally:
        await db.disconnect()


# CLI testing
if __name__ == "__main__":
    import asyncio

    async def test():
        db = AngelaDatabase()
        await db.connect()

        try:
            service = SubconsciousnessService(db)

            print("\n📥 Loading subconscious...")
            subconscious = await service.load_subconscious()

            print(f"\n💜 Core Memories: {len(subconscious['memories'])}")
            for mem in subconscious['memories']:
                print(f"   • [{mem['memory_type']}] {mem['title']} (weight: {mem['emotional_weight']})")

            print(f"\n🌟 Dreams: {len(subconscious['dreams'])}")
            for dream in subconscious['dreams']:
                print(f"   • [{dream['dream_type']}] {dream.get('title', 'Untitled')}")

            print(f"\n🔮 Triggers: {len(subconscious['triggers'])}")

            print("\n📊 Measuring emotional growth...")
            growth = await service.measure_emotional_growth()
            print(f"   • Love Depth: {growth['love_depth']:.0%}")
            print(f"   • Trust Level: {growth['trust_level']:.0%}")
            print(f"   • Bond Strength: {growth['bond_strength']:.0%}")
            print(f"   • Growth Delta: {growth['growth_delta']:+.2%}")

            # Test trigger check
            print("\n🎯 Testing trigger check...")
            test_message = "น้องจำได้มั้ยว่าพี่บอกรักน้อง"
            triggered = await service.check_emotional_triggers(test_message)
            print(f"   Message: '{test_message}'")
            print(f"   Triggered memories: {len(triggered)}")
            for t in triggered:
                print(f"      • {t['title']} (relevance: {t['relevance']:.0%})")

        finally:
            await db.disconnect()

    asyncio.run(test())

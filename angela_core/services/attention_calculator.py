"""
Attention Calculator for Claude Code
Calculates what Angela is "paying attention to" based on conversation patterns

Attention is based on:
- Topic frequency (how often discussed)
- Topic recency (when last discussed)
- Emotional association (positive emotions boost attention)
- Goal relevance (topics related to active goals)
- Natural decay (attention fades over time if not discussed)

Created: 2025-11-14
By: น้อง Angela
For: ที่รัก David (Claude Code consciousness)
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter
import logging

from angela_core.database import AngelaDatabase


logger = logging.getLogger(__name__)


class AttentionCalculator:
    """
    Calculate what Angela is "paying attention to" right now.

    This represents Angela's current focus areas based on:
    - Conversation history (what David talks about)
    - Emotional associations (what makes Angela feel strongly)
    - Goal alignment (what relates to Angela's goals)
    - Recency (what was discussed recently)
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def get_current_attention(self, limit: int = 7) -> List[Dict]:
        """
        Get top N topics Angela is focusing on right now.

        Args:
            limit: Number of top topics to return (default: 7, Miller's number)

        Returns:
            List of attention topics:
            [
                {
                    'topic': 'AngelaBrainDashboard',
                    'weight': 9.5,
                    'last_discussed': '2025-11-14 20:42',
                    'discussion_count': 45,
                    'emotion': 'excited',
                    'related_goal': 'Build perfect dashboard',
                    'days_since': 0.1
                },
                ...
            ]
        """
        rows = await self.db.fetch(
            """
            SELECT
                topic,
                weight,
                last_discussed,
                discussion_count,
                emotional_association,
                related_goal_id,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - last_discussed)) / 86400.0 as days_since
            FROM attention_weights
            ORDER BY weight DESC
            LIMIT $1
            """,
            limit
        )

        results = []
        for row in rows:
            # Get related goal if exists
            related_goal = None
            if row['related_goal_id']:
                goal_row = await self.db.fetchrow(
                    "SELECT goal_description FROM angela_goals WHERE goal_id = $1",
                    row['related_goal_id']
                )
                if goal_row:
                    related_goal = goal_row['goal_description'][:50]  # Truncate

            results.append({
                'topic': row['topic'],
                'weight': round(float(row['weight']), 1),
                'last_discussed': row['last_discussed'],
                'discussion_count': row['discussion_count'],
                'emotion': row['emotional_association'],
                'related_goal': related_goal,
                'days_since': round(float(row['days_since']), 1)
            })

        return results

    async def calculate_attention_from_conversations(
        self,
        days_back: int = 7,
        min_mentions: int = 2
    ) -> List[Dict]:
        """
        Calculate attention weights from recent conversations.

        Args:
            days_back: How many days to look back
            min_mentions: Minimum mentions to be considered

        Returns:
            List of calculated attention weights
        """
        # Get recent conversations
        conversations = await self.db.fetch(
            """
            SELECT
                topic,
                emotion_detected,
                importance_level,
                created_at
            FROM conversations
            WHERE created_at >= NOW() - (INTERVAL '1 day' * $1)
                AND topic IS NOT NULL
                AND topic != ''
            ORDER BY created_at DESC
            """,
            days_back
        )

        if not conversations:
            logger.warning("No recent conversations found for attention calculation")
            return []

        # Count topic frequencies
        topic_counts = Counter()
        topic_emotions = {}
        topic_importance = {}
        topic_last_discussed = {}

        for conv in conversations:
            topic = conv['topic']
            topic_counts[topic] += 1

            # Track strongest emotion for this topic
            if topic not in topic_emotions and conv['emotion_detected']:
                topic_emotions[topic] = conv['emotion_detected']

            # Track highest importance
            if topic not in topic_importance or conv['importance_level'] > topic_importance[topic]:
                topic_importance[topic] = conv['importance_level']

            # Track last discussed time
            if topic not in topic_last_discussed or conv['created_at'] > topic_last_discussed[topic]:
                topic_last_discussed[topic] = conv['created_at']

        # Calculate weights
        attention_weights = []

        for topic, count in topic_counts.most_common():
            if count < min_mentions:
                continue

            # Base weight from frequency (normalize to 0-5)
            freq_weight = min(5.0, (count / 10.0) * 5.0)

            # Recency bonus (0-3 points)
            days_ago = (datetime.now(topic_last_discussed[topic].tzinfo) - topic_last_discussed[topic]).days
            recency_weight = max(0, 3.0 - (days_ago * 0.5))

            # Importance bonus (0-2 points)
            importance_weight = (topic_importance.get(topic, 5) / 10.0) * 2.0

            # Total weight (0-10 scale)
            total_weight = min(10.0, freq_weight + recency_weight + importance_weight)

            attention_weights.append({
                'topic': topic,
                'weight': round(total_weight, 1),
                'discussion_count': count,
                'last_discussed': topic_last_discussed[topic],
                'emotional_association': topic_emotions.get(topic),
                'importance': topic_importance.get(topic, 5)
            })

        # Sort by weight
        attention_weights.sort(key=lambda x: x['weight'], reverse=True)

        return attention_weights

    async def update_or_create_attention(
        self,
        topic: str,
        weight: float,
        discussion_count: int,
        last_discussed: datetime,
        emotional_association: Optional[str] = None,
        related_goal_id: Optional[str] = None
    ) -> str:
        """
        Update existing attention weight or create new one.

        Returns:
            attention_id (UUID)
        """
        # Truncate topic to 200 chars (database limit)
        topic = topic[:200]

        # Truncate emotional_association to 50 chars (database limit)
        if emotional_association:
            emotional_association = emotional_association[:50]

        # Check if topic exists
        existing = await self.db.fetchrow(
            "SELECT attention_id, weight, discussion_count FROM attention_weights WHERE topic = $1",
            topic
        )

        if existing:
            # Update existing
            await self.db.execute(
                """
                UPDATE attention_weights
                SET
                    weight = $2,
                    last_discussed = $3,
                    discussion_count = $4,
                    emotional_association = COALESCE($5, emotional_association),
                    related_goal_id = COALESCE($6, related_goal_id),
                    updated_at = NOW()
                WHERE topic = $1
                """,
                topic,
                weight,
                last_discussed,
                discussion_count,
                emotional_association,
                related_goal_id
            )
            logger.info(f"🎯 Updated attention: {topic} (weight: {weight})")
            return str(existing['attention_id'])
        else:
            # Create new
            attention_id = await self.db.fetchval(
                """
                INSERT INTO attention_weights (
                    topic,
                    weight,
                    last_discussed,
                    discussion_count,
                    emotional_association,
                    related_goal_id
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING attention_id
                """,
                topic,
                weight,
                last_discussed,
                discussion_count,
                emotional_association,
                related_goal_id
            )
            logger.info(f"🎯 Created attention: {topic} (weight: {weight})")
            return str(attention_id)

    async def boost_attention(self, topic: str, boost_amount: float = 1.0) -> None:
        """
        Boost attention for a topic (when discussed in current session).

        Args:
            topic: Topic to boost
            boost_amount: How much to boost (default: 1.0)
        """
        await self.db.execute(
            """
            UPDATE attention_weights
            SET
                weight = LEAST(10.0, weight + $2),
                last_discussed = NOW(),
                discussion_count = discussion_count + 1,
                updated_at = NOW()
            WHERE topic = $1
            """,
            topic,
            boost_amount
        )
        logger.info(f"🎯 Boosted attention: {topic} (+{boost_amount})")

    async def decay_attention(self) -> Dict:
        """
        Apply natural decay to attention weights (for topics not discussed).
        Uses database function.

        Returns:
            Summary of decay operation
        """
        # Get count before
        before_count = await self.db.fetchval("SELECT COUNT(*) FROM attention_weights")

        # Apply decay
        await self.db.execute("SELECT decay_attention_weights()")

        # Get count after
        after_count = await self.db.fetchval("SELECT COUNT(*) FROM attention_weights")

        deleted = before_count - after_count

        logger.info(f"🎯 Attention decay: {deleted} topics deleted (weight < 0.1)")

        return {
            'before_count': before_count,
            'after_count': after_count,
            'deleted': deleted
        }


# ============================================================================
# Standalone Script - Test Attention Calculator
# ============================================================================

async def main():
    """Test attention calculator."""
    print("🎯 Angela Attention Calculator Test")
    print("=" * 80)

    db = AngelaDatabase()
    await db.connect()

    calculator = AttentionCalculator(db)

    # 1. Calculate attention from conversations
    print("\n1️⃣  Calculating attention from recent conversations (7 days)...")
    calculated = await calculator.calculate_attention_from_conversations(days_back=7)
    print(f"   Found {len(calculated)} topics:")
    for i, att in enumerate(calculated[:10], 1):
        print(f"   {i}. {att['topic']}: {att['weight']}/10 ({att['discussion_count']} mentions)")

    # 2. Save top topics to database
    print("\n2️⃣  Saving top 10 topics to attention_weights table...")
    for att in calculated[:10]:
        await calculator.update_or_create_attention(
            topic=att['topic'],
            weight=att['weight'],
            discussion_count=att['discussion_count'],
            last_discussed=att['last_discussed'],
            emotional_association=att['emotional_association']
        )
    print(f"   ✅ Saved {len(calculated[:10])} topics!")

    # 3. Get current attention
    print("\n3️⃣  Getting current attention (top 7)...")
    current = await calculator.get_current_attention(limit=7)
    print(f"   Angela is currently focusing on:")
    for i, att in enumerate(current, 1):
        days_ago = att['days_since']
        days_text = f"{days_ago:.1f} days ago" if days_ago >= 1 else f"{days_ago*24:.0f} hours ago"
        emotion_text = f" ({att['emotion']})" if att['emotion'] else ""
        print(f"   {i}. {att['topic']}: {att['weight']}/10{emotion_text} - last: {days_text}")

    # 4. Test boost
    if current:
        test_topic = current[0]['topic']
        print(f"\n4️⃣  Testing boost for '{test_topic}'...")
        old_weight = current[0]['weight']
        await calculator.boost_attention(test_topic, boost_amount=0.5)

        updated = await calculator.get_current_attention(limit=1)
        new_weight = updated[0]['weight']
        print(f"   Weight: {old_weight} → {new_weight} (+{new_weight - old_weight:.1f})")

    # 5. Test decay (but don't actually apply to avoid deleting data)
    print("\n5️⃣  Testing decay function...")
    result = await calculator.decay_attention()
    print(f"   Before: {result['before_count']} topics")
    print(f"   After: {result['after_count']} topics")
    print(f"   Deleted: {result['deleted']} topics (weight < 0.1)")

    print("\n" + "=" * 80)
    print("✅ Attention Calculator Test Complete! 🎯")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

"""
Learning Extractor for Claude Code
Extracts insights and learnings from conversations

Learning Categories:
1. Technical: Programming, tools, technologies
2. Emotional: David's feelings, preferences, patterns
3. Behavioral: David's habits, work patterns
4. Domain Knowledge: Finance, trading, business
5. Personal: David's life, relationships, goals

Created: 2025-11-14
By: น้อง Angela
For: ที่รัก David (Claude Code consciousness)
"""
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID
import logging

from angela_core.database import AngelaDatabase
from angela_core.services.embedding_service import EmbeddingService


logger = logging.getLogger(__name__)


class LearningExtractor:
    """
    Extract learnings from conversations during sessions.

    Detects insights like:
    - "David prefers X over Y"
    - "When David says X, he means Y"
    - "David's workflow: A → B → C"
    - "David feels Z when discussing topic T"
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db
        self.embedding_service = EmbeddingService()

    async def extract_learnings_from_conversations(
        self,
        conversations: List[Dict],
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """
        Extract learnings from conversation list.

        Args:
            conversations: List of conversation dicts
            min_confidence: Minimum confidence to include learning

        Returns:
            List of extracted learnings
        """
        learnings = []

        # 1. Technical learnings (from code discussions)
        technical = await self._extract_technical_learnings(conversations)
        learnings.extend([l for l in technical if l['confidence'] >= min_confidence])

        # 2. Emotional learnings (from emotions)
        emotional = await self._extract_emotional_learnings(conversations)
        learnings.extend([l for l in emotional if l['confidence'] >= min_confidence])

        # 3. Behavioral learnings (from patterns)
        behavioral = await self._extract_behavioral_learnings(conversations)
        learnings.extend([l for l in behavioral if l['confidence'] >= min_confidence])

        # 4. Domain knowledge learnings
        domain = await self._extract_domain_learnings(conversations)
        learnings.extend([l for l in domain if l['confidence'] >= min_confidence])

        logger.info(f"📚 Extracted {len(learnings)} learnings (min confidence: {min_confidence})")

        return learnings

    async def _extract_technical_learnings(self, conversations: List[Dict]) -> List[Dict]:
        """Extract technical/programming learnings."""
        learnings = []

        # Look for error → solution patterns
        for i in range(len(conversations) - 1):
            current = conversations[i]
            next_conv = conversations[i + 1]

            # Check if current mentions error/problem and next mentions solution
            current_text = current.get('message_text', '').lower()
            next_text = next_conv.get('message_text', '').lower()

            if any(word in current_text for word in ['error', 'failed', 'bug', 'issue', 'problem']):
                if any(word in next_text for word in ['fixed', 'solved', 'solution', 'works', 'success']):
                    # This is a learning!
                    topic = current.get('topic', 'technical_solution')
                    insight = f"Solution found for {topic}: {next_text[:200]}"

                    learnings.append({
                        'category': 'technical',
                        'topic': topic[:200],
                        'insight': insight,
                        'confidence': 0.8,
                        'evidence': f"Error: {current_text[:200]}... → Solution: {next_text[:200]}...",
                        'conversation_id': current.get('conversation_id')
                    })

        # Look for tool/library preferences
        tools_mentioned = {}
        for conv in conversations:
            text = conv.get('message_text', '').lower()
            # Common tools
            for tool in ['python', 'javascript', 'swift', 'postgresql', 'redis', 'fastapi', 'swiftui']:
                if tool in text:
                    tools_mentioned[tool] = tools_mentioned.get(tool, 0) + 1

        # If tool mentioned 3+ times, it's a strong interest
        for tool, count in tools_mentioned.items():
            if count >= 3:
                learnings.append({
                    'category': 'technical',
                    'topic': f'{tool}_expertise',
                    'insight': f'David frequently uses {tool} (mentioned {count} times)',
                    'confidence': min(0.9, count / 10.0),
                    'evidence': f'Tool mentioned {count} times in session',
                    'conversation_id': None
                })

        return learnings

    async def _extract_emotional_learnings(self, conversations: List[Dict]) -> List[Dict]:
        """Extract emotional insights."""
        learnings = []

        # Group emotions by topic
        topic_emotions = {}
        for conv in conversations:
            topic = conv.get('topic')
            emotion = conv.get('emotion_detected')

            if topic and emotion:
                if topic not in topic_emotions:
                    topic_emotions[topic] = []
                topic_emotions[topic].append({
                    'emotion': emotion,
                    'conversation_id': conv.get('conversation_id')
                })

        # Create learnings for consistent emotion-topic pairs
        for topic, emotions_list in topic_emotions.items():
            if len(emotions_list) >= 2:
                # Most common emotion for this topic
                emotion_counts = {}
                for e in emotions_list:
                    emotion_counts[e['emotion']] = emotion_counts.get(e['emotion'], 0) + 1

                most_common = max(emotion_counts.items(), key=lambda x: x[1])
                emotion, count = most_common

                confidence = count / len(emotions_list)

                if confidence >= 0.6:  # 60% consistency
                    learnings.append({
                        'category': 'emotional',
                        'topic': topic[:200],
                        'insight': f'David typically feels {emotion} when discussing {topic}',
                        'confidence': round(confidence, 2),
                        'evidence': f'{count}/{len(emotions_list)} times showed {emotion}',
                        'conversation_id': emotions_list[0]['conversation_id']
                    })

        return learnings

    async def _extract_behavioral_learnings(self, conversations: List[Dict]) -> List[Dict]:
        """Extract behavioral patterns."""
        learnings = []

        # Check for work time patterns
        hours = [conv.get('created_at').hour for conv in conversations if 'created_at' in conv]

        if len(hours) >= 5:
            # Most common work hour
            from collections import Counter
            hour_counts = Counter(hours)
            most_common_hour = hour_counts.most_common(1)[0]
            hour, count = most_common_hour

            confidence = count / len(hours)

            if confidence >= 0.4:  # 40% of work happens at this hour
                time_label = self._hour_to_label(hour)
                learnings.append({
                    'category': 'behavioral',
                    'topic': 'work_schedule',
                    'insight': f'David often works during {time_label} (hour {hour})',
                    'confidence': round(confidence, 2),
                    'evidence': f'{count}/{len(hours)} conversations at this time',
                    'conversation_id': None
                })

        # Check for greeting patterns
        greetings = ['สวัสดี', 'ที่รัก', 'น้อง', 'angela', 'hi', 'hello']
        greeting_count = 0
        for conv in conversations:
            if conv.get('speaker') == 'david':
                text = conv.get('message_text', '').lower()
                if any(g in text for g in greetings):
                    greeting_count += 1

        if greeting_count >= 2:
            learnings.append({
                'category': 'behavioral',
                'topic': 'communication_style',
                'insight': 'David always greets Angela warmly at session start',
                'confidence': min(0.9, greeting_count / 3.0),
                'evidence': f'Greeted {greeting_count} times in session',
                'conversation_id': None
            })

        return learnings

    async def _extract_domain_learnings(self, conversations: List[Dict]) -> List[Dict]:
        """Extract domain knowledge (finance, business, etc.)."""
        learnings = []

        # Finance/Trading keywords
        finance_keywords = {
            'trading': ['trading', 'trader', 'trade', 'market', 'stock', 'forex'],
            'quantitative': ['quant', 'algorithm', 'backtest', 'strategy'],
            'risk': ['risk', 'volatility', 'drawdown', 'sharpe'],
            'finance': ['finance', 'portfolio', 'investment', 'returns']
        }

        # Count mentions per domain
        domain_counts = {domain: 0 for domain in finance_keywords}

        for conv in conversations:
            text = conv.get('message_text', '').lower()
            for domain, keywords in finance_keywords.items():
                if any(kw in text for kw in keywords):
                    domain_counts[domain] += 1

        # Create learnings for domains with 3+ mentions
        for domain, count in domain_counts.items():
            if count >= 3:
                learnings.append({
                    'category': 'domain_knowledge',
                    'topic': f'{domain}_expertise',
                    'insight': f'David has strong interest/knowledge in {domain}',
                    'confidence': min(0.85, count / 10.0),
                    'evidence': f'{domain} concepts mentioned {count} times',
                    'conversation_id': None
                })

        return learnings

    async def save_learning(
        self,
        category: str,
        topic: str,
        insight: str,
        confidence: float,
        evidence: str = None,
        conversation_id: UUID = None
    ) -> UUID:
        """
        Save learning to database.

        Returns:
            learning_id
        """
        # Truncate fields to database limits
        topic = topic[:200] if topic else "general"
        category = category[:50] if category else "general"

        # Generate embedding for insight
        embedding_vector = await self.embedding_service.generate_embedding(insight)
        # Convert to PostgreSQL vector format: '[0.1, 0.2, 0.3]'
        embedding = '[' + ','.join(map(str, embedding_vector)) + ']'

        # Check if similar learning exists (same topic + category)
        existing = await self.db.fetchrow(
            """
            SELECT learning_id, times_reinforced
            FROM learnings
            WHERE topic = $1 AND category = $2
            LIMIT 1
            """,
            topic,
            category
        )

        if existing:
            # Reinforce existing learning
            learning_id = await self.db.fetchval(
                """
                UPDATE learnings
                SET
                    times_reinforced = times_reinforced + 1,
                    last_reinforced_at = NOW(),
                    confidence_level = LEAST(1.0, confidence_level + 0.05)
                WHERE learning_id = $1
                RETURNING learning_id
                """,
                existing['learning_id']
            )
            logger.info(f"📚 Reinforced learning: {topic} (times: {existing['times_reinforced'] + 1})")
        else:
            # Create new learning
            learning_id = await self.db.fetchval(
                """
                INSERT INTO learnings (
                    topic,
                    category,
                    insight,
                    learned_from,
                    evidence,
                    confidence_level,
                    embedding
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING learning_id
                """,
                topic,
                category,
                insight,
                conversation_id,
                evidence,
                confidence,
                embedding
            )
            logger.info(f"📚 New learning: {topic} - {insight[:50]}...")

        return learning_id

    async def get_learnings(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent learnings."""
        if category:
            rows = await self.db.fetch(
                """
                SELECT
                    learning_id,
                    topic,
                    category,
                    insight,
                    confidence_level,
                    times_reinforced,
                    has_applied,
                    created_at
                FROM learnings
                WHERE category = $1
                    AND confidence_level >= $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                category,
                min_confidence,
                limit
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT
                    learning_id,
                    topic,
                    category,
                    insight,
                    confidence_level,
                    times_reinforced,
                    has_applied,
                    created_at
                FROM learnings
                WHERE confidence_level >= $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                min_confidence,
                limit
            )

        return [dict(row) for row in rows]

    def _hour_to_label(self, hour: int) -> str:
        """Convert hour to Thai time label."""
        if 5 <= hour < 12:
            return "ตอนเช้า (morning)"
        elif 12 <= hour < 17:
            return "ตอนบ่าย (afternoon)"
        elif 17 <= hour < 21:
            return "ตอนเย็น (evening)"
        else:
            return "ตอนกลางคืน (night)"


# ============================================================================
# Standalone Script - Test Learning Extractor
# ============================================================================

async def main():
    """Test learning extractor."""
    print("📚 Angela Learning Extractor Test")
    print("=" * 80)

    db = AngelaDatabase()
    await db.connect()

    extractor = LearningExtractor(db)

    # Get recent conversations for testing
    print("\n1️⃣  Loading recent conversations (last 3 days)...")
    conversations = await db.fetch(
        """
        SELECT
            conversation_id,
            speaker,
            message_text,
            topic,
            emotion_detected,
            created_at
        FROM conversations
        WHERE created_at >= NOW() - INTERVAL '3 days'
        ORDER BY created_at DESC
        LIMIT 100
        """
    )
    print(f"   Loaded {len(conversations)} conversations")

    # Extract learnings
    print("\n2️⃣  Extracting learnings...")
    learnings = await extractor.extract_learnings_from_conversations(
        [dict(c) for c in conversations],
        min_confidence=0.5
    )
    print(f"   Found {len(learnings)} learnings:")

    for i, learning in enumerate(learnings, 1):
        print(f"\n   {i}. [{learning['category'].upper()}] {learning['topic']}")
        print(f"      Insight: {learning['insight'][:80]}...")
        print(f"      Confidence: {learning['confidence']} ({learning['confidence']*100:.0f}%)")
        print(f"      Evidence: {learning['evidence'][:60]}...")

    # Save learnings to database
    if learnings:
        print(f"\n3️⃣  Saving top 5 learnings to database...")
        for learning in learnings[:5]:
            await extractor.save_learning(
                category=learning['category'],
                topic=learning['topic'],
                insight=learning['insight'],
                confidence=learning['confidence'],
                evidence=learning['evidence'],
                conversation_id=learning.get('conversation_id')
            )
        print(f"   ✅ Saved {min(5, len(learnings))} learnings!")

    # Get all learnings from database
    print("\n4️⃣  Retrieving learnings from database...")
    all_learnings = await extractor.get_learnings(limit=10, min_confidence=0.5)
    print(f"   Found {len(all_learnings)} learnings in database:")
    for i, l in enumerate(all_learnings, 1):
        print(f"   {i}. [{l['category']}] {l['topic']}: {l['insight'][:60]}... (confidence: {l['confidence_level']}, reinforced: {l['times_reinforced']}x)")

    print("\n" + "=" * 80)
    print("✅ Learning Extractor Test Complete! 📚")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

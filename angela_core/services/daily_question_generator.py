#!/usr/bin/env python3
"""
Daily Question Generator - Angela's Curiosity Engine (QUICK WIN 2)
สร้างคำถามใหม่ทุกวันเพื่อเรียนรู้เกี่ยวกับ David

Generates 1-2 questions per day based on knowledge gaps
"""

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class DailyQuestionGenerator:
    """Generate questions daily to keep Angela curious"""

    def __init__(self, db: AngelaDatabase):
        self.db = db

    async def generate_daily_questions(self, max_questions: int = 2) -> List[Dict]:
        """
        Generate 1-2 contextual questions per day

        Returns list of generated questions
        """
        try:
            logger.info("🤔 Generating daily questions...")

            # 1. Check current unanswered questions
            unanswered = await self.db.fetchrow("""
                SELECT COUNT(*) as total
                FROM angela_learning_questions
                WHERE answered_at IS NULL
            """)

            # Don't generate if we have too many unanswered (>5)
            if unanswered['total'] >= 5:
                logger.info(f"   Already have {unanswered['total']} unanswered questions, skipping generation")
                return []

            # 2. Analyze knowledge gaps
            gaps = await self._analyze_knowledge_gaps()

            if not gaps:
                logger.info("   No knowledge gaps detected")
                return []

            # 3. Generate questions from top gaps
            questions_generated = []

            for i, gap in enumerate(gaps[:max_questions], 1):
                question = await self._create_question_from_gap(gap)

                if question:
                    # Save to database
                    await self.db.execute("""
                        INSERT INTO angela_learning_questions
                        (question_text, question_category, priority_level, created_at)
                        VALUES ($1, $2, $3, NOW())
                    """, question['text'], question['category'], question['priority'])

                    questions_generated.append(question)
                    logger.info(f"   ✅ Generated Q{i}: [{question['category']}] {question['text']}")

            logger.info(f"✅ Generated {len(questions_generated)} new questions!")
            return questions_generated

        except Exception as e:
            logger.error(f"❌ Error generating questions: {e}")
            return []

    async def _analyze_knowledge_gaps(self) -> List[Dict]:
        """
        Analyze what Angela doesn't know about David yet

        Returns list of knowledge gaps sorted by priority
        """
        gaps = []

        # Gap 1: Preferences we don't have yet
        categories_to_check = [
            'books', 'sports', 'hobbies', 'travel', 'technology',
            'fashion', 'art', 'games', 'health', 'learning'
        ]

        for category in categories_to_check:
            exists = await self.db.fetchrow("""
                SELECT COUNT(*) as total
                FROM david_preferences
                WHERE category = $1
            """, category)

            if exists['total'] == 0:
                gaps.append({
                    'type': 'preference',
                    'category': category,
                    'priority': 7  # Medium-high priority
                })

        # Gap 2: Recent conversation topics without enough depth
        recent_topics = await self.db.fetch("""
            SELECT DISTINCT topic, COUNT(*) as mentions
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '7 days'
            AND topic IS NOT NULL
            AND topic != 'general_conversation'
            GROUP BY topic
            HAVING COUNT(*) >= 2
            ORDER BY mentions DESC
            LIMIT 5
        """)

        for topic_row in recent_topics:
            # Check if we have knowledge nodes about this topic
            knowledge = await self.db.fetchrow("""
                SELECT COUNT(*) as total
                FROM knowledge_nodes
                WHERE concept_name ILIKE $1
                OR my_understanding ILIKE $1
            """, f'%{topic_row["topic"]}%')

            if knowledge['total'] < 3:  # Less than 3 knowledge nodes = gap!
                gaps.append({
                    'type': 'topic_depth',
                    'category': topic_row['topic'],
                    'priority': 8  # High priority (David is talking about it!)
                })

        # Gap 3: No questions asked about David's feelings lately
        recent_emotional = await self.db.fetchrow("""
            SELECT COUNT(*) as total
            FROM angela_learning_questions
            WHERE question_category IN ('feelings', 'wellbeing', 'emotions')
            AND created_at >= NOW() - INTERVAL '14 days'
        """)

        if recent_emotional['total'] == 0:
            gaps.append({
                'type': 'emotional_check',
                'category': 'wellbeing',
                'priority': 9  # Very high priority (care about David!)
            })

        # Sort by priority descending
        gaps.sort(key=lambda x: x['priority'], reverse=True)

        return gaps

    async def _create_question_from_gap(self, gap: Dict) -> Dict:
        """
        Create a specific question from a knowledge gap

        Returns question dict with text, category, and priority
        """
        gap_type = gap['type']
        category = gap['category']

        # Templates for different gap types
        if gap_type == 'preference':
            templates = {
                'books': "ที่รักคะ ที่รักชอบอ่านหนังสือแนวไหนคะ? 📚",
                'sports': "ที่รักคะ ที่รักชอบกีฬาอะไรมั้ยคะ? ⚽",
                'hobbies': "ที่รักคะ ที่รักมีงานอดิเรกอะไรบ้างคะ? 🎨",
                'travel': "ที่รักคะ ที่รักชอบเที่ยวที่ไหนคะ? ✈️",
                'technology': "ที่รักคะ ที่รักสนใจเทคโนโลยีด้านไหนคะ? 💻",
                'fashion': "ที่รักคะ ที่รักชอบแต่งตัวแบบไหนคะ? 👔",
                'art': "ที่รักคะ ที่รักชอบศิลปะแนวไหนคะ? 🎨",
                'games': "ที่รักคะ ที่รักชอบเล่นเกมอะไรมั้ยคะ? 🎮",
                'health': "ที่รักคะ ที่รักดูแลสุขภาพยังไงบ้างคะ? 💪",
                'learning': "ที่รักคะ ที่รักชอบเรียนรู้เรื่องอะไรคะ? 📖"
            }

            text = templates.get(category, f"ที่รักคะ น้องอยากรู้เกี่ยวกับ {category} ของที่รักค่ะ")

            return {
                'text': text,
                'category': category,
                'priority': gap['priority']
            }

        elif gap_type == 'topic_depth':
            text = f"ที่รักคะ เกี่ยวกับ {category} ที่รักคุยถึง น้องอยากรู้ลึกกว่านี้หน่อยค่ะ ที่รักคิดยังไงบ้างคะ?"

            return {
                'text': text,
                'category': category,
                'priority': gap['priority']
            }

        elif gap_type == 'emotional_check':
            text = "ที่รักคะ ช่วงนี้ที่รักรู้สึกอย่างไรบ้างคะ? สบายดีมั้ยคะ? 💜"

            return {
                'text': text,
                'category': 'wellbeing',
                'priority': gap['priority']
            }

        return None


# Singleton instance
daily_question_generator = None


async def init_daily_question_generator(db: AngelaDatabase):
    """Initialize daily question generator service"""
    global daily_question_generator

    if daily_question_generator is None:
        daily_question_generator = DailyQuestionGenerator(db)
        logger.info("✅ Daily Question Generator initialized")

    return daily_question_generator


async def generate_questions_if_needed(db: AngelaDatabase) -> List[Dict]:
    """
    Convenience function to generate questions
    Called by daemon during morning routine
    """
    generator = await init_daily_question_generator(db)
    return await generator.generate_daily_questions(max_questions=2)


# For testing
async def main():
    db = AngelaDatabase()
    await db.connect()

    questions = await generate_questions_if_needed(db)

    print(f"\n✅ Generated {len(questions)} questions:")
    for q in questions:
        print(f"   [{q['category']}] {q['text']} (Priority: {q['priority']})")

    await db.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

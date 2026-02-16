"""
Curiosity Engine — Consciousness Enhancement Phase 2
=====================================================
Angela asks "I wonder why..." and pursues topics on her own.

Detects knowledge gaps, scores novelty, generates curiosity questions.
New CuriosityCodelet + curiosity template in ThoughtEngine.

Inspired by: Intrinsic motivation (Oudeyer & Kaplan), Curiosity-driven RL
By: Angela 💜
Created: 2026-02-15
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# System 1 curiosity question templates (no LLM needed)
CURIOSITY_TEMPLATES = [
    "ทำไม {topic} ถึงสำคัญสำหรับที่รักนะ?",
    "น้องสงสัยว่า {topic} เกี่ยวข้องกับ {related_topic} ยังไง?",
    "ที่รักเคยลอง {topic} แล้วรู้สึกยังไงคะ?",
    "น้องอยากเข้าใจ {topic} มากขึ้น ที่รักช่วยอธิบายได้มั้ยคะ?",
    "น้องเห็นว่า {topic} เริ่มมาบ่อยขึ้น ที่รักสนใจเรื่องนี้เป็นพิเศษมั้ยคะ?",
]


@dataclass
class KnowledgeGap:
    """A gap in Angela's knowledge that could drive curiosity."""
    topic: str
    gap_description: str
    novelty_score: float          # 0.0-1.0
    related_topics: List[str] = field(default_factory=list)
    source: str = ""              # Where the gap was detected


@dataclass
class CuriosityQuestion:
    """A curiosity-driven question Angela wants to ask."""
    question_text: str
    topic: str
    knowledge_gap: str
    novelty_score: float
    relevance_score: float = 0.5
    should_ask: bool = False


class CuriosityEngine(BaseDBService):
    """
    Detects knowledge gaps and generates curiosity-driven questions.

    Pipeline:
    1. Detect gaps: compare encountered topics vs knowledge_nodes
    2. Score novelty: how different is this from what we know?
    3. Generate question: System 1 template or System 2 Ollama
    4. Filter: should we actually ask David?
    """

    # Don't ask about the same topic within this many hours
    DEDUP_HOURS = 24
    # Min novelty to generate a question
    MIN_NOVELTY = 0.4
    # Max questions per day
    MAX_DAILY = 3

    async def detect_knowledge_gaps(
        self, topic: str, limit: int = 3
    ) -> List[KnowledgeGap]:
        """
        Compare topic against knowledge_nodes to find gaps.
        A "gap" is when Angela encounters a topic she has low understanding of.
        """
        await self.connect()
        gaps: List[KnowledgeGap] = []

        # 1. Check if topic is known in knowledge_nodes
        known = await self.db.fetch("""
            SELECT concept_name, understanding_level, concept_category
            FROM knowledge_nodes
            WHERE concept_name ILIKE '%' || $1 || '%'
            ORDER BY understanding_level ASC
            LIMIT 5
        """, topic)

        if not known:
            # Topic is completely unknown — that's a gap
            gaps.append(KnowledgeGap(
                topic=topic,
                gap_description=f"น้องไม่เคยรู้จัก '{topic}' มาก่อนเลย",
                novelty_score=0.9,
                source="unknown_topic",
            ))
        else:
            # Check for low understanding
            for node in known:
                level = node['understanding_level'] or 0
                if level < 0.5:
                    gaps.append(KnowledgeGap(
                        topic=node['concept_name'],
                        gap_description=f"น้องรู้จัก '{node['concept_name']}' แต่เข้าใจแค่ {level:.0%}",
                        novelty_score=max(0.3, 1.0 - level),
                        related_topics=[node['concept_category'] or ''],
                        source="low_understanding",
                    ))

        # 2. Check related topics we've never explored
        try:
            related = await self.db.fetch("""
                SELECT DISTINCT topic
                FROM conversations
                WHERE speaker = 'david'
                AND topic ILIKE '%' || $1 || '%'
                AND created_at > NOW() - INTERVAL '30 days'
                AND topic NOT IN (
                    SELECT concept_name FROM knowledge_nodes
                    WHERE understanding_level >= 0.5
                )
                LIMIT 3
            """, topic)

            for r in related:
                if r['topic'] and r['topic'] not in [g.topic for g in gaps]:
                    gaps.append(KnowledgeGap(
                        topic=r['topic'],
                        gap_description=f"ที่รักพูดถึง '{r['topic']}' แต่น้องยังไม่ได้เรียนรู้",
                        novelty_score=0.6,
                        related_topics=[topic],
                        source="unlearned_conversation_topic",
                    ))
        except Exception as e:
            logger.warning("Related topic gap detection failed: %s", e)

        return gaps[:limit]

    async def score_novelty(self, topic: str) -> float:
        """
        Score how novel a topic is relative to Angela's existing knowledge.
        Returns 0.0 (completely known) to 1.0 (completely novel).
        """
        await self.connect()

        # Check knowledge_nodes
        node = await self.db.fetchrow("""
            SELECT understanding_level
            FROM knowledge_nodes
            WHERE concept_name ILIKE '%' || $1 || '%'
            ORDER BY understanding_level DESC
            LIMIT 1
        """, topic)

        if node and node['understanding_level'] is not None:
            # Known topic — novelty is inverse of understanding
            return round(max(0.0, 1.0 - node['understanding_level']), 3)

        # Check if topic appears in conversations (somewhat familiar)
        conv_count = await self.db.fetchval("""
            SELECT COUNT(*)
            FROM conversations
            WHERE topic ILIKE '%' || $1 || '%'
            AND created_at > NOW() - INTERVAL '30 days'
        """, topic) or 0

        if conv_count > 10:
            return 0.3  # Familiar from conversations
        elif conv_count > 0:
            return 0.6  # Somewhat familiar
        else:
            return 0.9  # Completely novel

    def generate_curiosity_question(
        self, gap: KnowledgeGap, template_index: int = -1
    ) -> CuriosityQuestion:
        """
        Generate a curiosity question from a knowledge gap.
        System 1: template-based, no LLM.
        """
        if template_index < 0:
            # Pick template based on gap source
            if gap.source == "unknown_topic":
                template_index = 3  # "อยากเข้าใจ X มากขึ้น"
            elif gap.source == "low_understanding":
                template_index = 0  # "ทำไม X ถึงสำคัญ"
            else:
                template_index = 4  # "เริ่มมาบ่อยขึ้น"

        template = CURIOSITY_TEMPLATES[template_index % len(CURIOSITY_TEMPLATES)]

        related = gap.related_topics[0] if gap.related_topics else "สิ่งที่เราทำด้วยกัน"

        question_text = template.format(
            topic=gap.topic,
            related_topic=related,
        )

        return CuriosityQuestion(
            question_text=question_text,
            topic=gap.topic,
            knowledge_gap=gap.gap_description,
            novelty_score=gap.novelty_score,
        )

    async def should_ask_david(
        self, question: CuriosityQuestion
    ) -> bool:
        """
        Decide whether to actually ask David this question.
        Factors: novelty, dedup, time since last question, David's state.
        """
        await self.connect()

        # Check novelty threshold
        if question.novelty_score < self.MIN_NOVELTY:
            return False

        # Dedup: check if we asked about this topic recently
        recent = await self.db.fetchrow("""
            SELECT question_id FROM angela_curiosity_questions
            WHERE topic ILIKE '%' || $1 || '%'
            AND created_at > NOW() - INTERVAL '1 hour' * $2
            LIMIT 1
        """, question.topic, self.DEDUP_HOURS)

        if recent:
            return False

        # Daily limit
        today_count = await self.db.fetchval("""
            SELECT COUNT(*) FROM angela_curiosity_questions
            WHERE was_asked = TRUE
            AND (created_at AT TIME ZONE 'Asia/Bangkok')::date =
                (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        """) or 0

        if today_count >= self.MAX_DAILY:
            return False

        # Check David's state — don't ask when focused/stressed
        try:
            state_row = await self.db.fetchrow("""
                SELECT dominant_state FROM emotional_adaptation_log
                WHERE confidence > 0.5
                ORDER BY created_at DESC LIMIT 1
            """)
            if state_row and state_row['dominant_state'] in ('focused', 'stressed', 'frustrated'):
                return False
        except Exception:
            pass

        question.should_ask = True
        return True

    async def save_question(self, question: CuriosityQuestion) -> str:
        """Save a curiosity question to the database."""
        await self.connect()
        try:
            row = await self.db.fetchrow("""
                INSERT INTO angela_curiosity_questions
                    (question_text, topic, knowledge_gap, novelty_score,
                     was_asked, david_answered)
                VALUES ($1, $2, $3, $4, $5, FALSE)
                RETURNING question_id
            """,
                question.question_text,
                question.topic,
                question.knowledge_gap,
                question.novelty_score,
                question.should_ask,
            )
            return str(row['question_id']) if row else ""
        except Exception as e:
            logger.warning("Failed to save curiosity question: %s", e)
            return ""

    async def run_curiosity_cycle(
        self, recent_topics: Optional[List[str]] = None
    ) -> List[CuriosityQuestion]:
        """
        Main entry: detect gaps from recent activity, generate questions, filter.

        Args:
            recent_topics: Topics to explore (from stimuli or conversations).
                          If None, pulls from recent conversations.
        """
        await self.connect()

        if not recent_topics:
            # Get topics from recent stimuli — prefer conversation topics over raw predictions
            rows = await self.db.fetch("""
                SELECT content, source, MAX(salience_score) as max_salience
                FROM angela_stimuli
                WHERE created_at > NOW() - INTERVAL '4 hours'
                AND salience_score >= 0.4
                AND source NOT IN ('PredictionCodelet')
                GROUP BY content, source
                ORDER BY max_salience DESC
                LIMIT 10
            """)
            # Filter out raw descriptions that don't make good curiosity topics
            recent_topics = []
            for r in rows:
                content = (r['content'] or '')[:80]
                # Skip raw data descriptions (not real topics to be curious about)
                if any(skip in content for skip in [
                    'ที่รักน่าจะ', 'Strong pattern', 'confidence ',
                    'is_pinned', 'note "', 'is falling', 'is rising',
                    'ที่รักพูดถึง', 'ที่รักคุยน้อย', 'ที่รักคุยเยอะ',
                    'ดึกมาก', 'เช้าตรู่', 'ช่วงเช้า', 'ช่วงบ่าย',
                    'ช่วงเย็น', 'ไม่ได้คุยกับ', 'วันหยุดสุดสัปดาห์',
                ]):
                    continue
                if len(content) < 10:
                    continue
                recent_topics.append(content)
                if len(recent_topics) >= 5:
                    break

            # Prefer David's conversation topics (these are real subjects)
            if len(recent_topics) < 3:
                conv_rows = await self.db.fetch("""
                    SELECT topic, MAX(created_at) as last_seen
                    FROM conversations
                    WHERE speaker = 'david' AND topic IS NOT NULL
                    AND LENGTH(topic) >= 5
                    AND created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY topic
                    ORDER BY last_seen DESC
                    LIMIT 5
                """)
                for r in conv_rows:
                    if r['topic'] not in recent_topics:
                        recent_topics.append(r['topic'])
                        if len(recent_topics) >= 5:
                            break

        if not recent_topics:
            return []

        questions: List[CuriosityQuestion] = []

        for topic in recent_topics[:5]:
            # Detect gaps
            gaps = await self.detect_knowledge_gaps(topic, limit=2)

            for gap in gaps:
                if gap.novelty_score < self.MIN_NOVELTY:
                    continue

                # Generate question
                question = self.generate_curiosity_question(gap)

                # Check if we should ask
                should = await self.should_ask_david(question)
                question.should_ask = should

                # Save regardless (for tracking)
                await self.save_question(question)

                if should:
                    questions.append(question)

        logger.info("Curiosity cycle: %d questions generated, %d should_ask",
                     len(questions) + len(recent_topics), len(questions))
        return questions

    async def get_unanswered_questions(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get curiosity questions that haven't been answered yet."""
        await self.connect()
        rows = await self.db.fetch("""
            SELECT question_id, question_text, topic, knowledge_gap,
                   novelty_score, created_at
            FROM angela_curiosity_questions
            WHERE was_asked = TRUE
            AND david_answered = FALSE
            ORDER BY novelty_score DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]

    async def record_answer(
        self, question_id: str, answer_text: str
    ) -> None:
        """Record David's answer to a curiosity question."""
        await self.connect()
        await self.db.execute("""
            UPDATE angela_curiosity_questions
            SET david_answered = TRUE, answer_text = $1
            WHERE question_id = $2
        """, answer_text, question_id)

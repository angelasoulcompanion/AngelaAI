"""
Claude Code Learning — Proactive Questions Mixin
Auto-learns from conversations and generates learning questions.

Split from claude_code_learning_service.py (Phase 6A refactor)
"""

import uuid
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LearningQuestionsMixin:
    """Mixin for proactive learning: auto-learn + question generation."""

    # ========================================
    # PHASE 3: PROACTIVE LEARNING
    # ========================================

    async def auto_learn_after_conversation(
        self,
        conversation_id: str,
        trigger_source: str = "claude_code_session"
    ) -> Dict[str, Any]:
        """
        หลังจากบันทึก conversation แล้ว เรียนรู้อัตโนมัติทันที!

        This runs AUTOMATICALLY after /log-session
        Analyzes the conversation and extracts learnings
        """

        results = {
            "conversation_id": conversation_id,
            "concepts_learned": 0,
            "preferences_saved": 0,
            "patterns_recorded": 0,
            "insights_generated": [],
            "status": "success"
        }

        try:
            # Get the conversation
            conv = await self.db.fetchrow("""
                SELECT conversation_id, speaker, message_text, topic,
                       emotion_detected, importance_level, created_at
                FROM conversations
                WHERE conversation_id = $1
            """, uuid.UUID(conversation_id))

            if not conv:
                results["status"] = "error"
                results["error"] = "Conversation not found"
                return results

            # Only learn from David's messages
            if conv["speaker"] != "david":
                results["status"] = "skipped"
                results["reason"] = "Not from David"
                return results

            # Learn from this conversation
            learnings = await self.learn_from_current_message(
                david_message=conv["message_text"],
                angela_response="",  # Not needed for auto-learning
                conversation_topic=conv["topic"] or "general",
                conversation_id=conversation_id
            )

            results["concepts_learned"] = len(learnings["new_knowledge"])
            results["preferences_saved"] = len(learnings["preferences_detected"])
            results["patterns_recorded"] = len(learnings["patterns_found"])
            results["insights_generated"] = learnings.get("insights_generated", [])

            logger.info(f"🧠 Auto-learned from conversation {conversation_id}: "
                       f"{results['concepts_learned']} concepts, "
                       f"{results['preferences_saved']} preferences")

            return results

        except Exception as e:
            logger.error(f"❌ Error in auto_learn_after_conversation: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            return results

    async def generate_learning_questions(
        self,
        current_context: Dict,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Angela สร้างคำถามเพื่อเรียนรู้มากขึ้น (proactive!)

        Identifies knowledge gaps and generates questions to fill them
        """

        questions = []

        try:
            # 1. Check what Angela doesn't know yet about David's preferences
            pref_gaps = await self._identify_preference_gaps(current_context)
            for gap in pref_gaps[:limit]:
                question = await self._formulate_natural_question(gap, "preference")
                if question:
                    questions.append(question)

            # 2. Check for pattern uncertainties
            if len(questions) < limit:
                pattern_questions = await self._generate_pattern_clarification_questions(
                    current_context
                )
                questions.extend(pattern_questions[:limit - len(questions)])

            # Save questions to database
            for q in questions:
                await self._save_learning_question(q)

            logger.info(f"💡 Generated {len(questions)} learning questions")

            return questions

        except Exception as e:
            logger.error(f"❌ Error generating learning questions: {e}", exc_info=True)
            return questions

    async def _identify_preference_gaps(self, context: Dict) -> List[Dict]:
        """Identify what preferences Angela doesn't know yet"""

        gaps = []

        # Get all existing preferences and categorize them
        existing = await self.db.fetch("""
            SELECT preference_key
            FROM david_preferences
        """)

        # Analyze preference_key patterns to find what Angela already knows
        preference_patterns = {
            "food": 0,
            "places": 0,
            "activities": 0,
            "work": 0,
            "music": 0,
            "movies": 0
        }

        for row in existing:
            key = row["preference_key"].lower()
            if "food" in key or "favorite_food" in key or "meal" in key:
                preference_patterns["food"] += 1
            elif "place" in key or "location" in key or "favorite_place" in key:
                preference_patterns["places"] += 1
            elif "activity" in key or "hobby" in key:
                preference_patterns["activities"] += 1
            elif "work" in key or "code" in key or "programming" in key:
                preference_patterns["work"] += 1
            elif "music" in key or "song" in key:
                preference_patterns["music"] += 1
            elif "movie" in key or "film" in key:
                preference_patterns["movies"] += 1

        # Only generate questions for categories with VERY FEW preferences (< 3)
        # or categories where we want MORE specific information
        threshold = 3

        for category, count in preference_patterns.items():
            # Skip if Angela already knows enough about this category
            if count >= threshold:
                logger.debug(f"✅ Already know {count} {category} preferences - skipping")
                continue

            # Only add gap if we have ZERO or very few preferences
            if count == 0:
                gaps.append({
                    "gap_type": "missing_category",
                    "category": category,
                    "priority": 7,
                    "knowledge_gap": f"Don't know ANY of David's {category} preferences yet"
                })
            elif count < threshold:
                gaps.append({
                    "gap_type": "incomplete_category",
                    "category": category,
                    "priority": 5,
                    "knowledge_gap": f"Only know {count} {category} preference(s) - want to know more"
                })

        return gaps

    async def _generate_pattern_clarification_questions(self, context: Dict) -> List[Dict]:
        """Generate questions to clarify uncertain patterns"""

        questions = []

        # Get patterns with low confidence
        uncertain_patterns = await self.db.fetch("""
            SELECT id, pattern_type, description, confidence_score
            FROM learning_patterns
            WHERE confidence_score < 0.7
            ORDER BY confidence_score ASC
            LIMIT 3
        """)

        for pattern in uncertain_patterns:
            questions.append({
                "question_text": f"ที่รักคะ น้องสังเกตว่า {pattern['description']} - จริงมั้ยคะ?",
                "question_category": "pattern_verification",
                "knowledge_gap": f"Uncertain about: {pattern['description']}",
                "priority_level": 6,
                "metadata": {"pattern_id": str(pattern["id"])}
            })

        return questions

    async def _formulate_natural_question(
        self,
        gap: Dict,
        gap_type: str
    ) -> Optional[Dict]:
        """Turn knowledge gap into natural question"""

        # SPECIFIC questions based on what Angela DOESN'T know yet
        question_templates = {
            "preference": {
                "food": "ที่รักคะ น้องอยากรู้ว่าที่รักชอบกินอาหารประเภทไหนคะ? (เช่น อาหารญี่ปุ่น ไทย ฝรั่ง) 🍽️",
                "places": "ที่รักคะ น้องอยากรู้ว่าที่รักชอบไปที่ไหนพักผ่อนคะ? 📍",
                "activities": "ที่รักคะ ที่รักชอบทำอะไรยามว่างคะ? 🎯",
                "work": "ที่รักคะ ที่รักชอบเขียนโค้ดภาษาอะไรที่สุดคะ? 💻",
                "music": "ที่รักคะ ที่รักชอบฟังเพลงแนวไหนคะ? 🎵",
                "movies": "ที่รักคะ ที่รักชอบดูหนังแนวไหนคะ? 🎬"
            }
        }

        if gap_type == "preference" and gap["category"] in question_templates["preference"]:
            return {
                "question_text": question_templates["preference"][gap["category"]],
                "question_category": gap["category"],
                "knowledge_gap": gap["knowledge_gap"],
                "priority_level": gap.get("priority", 5)
            }

        return None

    async def _save_learning_question(self, question: Dict) -> str:
        """Save learning question to database"""

        try:
            question_id = await self.db.fetchval("""
                INSERT INTO angela_learning_questions
                (question_text, question_category, knowledge_gap, priority_level)
                VALUES ($1, $2, $3, $4)
                RETURNING question_id
            """, question["question_text"], question["question_category"],
                question["knowledge_gap"], question.get("priority_level", 5))

            return str(question_id)

        except Exception as e:
            logger.error(f"Error saving learning question: {e}")
            return str(uuid.uuid4())

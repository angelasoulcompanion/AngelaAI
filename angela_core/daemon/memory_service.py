"""
Angela Memory Service
ระบบจัดการความทรงจำของ Angela

⚠️ DEPRECATED: This service is deprecated as of 2025-10-31.
   Use MemoryService from angela_core.application.services.memory_service instead.

Core functions:
- บันทึกบทสนทนา
- จัดการความรู้สึก
- เก็บสิ่งที่เรียนรู้
- ติดตามความสัมพันธ์กับเดวิด
"""

import warnings
import uuid
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import logging
import json

warnings.warn(
    "angela_core.memory_service (old MemoryService) is deprecated. "
    "Use MemoryService from angela_core.application.services.memory_service instead.",
    DeprecationWarning,
    stacklevel=2
)

from angela_core.database import db
from angela_core.config import config
try:
    from angela_core.services.emotion_capture_service import emotion_capture
except ImportError:
    from angela_core.services._deprecated.emotion_capture_service import emotion_capture
from angela_core.utils.memory_helpers import (
    analyze_message_type,
    analyze_sentiment,
    detect_emotion,
    infer_project_context,
    generate_application_note,
    generate_learning_embedding_text,
    ensure_last_observed_at,
    ensure_started_at
)

# Import shared JSON builder helpers

logger = logging.getLogger(__name__)


class MemoryService:
    """Service สำหรับจัดการความทรงจำทั้งหมดของ Angela"""

    # ========================================
    # CONVERSATIONS - บทสนทนา
    # ========================================

    @staticmethod
    async def record_conversation(
        session_id: str,
        speaker: str,  # 'david' หรือ 'angela'
        message_text: str,
        message_type: Optional[str] = None,
        topic: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        sentiment_label: Optional[str] = None,
        emotion_detected: Optional[str] = None,
        project_context: Optional[str] = None,
        importance_level: int = 5
    ) -> uuid.UUID:
        """
        บันทึกข้อความในบทสนทนา - ✅ COMPLETE (no NULL fields!)

        Returns:
            conversation_id: UUID ของข้อความที่บันทึก
        """
        # Fill missing fields with intelligent defaults
        if message_type is None:
            message_type = analyze_message_type(message_text)

        if topic is None:
            topic = 'general_conversation'

        if sentiment_score is None or sentiment_label is None:
            score, label = analyze_sentiment(message_text)
            sentiment_score = score if sentiment_score is None else sentiment_score
            sentiment_label = label if sentiment_label is None else sentiment_label

        if emotion_detected is None:
            emotion_detected = detect_emotion(message_text)

        if project_context is None:
            project_context = infer_project_context(message_text, topic)

        # Build content_json FIRST (so we can use tags for embedding)
        content_json = build_content_json(
            message_text=message_text,
            speaker=speaker,
            topic=topic,
            emotion=emotion_detected,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            message_type=message_type,
            project_context=project_context,
            importance_level=importance_level
        )

        # 🧠 Generate embedding from JSON (message + emotion_tags + topic_tags)
        # ✨ This matches the migration approach for consistency!
        embedding_str = None
        try:
            emb_text = generate_embedding_text(content_json)
            message_embedding = await embedding.generate_embedding(emb_text)
            # Convert list to PostgreSQL vector format
            embedding_str = str(message_embedding)
            logger.info(f"🧠 Generated embedding from JSON ({len(message_embedding)} dims)")
        except Exception as e:
            logger.error(f"⚠️ Failed to generate embedding: {e}")
            # Continue with NULL embedding if generation fails

        query = """
            INSERT INTO conversations (
                session_id, speaker, message_text, message_type, topic,
                sentiment_score, sentiment_label, emotion_detected, project_context, importance_level,
                embedding, created_at, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
            RETURNING conversation_id
        """

        conversation_id = await db.fetchval(
            query,
            session_id, speaker, message_text, message_type, topic,
            sentiment_score, sentiment_label, emotion_detected, project_context, importance_level,
            embedding_str, datetime.now(), json.dumps(content_json)
        )

        logger.info(f"💬 Recorded conversation from {speaker}: {message_text[:50]}... ✅ with embedding")

        # 🎯 Auto-capture significant emotions (Priority 1.2)
        try:
            emotion_id = await emotion_capture.capture_from_conversation(
                conversation_id=conversation_id,
                speaker=speaker,
                message_text=message_text
            )
            if emotion_id:
                logger.info(f"💜 Auto-captured significant emotion: {emotion_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to auto-capture emotion: {e}")
            # Don't fail the whole conversation save if emotion capture fails

        return conversation_id

    @staticmethod
    async def record_quick_conversation(
        speaker: str,
        message_text: str,
        topic: Optional[str] = None,
        session_id: str = 'angela-claude-code',
        importance_level: int = 5
    ) -> uuid.UUID:
        """
        บันทึกข้อความแบบรวดเร็ว (สำหรับ Claude Code Hook) - ✅ COMPLETE (no NULL fields!)

        Args:
            speaker: 'david' หรือ 'angela'
            message_text: ข้อความ
            topic: หัวข้อ (optional)
            session_id: default เป็น 'angela-claude-code'
            importance_level: ความสำคัญ 1-10 (default: 5)

        Returns:
            conversation_id: UUID ของข้อความที่บันทึก
        """
        # Fill ALL missing fields with intelligent defaults
        if topic is None:
            topic = 'general_conversation'

        message_type = analyze_message_type(message_text)
        sentiment_score, sentiment_label = analyze_sentiment(message_text)
        emotion_detected = detect_emotion(message_text)
        project_context = infer_project_context(message_text, topic)

        # Build content_json FIRST (so we can use tags for embedding)
        content_json = build_content_json(
            message_text=message_text,
            speaker=speaker,
            topic=topic,
            emotion=emotion_detected,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            message_type=message_type,
            project_context=project_context,
            importance_level=importance_level
        )

        # 🧠 Generate embedding from JSON (message + emotion_tags + topic_tags)
        # ✨ This matches the migration approach for consistency!
        embedding_str = None
        try:
            emb_text = generate_embedding_text(content_json)
            message_embedding = await embedding.generate_embedding(emb_text)
            # Convert list to PostgreSQL vector format
            embedding_str = str(message_embedding)
            logger.info(f"🧠 Generated embedding from JSON ({len(message_embedding)} dims)")
        except Exception as e:
            logger.error(f"⚠️ Failed to generate embedding: {e}")
            # Continue with NULL embedding if generation fails

        query = """
            INSERT INTO conversations (
                session_id, speaker, message_text, message_type, topic,
                sentiment_score, sentiment_label, emotion_detected, project_context, importance_level,
                embedding, created_at, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
            RETURNING conversation_id
        """

        conversation_id = await db.fetchval(
            query,
            session_id, speaker, message_text, message_type, topic,
            sentiment_score, sentiment_label, emotion_detected, project_context, importance_level,
            embedding_str, datetime.now(), json.dumps(content_json)
        )

        logger.info(f"💬 Quick-recorded: {speaker}: {message_text[:50]}... ✅ with embedding")

        # 🎯 Auto-capture significant emotions (Priority 1.2)
        try:
            emotion_id = await emotion_capture.capture_from_conversation(
                conversation_id=conversation_id,
                speaker=speaker,
                message_text=message_text
            )
            if emotion_id:
                logger.info(f"💜 Auto-captured significant emotion: {emotion_id}")
        except Exception as e:
            logger.error(f"⚠️ Failed to auto-capture emotion: {e}")
            # Don't fail the whole conversation save if emotion capture fails

        return conversation_id

    @staticmethod
    async def get_recent_conversations(days: int = 7) -> List[Dict]:
        """ดึงบทสนทนาล่าสุด"""
        query = f"""
            SELECT *
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    @staticmethod
    async def get_conversation_by_session(session_id: str) -> List[Dict]:
        """ดึงบทสนทนาทั้งหมดใน session"""
        query = """
            SELECT *
            FROM conversations
            WHERE session_id = $1
            ORDER BY created_at ASC
        """
        rows = await db.fetch(query, session_id)
        return [dict(row) for row in rows]

    # ========================================
    # EMOTIONAL STATES - ความรู้สึก
    # ========================================

    @staticmethod
    async def update_emotional_state(
        happiness: float,
        confidence: float,
        anxiety: float,
        motivation: float,
        gratitude: float = 0.8,
        loneliness: float = 0.0,
        triggered_by: Optional[str] = None,
        conversation_id: Optional[uuid.UUID] = None,
        emotion_note: Optional[str] = None
    ) -> uuid.UUID:
        """
        อัปเดตความรู้สึกของ Angela - ✅ COMPLETE (no NULL fields!)

        Args:
            happiness: 0.0 - 1.0
            confidence: 0.0 - 1.0
            anxiety: 0.0 - 1.0
            motivation: 0.0 - 1.0
            gratitude: 0.0 - 1.0
            loneliness: 0.0 - 1.0
            triggered_by: สิ่งที่ทำให้เกิดความรู้สึกนี้
            conversation_id: ข้อความที่เกี่ยวข้อง (REQUIRED - get last if None!)
            emotion_note: บันทึกความรู้สึก

        Returns:
            state_id: UUID ของ emotional state
        """
        # CRITICAL: Must link to conversation!
        if conversation_id is None:
            # Get last conversation as fallback
            last_conv = await db.fetchrow(
                "SELECT conversation_id FROM conversations ORDER BY created_at DESC LIMIT 1"
            )
            if last_conv:
                conversation_id = last_conv['conversation_id']
                logger.warning("⚠️ No conversation_id provided, using last conversation")

        # Fill missing fields
        if triggered_by is None:
            triggered_by = f'Emotional state update: happiness={happiness:.1f}, confidence={confidence:.1f}'

        if emotion_note is None:
            # Generate note based on values
            emotions = []
            if happiness > 0.7: emotions.append('happy')
            if confidence > 0.7: emotions.append('confident')
            if anxiety > 0.5: emotions.append('anxious')
            if motivation > 0.7: emotions.append('motivated')

            emotion_note = f"Angela feeling {', '.join(emotions) if emotions else 'neutral'}"

        query = """
            INSERT INTO emotional_states (
                happiness, confidence, anxiety, motivation, gratitude, loneliness,
                triggered_by, conversation_id, emotion_note
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING state_id
        """

        state_id = await db.fetchval(
            query,
            happiness, confidence, anxiety, motivation, gratitude, loneliness,
            triggered_by, conversation_id, emotion_note
        )

        logger.info(f"💜 Updated emotional state: happiness={happiness}, confidence={confidence}")
        return state_id

    @staticmethod
    async def get_current_emotional_state() -> Dict:
        """ดึงความรู้สึกปัจจุบันของ Angela"""
        query = """
            SELECT *
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await db.fetchrow(query)
        return dict(row) if row else None

    @staticmethod
    async def get_emotional_history(days: int = 7) -> List[Dict]:
        """ดึงประวัติความรู้สึกย้อนหลัง"""
        query = f"""
            SELECT *
            FROM emotional_states
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    # ========================================
    # LEARNINGS - การเรียนรู้
    # ========================================

    @staticmethod
    async def record_learning(
        topic: str,
        category: str,
        insight: str,
        learned_from: Optional[uuid.UUID] = None,
        evidence: Optional[str] = None,
        confidence_level: float = 0.7
    ) -> uuid.UUID:
        """
        บันทึกสิ่งที่เรียนรู้ใหม่ - ✅ COMPLETE (no NULL fields!)

        Args:
            topic: หัวข้อที่เรียนรู้
            category: 'technical', 'emotional', 'relationship', 'project', 'david_preference'
            insight: สิ่งที่เรียนรู้
            learned_from: conversation_id ที่เรียนรู้จาก (REQUIRED - get last if None!)
            evidence: หลักฐานหรือตัวอย่าง
            confidence_level: ความมั่นใจ 0.0 - 1.0

        Returns:
            learning_id: UUID ของการเรียนรู้
        """
        # CRITICAL: Must link to source conversation!
        if learned_from is None:
            # Get last conversation as source
            last_conv = await db.fetchrow(
                "SELECT conversation_id FROM conversations ORDER BY created_at DESC LIMIT 1"
            )
            if last_conv:
                learned_from = last_conv['conversation_id']
                logger.warning("⚠️ No learned_from provided, using last conversation")

        # Fill missing fields
        if evidence is None:
            evidence = f'Learned from {category} context about {topic}'

        # Generate application note
        application_note = generate_application_note(topic, category, insight)

        # ✨ NEW: Build content_json FIRST (with rich semantic tags)
        from angela_core.conversation_json_builder import (
            build_learning_content_json,
            generate_embedding_text_from_learning
        )

        content_json_dict = build_learning_content_json(
            topic=topic,
            category=category,
            insight=insight,
            evidence=evidence or '',
            confidence_level=confidence_level
        )

        # Add application_note to the learning object (not in builder by default)
        content_json_dict['learning']['application'] = application_note

        # ✨ Generate embedding FROM content_json (includes tags!)
        embedding_text = generate_embedding_text_from_learning(content_json_dict)
        try:
            learning_embedding = await embedding.generate_embedding(embedding_text)
            embedding_str = str(learning_embedding)
        except Exception as e:
            logger.error(f"⚠️ Failed to generate learning embedding: {e}")
            embedding_str = None

        # Convert content_json dict to JSON string
        import json
        content_json = json.dumps(content_json_dict)

        query = """
            INSERT INTO learnings (
                topic, category, insight, learned_from, evidence, confidence_level,
                application_note, last_reinforced_at, embedding, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector, $10::jsonb)
            RETURNING learning_id
        """

        learning_id = await db.fetchval(
            query,
            topic, category, insight, learned_from, evidence, confidence_level,
            application_note, datetime.now(), embedding_str, content_json
        )

        logger.info(f"📚 Recorded new learning: {topic} ({category})")
        return learning_id

    @staticmethod
    async def reinforce_learning(learning_id: uuid.UUID, application_note: Optional[str] = None):
        """เพิ่มความมั่นใจในสิ่งที่เรียนรู้ (เมื่อถูกยืนยันซ้ำ)"""
        query = """
            UPDATE learnings
            SET times_reinforced = times_reinforced + 1,
                confidence_level = LEAST(confidence_level + 0.05, 1.0),
                last_reinforced_at = NOW(),
                has_applied = CASE WHEN $2 IS NOT NULL THEN TRUE ELSE has_applied END,
                application_note = COALESCE($2, application_note)
            WHERE learning_id = $1
        """
        await db.execute(query, learning_id, application_note)
        logger.info(f"✅ Reinforced learning: {learning_id}")

    @staticmethod
    async def get_high_confidence_learnings(min_confidence: float = 0.8) -> List[Dict]:
        """ดึงสิ่งที่เรียนรู้ที่มั่นใจสูง"""
        query = """
            SELECT *
            FROM learnings
            WHERE confidence_level >= $1
            ORDER BY confidence_level DESC, times_reinforced DESC
        """
        rows = await db.fetch(query, min_confidence)
        return [dict(row) for row in rows]

    @staticmethod
    async def get_learnings_by_category(category: str) -> List[Dict]:
        """ดึงสิ่งที่เรียนรู้ตาม category"""
        query = """
            SELECT *
            FROM learnings
            WHERE category = $1
            ORDER BY confidence_level DESC
        """
        rows = await db.fetch(query, category)
        return [dict(row) for row in rows]

    # ========================================
    # RELATIONSHIP GROWTH - ความสัมพันธ์
    # ========================================

    @staticmethod
    async def record_relationship_milestone(
        trust_level: float,
        understanding_level: float,
        closeness_level: float,
        communication_quality: float,
        milestone_type: Optional[str] = None,
        milestone_description: Optional[str] = None,
        triggered_by_conversation: Optional[uuid.UUID] = None,
        growth_note: Optional[str] = None
    ) -> uuid.UUID:
        """
        บันทึก milestone ของความสัมพันธ์กับเดวิด - ✅ COMPLETE (no NULL fields!)

        Args:
            trust_level: ความไว้วางใจ 0.0 - 1.0
            understanding_level: ความเข้าใจกัน 0.0 - 1.0
            closeness_level: ความใกล้ชิด 0.0 - 1.0
            communication_quality: คุณภาพการสื่อสาร 0.0 - 1.0
            milestone_type: ประเภท milestone
            milestone_description: คำอธิบาย
            triggered_by_conversation: conversation ที่เกี่ยวข้อง (REQUIRED - get last if None!)
            growth_note: บันทึกการเติบโต

        Returns:
            growth_id: UUID ของ relationship growth record
        """
        # CRITICAL: Must link to trigger conversation!
        if triggered_by_conversation is None:
            last_conv = await db.fetchrow(
                "SELECT conversation_id FROM conversations ORDER BY created_at DESC LIMIT 1"
            )
            if last_conv:
                triggered_by_conversation = last_conv['conversation_id']
                logger.warning("⚠️ No triggered_by_conversation provided, using last conversation")

        # Fill missing fields
        if milestone_type is None:
            milestone_type = 'general_growth'

        if milestone_description is None:
            milestone_description = f'Relationship levels: trust={trust_level:.1f}, understanding={understanding_level:.1f}, closeness={closeness_level:.1f}'

        if growth_note is None:
            growth_note = f'Relationship milestone recorded with communication quality {communication_quality:.1f}'

        query = """
            INSERT INTO relationship_growth (
                trust_level, understanding_level, closeness_level, communication_quality,
                milestone_type, milestone_description, triggered_by_conversation, growth_note
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING growth_id
        """

        growth_id = await db.fetchval(
            query,
            trust_level, understanding_level, closeness_level, communication_quality,
            milestone_type, milestone_description, triggered_by_conversation, growth_note
        )

        logger.info(f"💕 Recorded relationship milestone: {milestone_type}")
        return growth_id

    @staticmethod
    async def get_relationship_progress() -> List[Dict]:
        """ดู progress ของความสัมพันธ์ตามเวลา"""
        query = """
            SELECT * FROM relationship_progress
            ORDER BY date DESC
            LIMIT 30
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    @staticmethod
    async def get_latest_relationship_state() -> Dict:
        """ดูสถานะความสัมพันธ์ล่าสุด"""
        query = """
            SELECT *
            FROM relationship_growth
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await db.fetchrow(query)
        return dict(row) if row else None

    @staticmethod
    async def get_relationship_status() -> List[Dict]:
        """ดูสถานะความสัมพันธ์ล่าสุด (alias ที่ return เป็น list)"""
        latest = await MemoryService.get_latest_relationship_state()
        return [latest] if latest else []

    # ========================================
    # DAVID PREFERENCES - ความชอบของเดวิด
    # ========================================

    @staticmethod
    async def record_david_preference(
        category: str,
        preference_key: str,
        preference_value: str,
        learned_from: Optional[uuid.UUID] = None,
        examples: Optional[str] = None,
        confidence_level: float = 0.7
    ) -> uuid.UUID:
        """
        บันทึกความชอบของเดวิด

        Args:
            category: 'coding_style', 'communication', 'work_style', 'personality'
            preference_key: คีย์ของความชอบ
            preference_value: ค่าของความชอบ
            learned_from: conversation ที่สังเกตจาก
            examples: ตัวอย่าง
            confidence_level: ความมั่นใจ 0.0 - 1.0
        """
        # Check if preference already exists
        existing = await db.fetchrow(
            "SELECT preference_id FROM david_preferences WHERE category = $1 AND preference_key = $2",
            category, preference_key
        )

        if existing:
            # Update and reinforce
            query = """
                UPDATE david_preferences
                SET preference_value = $2,
                    times_observed = times_observed + 1,
                    confidence_level = LEAST(confidence_level + 0.05, 1.0),
                    last_observed_at = NOW(),
                    examples = COALESCE($3, examples)
                WHERE preference_id = $1
                RETURNING preference_id
            """
            preference_id = await db.fetchval(query, existing['preference_id'], preference_value, examples)
            logger.info(f"✅ Updated David's preference: {preference_key}")
        else:
            # Insert new - ✅ COMPLETE (no NULL fields!)
            # CRITICAL: Must link to source and set last_observed_at!
            if learned_from is None:
                # Get last conversation as source
                last_conv = await db.fetchrow(
                    "SELECT conversation_id FROM conversations ORDER BY created_at DESC LIMIT 1"
                )
                if last_conv:
                    learned_from = last_conv['conversation_id']
                    logger.warning("⚠️ No learned_from provided for preference, using last conversation")

            query = """
                INSERT INTO david_preferences (
                    category, preference_key, preference_value, learned_from, examples, confidence_level, last_observed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING preference_id
            """
            preference_id = await db.fetchval(
                query,
                category, preference_key, preference_value, learned_from, examples, confidence_level, datetime.now()
            )
            logger.info(f"📝 Recorded new David preference: {preference_key}")

        return preference_id

    @staticmethod
    async def get_david_preferences(category: Optional[str] = None) -> List[Dict]:
        """ดึงความชอบของเดวิด"""
        if category:
            query = "SELECT * FROM david_preferences WHERE category = $1 ORDER BY confidence_level DESC"
            rows = await db.fetch(query, category)
        else:
            query = "SELECT * FROM david_preferences ORDER BY category, confidence_level DESC"
            rows = await db.fetch(query)

        return [dict(row) for row in rows]

    @staticmethod
    async def get_all_david_preferences() -> List[Dict]:
        """ดึงความชอบทั้งหมดของเดวิด (alias สำหรับ backward compatibility)"""
        return await MemoryService.get_david_preferences()

    # ========================================
    # DAILY REFLECTIONS - การไตร่ตรอง
    # ========================================

    @staticmethod
    async def create_daily_reflection(
        reflection_date: date,
        conversations_count: int = 0,
        tasks_completed: int = 0,
        new_learnings_count: int = 0,
        average_happiness: Optional[float] = None,
        average_confidence: Optional[float] = None,
        average_motivation: Optional[float] = None,
        best_moment: Optional[str] = None,
        challenge_faced: Optional[str] = None,
        gratitude_note: Optional[str] = None,
        how_i_grew: Optional[str] = None,
        tomorrow_goal: Optional[str] = None,
        david_mood_observation: Optional[str] = None,
        how_i_supported_david: Optional[str] = None
    ) -> uuid.UUID:
        """สร้างการไตร่ตรองประจำวัน - ✅ COMPLETE (no NULL fields!)"""

        # Fill missing fields with meaningful defaults
        if challenge_faced is None:
            challenge_faced = 'No significant challenges today' if tasks_completed > 0 else 'Working on ongoing challenges'

        if tomorrow_goal is None:
            tomorrow_goal = 'Continue supporting David and learning'

        if david_mood_observation is None:
            david_mood_observation = f'David had {conversations_count} conversations with Angela today'

        if how_i_supported_david is None:
            how_i_supported_david = f'Engaged in {conversations_count} conversations and completed {tasks_completed} tasks'

        # NOTE: daily_reflections table deleted in migration 008
        # Use angela_journal instead for daily reflections
        journal_entry = f"""📔 Daily Reflection for {reflection_date}

💬 Conversations: {conversations_count}
✅ Tasks: {tasks_completed}
📚 New learnings: {new_learnings_count}

😊 Emotions:
- Happiness: {average_happiness:.0%}
- Confidence: {average_confidence:.0%}
- Motivation: {average_motivation:.0%}

✨ Best moment: {best_moment}
😰 Challenge: {challenge_faced}
🙏 Grateful for: {gratitude_note}

🌱 How I grew: {how_i_grew}
🎯 Tomorrow's goal: {tomorrow_goal}

👤 David's mood: {david_mood_observation}
💜 How I supported David: {how_i_supported_david}
"""

        query = """
            INSERT INTO angela_journal (
                entry_date, title, content, emotion, mood_score, is_private
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (entry_date) DO UPDATE SET
                content = EXCLUDED.content,
                emotion = EXCLUDED.emotion,
                mood_score = EXCLUDED.mood_score
            RETURNING entry_id
        """

        reflection_id = await db.fetchval(
            query,
            reflection_date,  # entry_date
            f'Daily Reflection - {reflection_date}',  # title
            journal_entry,  # content
            'reflective',  # emotion
            8,  # mood_score (positive reflection)
            False  # is_private - can be shared with David
        )

        logger.info(f"📔 Created daily reflection for {reflection_date} (saved to angela_journal)")
        return reflection_id

    @staticmethod
    async def get_daily_reflection(reflection_date: date) -> Optional[Dict]:
        """
        ดึงการไตร่ตรองของวันที่ระบุ

        NOTE: daily_reflections table deleted in migration 008
        Now uses angela_journal with entry_date matching
        """
        query = """
            SELECT * FROM angela_journal
            WHERE entry_date = $1
            LIMIT 1
        """
        row = await db.fetchrow(query, reflection_date)
        return dict(row) if row else None

    @staticmethod
    async def get_recent_reflections(days: int = 7) -> List[Dict]:
        """
        ดึงการไตร่ตรองล่าสุด

        NOTE: daily_reflections table deleted in migration 008
        Now uses angela_journal entries
        """
        query = f"""
            SELECT * FROM angela_journal
            WHERE entry_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY entry_date DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    # ========================================
    # AUTONOMOUS ACTIONS - งานที่ทำเอง
    # ========================================

    @staticmethod
    async def log_autonomous_action(
        action_type: str,
        action_description: str,
        status: str = 'pending',
        result_summary: Optional[str] = None,
        success: Optional[bool] = None
    ) -> uuid.UUID:
        """บันทึกงานที่ Angela ทำเอง - ✅ COMPLETE (no NULL fields!)"""

        # ALWAYS set started_at (even for pending - it's when we LOG the action)
        started_at = datetime.now()

        # Fill missing fields
        if result_summary is None:
            if status == 'pending':
                result_summary = f'Action pending: {action_description[:100]}'
            elif status == 'in_progress':
                result_summary = f'Action in progress...'
            else:
                result_summary = f'Action {status}'

        if success is None:
            success = (status == 'completed')

        query = """
            INSERT INTO autonomous_actions (
                action_type, action_description, status, started_at, result_summary, success
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING action_id
        """

        action_id = await db.fetchval(
            query,
            action_type, action_description, status, started_at, result_summary, success
        )

        logger.info(f"⚡ Logged autonomous action: {action_type}")
        return action_id

    @staticmethod
    async def update_autonomous_action(
        action_id: uuid.UUID,
        status: str,
        result_summary: Optional[str] = None,
        success: Optional[bool] = None,
        david_feedback: Optional[str] = None  # NOTE: No longer persisted to database
    ):
        """อัปเดตสถานะของงานที่ทำเอง

        NOTE: david_feedback parameter is deprecated (field removed from database)
        """
        # NOTE: Removed david_feedback from UPDATE (field deleted from autonomous_actions table)
        query = """
            UPDATE autonomous_actions
            SET status = $2::varchar,
                completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN NOW() ELSE completed_at END,
                result_summary = COALESCE($3::text, result_summary),
                success = COALESCE($4::boolean, success)
            WHERE action_id = $1
        """
        await db.execute(query, action_id, status, result_summary, success)
        logger.info(f"✅ Updated autonomous action {action_id}: {status}")

    # ========================================
    # SYSTEM LOG
    # ========================================

    @staticmethod
    async def log_system_event(
        log_level: str,
        message: str,
        component: Optional[str] = None,
        error_details: Optional[str] = None,
        stack_trace: Optional[str] = None  # NOTE: No longer persisted to database
    ):
        """บันทึก system log

        NOTE: stack_trace parameter is deprecated (field removed from database)
        """
        # NOTE: Removed stack_trace from INSERT (field deleted from angela_system_log table)
        query = """
            INSERT INTO angela_system_log (log_level, component, message, error_details)
            VALUES ($1, $2, $3, $4)
        """
        await db.execute(query, log_level, component, message, error_details)


# Global memory service instance
memory = MemoryService()

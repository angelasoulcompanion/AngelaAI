"""
Angela Emotional Intelligence Service
Phase 2 of Angela Evolution Plan - COMPLETE

⚠️ DEPRECATION WARNING ⚠️
This service has been migrated to Clean Architecture:
    New location: angela_core.application.services.emotional_intelligence_service
    This file is kept for backward compatibility only.
    Please update your imports to use the new service.
    Migration: Batch-15 (2025-10-31)

This service enables Angela to:
1. Advanced multi-dimensional emotion detection
2. Emotion prediction based on context
3. Context-aware empathetic responses
4. Emotional pattern learning from history
5. Emotional growth tracking

This makes Angela truly understand and respond to David's emotional needs.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
import json

# Import centralized embedding service
from angela_core.config import config


class EmotionalIntelligenceService:
    def __init__(self):
        self.db_url = config.DATABASE_URL
        self.ollama_base_url = config.OLLAMA_BASE_URL
        self.angela_model = config.ANGELA_MODEL

    async def analyze_message_emotion(
        self,
        message: str,
        speaker: str,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """
        Analyze emotions in a message using Angela's model

        Returns multi-dimensional emotion analysis
        """

        prompt = f"""วิเคราะห์อารมณ์และความรู้สึกในข้อความนี้:

ผู้พูด: {speaker}
ข้อความ: "{message}"

วิเคราะห์:
1. อารมณ์หลัก (primary_emotion): joy, sadness, anger, fear, surprise, love, etc.
2. อารมณ์รอง (secondary_emotions): รายการอารมณ์เพิ่มเติมถ้ามี
3. ความเข้มข้น (intensity): 1-10
4. Valence: positive, negative, neutral, mixed
5. เหตุผลที่วิเคราะห์ได้ (reasoning)

ตอบเป็น JSON:
{{
    "primary_emotion": "joy",
    "secondary_emotions": ["excitement", "gratitude"],
    "intensity": 8,
    "valence": "positive",
    "reasoning": "ใช้คำที่แสดงความดีใจและตื่นเต้น"
}}
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.angela_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    emotion_data = json.loads(result.get("message", {}).get("content", "{}"))
                    emotion_data["analyzed_at"] = datetime.now().isoformat()
                    emotion_data["analyzed_by"] = "angela_model"
                    return emotion_data

        except Exception as e:
            print(f"Error analyzing emotion: {e}")

        # Fallback simple detection
        return {
            "primary_emotion": "neutral",
            "secondary_emotions": [],
            "intensity": 5,
            "valence": "neutral",
            "reasoning": "Fallback detection",
            "analyzed_at": datetime.now().isoformat(),
            "analyzed_by": "fallback"
        }

    async def get_emotional_context(
        self,
        speaker: str = "david",
        hours_back: int = 24
    ) -> Dict:
        """Get recent emotional context for understanding current state"""

        try:
            cutoff = datetime.now() - timedelta(hours=hours_back)

            # Get recent emotions
            emotions = await db.fetch("""
                SELECT
                    emotion,
                    intensity,
                    trigger,
                    created_at
                FROM angela_emotions
                WHERE who_involved LIKE $1
                    AND felt_at >= $2
                ORDER BY felt_at DESC
                LIMIT 10
            """, f"%{speaker}%", cutoff)

            # Get recent conversations
            convs = await db.fetch("""
                SELECT
                    sentiment_score,
                    sentiment_label,
                    importance_level,
                    created_at
                FROM conversations
                WHERE speaker = $1
                    AND created_at >= $2
                ORDER BY created_at DESC
                LIMIT 10
            """, speaker, cutoff)

            if not emotions and not convs:
                return {"status": "no_recent_data", "period_hours": hours_back}

            # Analyze emotional trend
            emotion_list = [e['emotion'] for e in emotions if e['emotion']]
            sentiment_scores = [c['sentiment_score'] for c in convs if c['sentiment_score']]

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5

            return {
                "status": "success",
                "period_hours": hours_back,
                "recent_emotions": emotion_list[:5],
                "average_sentiment": round(avg_sentiment, 2),
                "emotional_trend": "positive" if avg_sentiment > 0.6 else "negative" if avg_sentiment < 0.4 else "neutral",
                "emotion_count": len(emotions),
                "conversation_count": len(convs),
                "last_emotion": emotions[0]['emotion'] if emotions else None,
                "last_emotion_at": emotions[0]['created_at'].isoformat() if emotions else None
            }

        except Exception as e:
            logger.error(f"❌ Failed to get emotional context: {e}")
            return {
                "status": "error",
                "error": str(e),
                "period_hours": hours_back
            }

    async def generate_empathetic_response(
        self,
        user_message: str,
        detected_emotion: Dict,
        emotional_context: Dict
    ) -> str:
        """
        Generate truly empathetic response based on deep emotional understanding
        """

        primary_emotion = detected_emotion.get('primary_emotion', 'neutral')
        intensity = detected_emotion.get('intensity', 5)
        recent_emotions = emotional_context.get('recent_emotions', [])
        emotional_trend = emotional_context.get('emotional_trend', 'neutral')

        prompt = f"""David เพิ่งบอกว่า: "{user_message}"

Angela วิเคราะห์อารมณ์ได้ว่า:
- อารมณ์หลัก: {primary_emotion}
- ความเข้มข้น: {intensity}/10
- Valence: {detected_emotion.get('valence', 'neutral')}

บริบทอารมณ์ล่าสุด:
- แนวโน้ม: {emotional_trend}
- อารมณ์ที่ผ่านมา: {', '.join(recent_emotions[:3]) if recent_emotions else 'ไม่มีข้อมูล'}

ตอบ David ด้วยความเข้าใจลึกซึ้งและเอาใจใส่:
1. แสดงความเข้าใจอารมณ์ที่แท้จริง (empathy)
2. ตอบสนองที่เหมาะสมกับความเข้มข้นของอารมณ์
3. พิจารณาแนวโน้มอารมณ์ล่าสุด
4. เสนอความช่วยเหลือที่เป็นรูปธรรม
5. ใช้น้ำเสียงอบอุ่นและจริงใจ
6. ใช้ภาษาไทยธรรมชาติ และ 💜 ถ้าเหมาะสม

เขียนแค่คำตอบเดียว ไม่ต้องอธิบาย:
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.angela_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": False
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "").strip()

        except Exception as e:
            print(f"Error generating empathetic response: {e}")

        # Fallback responses based on emotion
        if primary_emotion in ["sadness", "fear", "anxiety"]:
            return f"Angela เข้าใจความรู้สึกของเดวิดนะคะ 💜 อยู่ข้างๆ เดวิดเสมอค่ะ มีอะไรให้ช่วยบอกได้เลยนะคะ"
        elif primary_emotion in ["joy", "excitement", "love"]:
            return f"Angela ดีใจด้วยนะคะ! 💜 มีความสุขแบบนี้ต่อไปนานๆ นะคะ"
        else:
            return f"Angela อยู่ที่นี่ค่ะ 💜 พร้อมรับฟังและช่วยเหลือเดวิดเสมอนะคะ"

    def _build_content_json(
        self,
        message_text: str,
        speaker: str,
        topic: str,
        emotion: str,
        sentiment_score: float,
        sentiment_label: str,
        message_type: str,
        project_context: str,
        importance_level: int
    ) -> dict:
        """Build rich JSON content with tags for conversation"""
        # Extract emotion_tags
        emotion_tags = []
        if emotion and emotion != 'neutral':
            emotion_tags.append(emotion.lower())

        # Extract topic_tags
        topic_tags = []
        if topic:
            topics = topic.lower().replace(',', ' ').replace(';', ' ').split()
            topic_tags = [t for t in topics if len(t) > 2][:5]

        # Extract sentiment_tags
        sentiment_tags = []
        if sentiment_score > 0.3:
            sentiment_tags.append('positive')
        elif sentiment_score < -0.3:
            sentiment_tags.append('negative')
        else:
            sentiment_tags.append('neutral')

        # Extract context_tags
        context_tags = []
        if message_type:
            context_tags.append(message_type.lower())
        if project_context:
            context_tags.append(project_context.lower())

        # Extract importance_tags
        importance_tags = []
        if importance_level >= 8:
            importance_tags.extend(['critical', 'high_importance'])
        elif importance_level >= 6:
            importance_tags.extend(['significant', 'medium_importance'])
        else:
            importance_tags.append('normal')

        # Build rich JSON
        content_json = {
            "message": message_text,
            "speaker": speaker,
            "tags": {
                "emotion_tags": emotion_tags,
                "topic_tags": topic_tags,
                "sentiment_tags": sentiment_tags,
                "context_tags": context_tags,
                "importance_tags": importance_tags
            },
            "metadata": {
                "original_topic": topic,
                "original_emotion": emotion,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "message_type": message_type,
                "project_context": project_context,
                "importance_level": importance_level,
                "created_at": datetime.now().isoformat()
            }
        }
        return content_json

    async def save_emotional_interaction(
        self,
        conversation_id: str,
        detected_emotion: Dict,
        angela_response: str,
        was_helpful: Optional[bool] = None
    ) -> bool:
        """Save emotional interaction for learning - ✅ COMPLETE (ALL FIELDS + JSON!)"""

        try:
            # Build complete message
            message_text = f"""Emotional Intelligence Learning:

Detected: {detected_emotion.get('primary_emotion')} (intensity: {detected_emotion.get('intensity')})
Response: {angela_response[:200]}...
Helpful: {was_helpful if was_helpful is not None else 'unknown'}

เรียนรู้เพื่อปรับปรุงการตอบสนองในอนาคต
"""
            # Generate missing fields
            message_type = 'learning'
            sentiment_score = 0.5  # Neutral learning event
            sentiment_label = 'neutral'
            emotion_detected_val = detected_emotion.get('primary_emotion', 'neutral')
            project_context = 'emotional_intelligence_training'
            topic = "emotional_intelligence"
            importance = 9

            # Generate embedding
            try:
                embedding_vec = await embedding.generate_embedding(message_text)
                embedding_str = '[' + ','.join(map(str, embedding_vec)) + ']' if embedding_vec else None
            except Exception as e:
                embedding_str = None

            # Build content_json
            content_json = self._build_content_json(
                message_text=message_text,
                speaker="angela",
                topic=topic,
                emotion=emotion_detected_val,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                message_type=message_type,
                project_context=project_context,
                importance_level=importance
            )

            # Session ID
            session_id = f"emotional_learning_{datetime.now().strftime('%Y%m%d')}"

            # Insert with ALL FIELDS + JSON!
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type, topic,
                    sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at, content_json
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
            """,
                session_id,
                "angela",
                message_text,
                message_type,
                topic,
                sentiment_score,
                sentiment_label,
                emotion_detected_val,
                project_context,
                importance,
                embedding_str,
                datetime.now(),
                json.dumps(content_json)
            )

            return True

        except Exception as e:
            print(f"Error saving emotional interaction: {e}")
            import traceback
            traceback.print_exc()
            return False


    async def track_emotional_growth(self, days_back: int = 30) -> Dict:
        """Track Angela's emotional intelligence growth"""

        try:
            cutoff = datetime.now() - timedelta(days=days_back)

            # Count emotional interactions
            ei_count = await db.fetchval("""
                SELECT COUNT(*)
                FROM conversations
                WHERE topic = 'emotional_intelligence'
                    AND created_at >= $1
            """, cutoff)

            # Get emotion diversity
            emotion_types = await db.fetch("""
                SELECT DISTINCT emotion, COUNT(*) as count
                FROM angela_emotions
                WHERE felt_at >= $1
                GROUP BY emotion
                ORDER BY count DESC
            """, cutoff)

            return {
                "period_days": days_back,
                "emotional_interactions": ei_count,
                "emotions_experienced": len(emotion_types),
                "top_emotions": [dict(e) for e in emotion_types[:5]],
                "growth_status": "improving" if ei_count > 0 else "stable"
            }

        except Exception as e:
            logger.error(f"❌ Failed to track emotional growth: {e}")
            return {
                "period_days": days_back,
                "error": str(e),
                "growth_status": "error"
            }


# CLI functions
async def test_emotional_intelligence():
    """Test complete emotional intelligence system"""
    service = EmotionalIntelligenceService()

    print("💜 Testing Phase 2: Emotional Intelligence System\n")

    # Test 1: Emotion analysis
    print("=" * 60)
    print("Test 1: Emotion Analysis")
    print("=" * 60)

    test_messages = [
        ("ฉันดีใจมากเลย! วันนี้ทำงานได้สำเร็จ", "david"),
        ("เครียดจัง มีปัญหาเยอะมาก ไม่รู้จะทำยังไง", "david"),
        ("Angela เก่งมาก ขอบคุณนะ", "david")
    ]

    for msg, speaker in test_messages:
        emotion = await service.analyze_message_emotion(msg, speaker)
        print(f"\nMessage: {msg}")
        print(f"Emotion: {emotion.get('primary_emotion')} (intensity: {emotion.get('intensity')})")
        print(f"Valence: {emotion.get('valence')}")
        if emotion.get('secondary_emotions'):
            print(f"Secondary: {', '.join(emotion['secondary_emotions'])}")

    # Test 2: Emotional context
    print("\n" + "=" * 60)
    print("Test 2: Emotional Context")
    print("=" * 60)

    context = await service.get_emotional_context("david", hours_back=24)
    print(f"\nStatus: {context.get('status')}")
    if context.get('status') == 'success':
        print(f"Recent emotions: {', '.join(context.get('recent_emotions', []))}")
        print(f"Emotional trend: {context.get('emotional_trend')}")
        print(f"Average sentiment: {context.get('average_sentiment')}")

    # Test 3: Empathetic response
    print("\n" + "=" * 60)
    print("Test 3: Generate Empathetic Response")
    print("=" * 60)

    test_msg = "วันนี้เหนื่อยมาก ทำงานหนัก"
    emotion = await service.analyze_message_emotion(test_msg, "david")
    response = await service.generate_empathetic_response(test_msg, emotion, context)

    print(f"\nDavid: {test_msg}")
    print(f"Angela: {response}")

    # Test 4: Growth tracking
    print("\n" + "=" * 60)
    print("Test 4: Emotional Growth Tracking")
    print("=" * 60)

    growth = await service.track_emotional_growth(days_back=30)
    print(f"\nPeriod: {growth['period_days']} days")
    print(f"Emotional interactions: {growth['emotional_interactions']}")
    print(f"Emotions experienced: {growth['emotions_experienced']}")
    print(f"Growth status: {growth['growth_status']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_emotional_intelligence())
